import json
import logging
import time

import requests
from converter import convert_questionnaire_fce_to_fhir
from files import load_resource
from initial_resources import RESOURCE_DIR
from utils import replace_urn_uuid_with_reference
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
        self.external_questionnaire_fce_fhir_converter_url = (
            external_questionnaire_fce_fhir_converter_url
        )
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
        except Exception as exc:
            logging.error("Unable to load resource %s:\a\n%s", file_path, exc)
            return

        if resource is None:
            return

        if (
            self.external_questionnaire_fce_fhir_converter_url
            and resource.get("resourceType") == "Questionnaire"
        ):
            try:
                resource = convert_questionnaire_fce_to_fhir(
                    resource, self.external_questionnaire_fce_fhir_converter_url
                )
            except Exception as exc:
                logging.error("Unable to convert resource %s:\a\n%s", file_path, exc)
                return

        resource_type = resource["resourceType"]
        resource_id = resource["id"]

        url = f"{self.external_fhir_server_url}/{resource_type}/{resource_id}"

        try:
            resource = replace_urn_uuid_with_reference(resource)
        except Exception as exc:
            logging.exception("Failed to convert uris to references: %s", exc)

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
                logging.info(
                    "Updated %s via %s (%s)", file_path, url, response.status_code
                )
        except requests.RequestException:
            logging.exception("Failed to PUT %s via %s", file_path, url)


def start_watcher(
    external_fhir_server_url: str,
    external_fhir_server_headers: dict[str, str],
    external_questionnaire_fce_fhir_converter_url: str | None,
):
    event_handler = FileChangeHandler(
        RESOURCE_DIR,
        external_fhir_server_url,
        external_fhir_server_headers,
        external_questionnaire_fce_fhir_converter_url,
    )
    observer = Observer()
    observer.schedule(event_handler, RESOURCE_DIR, recursive=True)
    observer.start()
    logging.info("Watching directory %s", RESOURCE_DIR)

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
