import json
import logging
import time

import requests
from converter import convert_questionnaire_fce_to_fhir, embed_mapping_into_questionnaire
from files import load_resource, load_resources
from utils import replace_urn_uuid_with_reference, substitute_env_vars
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(level=logging.INFO)


def _questionnaires_referencing_mapping(questionnaires: dict, mapping_id: str):
    for q in questionnaires.values():
        for ref in q.get("mapping", []):
            if isinstance(ref, dict) and ref.get("reference", "").split("/")[-1] == mapping_id:
                yield q
                break


class FileChangeHandler(FileSystemEventHandler):
    def __init__(
        self,
        target_dir: str,
        external_fhir_server_url: str,
        external_fhir_server_headers: dict[str, str],
        external_questionnaire_fce_fhir_converter_url: str | None,
        embed_mapping: bool = False,
        all_resources: dict | None = None,
        *args,
        **kwargs,
    ) -> None:
        self.target_dir = target_dir
        self.external_fhir_server_url = external_fhir_server_url
        self.external_fhir_server_headers = external_fhir_server_headers
        self.external_questionnaire_fce_fhir_converter_url = external_questionnaire_fce_fhir_converter_url
        self.embed_mapping = embed_mapping
        self.all_resources = all_resources if all_resources is not None else {}
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

        resource_type = resource["resourceType"]
        resource_id = resource["id"]

        if self.embed_mapping and resource_type == "Mapping":
            self.all_resources.setdefault("Mapping", {})[resource_id] = resource
            mappings_by_id = self.all_resources.get("Mapping", {})
            for questionnaire in list(
                _questionnaires_referencing_mapping(self.all_resources.get("Questionnaire", {}), resource_id)
            ):
                processed = embed_mapping_into_questionnaire(questionnaire, mappings_by_id)
                self._send_resource(processed)
            return

        if self.embed_mapping and resource_type == "Questionnaire":
            self.all_resources.setdefault("Questionnaire", {})[resource_id] = resource
            resource = embed_mapping_into_questionnaire(resource, self.all_resources.get("Mapping", {}))

        elif self.external_questionnaire_fce_fhir_converter_url and resource_type == "Questionnaire":
            try:
                resource = convert_questionnaire_fce_to_fhir(
                    resource, self.external_questionnaire_fce_fhir_converter_url
                )
            except Exception:
                logging.exception("Unable to convert resource %s", file_path)
                return

        self._send_resource(resource)

    def _send_resource(self, resource: dict):
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
                    "Unable to update %s/%s via %s (%s):\a\n %s",
                    resource_type,
                    resource_id,
                    url,
                    response.status_code,
                    formatted_error,
                )
            else:
                logging.info("Updated %s/%s via %s (%s)", resource_type, resource_id, url, response.status_code)
        except requests.RequestException:
            logging.exception("Failed to PUT %s/%s via %s", resource_type, resource_id, url)


def start_watcher(
    input_dirs: list[str],
    external_fhir_server_url: str,
    external_fhir_server_headers: dict[str, str],
    external_questionnaire_fce_fhir_converter_url: str | None,
    embed_mapping: bool = False,
):
    all_resources: dict = {}
    if embed_mapping:
        for input_dir in input_dirs:
            for resource_type, by_id in load_resources(input_dir).items():
                all_resources.setdefault(resource_type, {}).update(by_id)

    observer = Observer()

    for input_dir in input_dirs:
        event_handler = FileChangeHandler(
            input_dir,
            external_fhir_server_url,
            external_fhir_server_headers,
            external_questionnaire_fce_fhir_converter_url,
            embed_mapping=embed_mapping,
            all_resources=all_resources,
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
