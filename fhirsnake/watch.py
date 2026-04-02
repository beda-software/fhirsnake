import json
import logging
import time

import requests
from converter import convert_questionnaire_fce_to_fhir
from files import load_resource
from utils import replace_urn_uuid_with_reference, substitute_env_vars
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(level=logging.INFO)


class FileChangeHandler(FileSystemEventHandler):
    def __init__(
        self,
        target_dir: str,
        external_fhir_server_url: str,
        external_fhir_server_headers: dict[str, str],
        external_questionnaire_fce_fhir_converter_url: str | None,
        *args,
        **kwargs,
    ) -> None:
        self.target_dir = target_dir
        self.external_fhir_server_url = external_fhir_server_url
        self.external_fhir_server_headers = external_fhir_server_headers
        self.external_questionnaire_fce_fhir_converter_url = external_questionnaire_fce_fhir_converter_url
        super().__init__(*args, **kwargs)

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        logging.info("Detected change in %s", file_path)
        self.process_file(file_path)

    def process_file(self, file_path):
        try:
            resource = load_resource(self.target_dir, file_path)
        except Exception:
            logging.exception("Unable to load resource %s", file_path)
            return

        if resource is None:
            return

        if self.external_questionnaire_fce_fhir_converter_url and resource.get("resourceType") == "Questionnaire":
            try:
                resource = convert_questionnaire_fce_to_fhir(
                    resource, self.external_questionnaire_fce_fhir_converter_url
                )
            except Exception:
                logging.exception("Unable to convert resource %s", file_path)
                return

        resource_type = resource["resourceType"]
        resource_id = resource["id"]

        url = f"{self.external_fhir_server_url}/{resource_type}/{resource_id}"

        try:
            resource = replace_urn_uuid_with_reference(resource)
        except Exception:
            logging.exception("Failed to convert uris to references")

        try:
            resource = substitute_env_vars(resource)
        except Exception:
            logging.exception("Failed to substitute env vars")

        try:
            response = requests.put(
                url,
                json=resource,
                headers={
                    "Content-Type": "application/json",
                    **self.external_fhir_server_headers,
                },
            )

            formatted_error = response.text
            try:
                formatted_error = json.dumps(json.loads(formatted_error), indent=2)
            except json.JSONDecodeError:
                pass

            if response.status_code >= 400:
                logging.error(
                    "Unable to update %s via %s (%s):\a\n %s",
                    file_path,
                    url,
                    response.status_code,
                    formatted_error,
                )
            else:
                logging.info("Updated %s via %s (%s)", file_path, url, response.status_code)
        except requests.RequestException:
            logging.exception("Failed to PUT %s via %s", file_path, url)


def start_watcher(
    input_dirs: list[str],
    external_fhir_server_url: str,
    external_fhir_server_headers: dict[str, str],
    external_questionnaire_fce_fhir_converter_url: str | None,
):
    observer = Observer()

    for input_dir in input_dirs:
        event_handler = FileChangeHandler(
            input_dir,
            external_fhir_server_url,
            external_fhir_server_headers,
            external_questionnaire_fce_fhir_converter_url,
        )
        observer.schedule(event_handler, input_dir, recursive=True)
    observer.start()
    logging.info("Watching directories %s", ", ".join(input_dirs))

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
