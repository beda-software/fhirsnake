import logging
import time

import requests
from files import load_resource
from initial_resources import RESOURCE_DIR
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logging.basicConfig(level=logging.INFO)


class FileChangeHandler(FileSystemEventHandler):
    def __init__(
        self, external_fhir_server_url: str, external_fhir_server_headers: dict[str, str], *args, **kwargs
    ) -> None:
        self.external_fhir_server_url = external_fhir_server_url
        self.external_fhir_server_headers = external_fhir_server_headers
        super().__init__(*args, **kwargs)

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        logging.info("Detected change in %s", file_path)
        self.process_file(file_path)

    def process_file(self, file_path):
        try:
            resource = load_resource(file_path)
        except Exception:
            logging.exception("Unable to load resource %s", file_path)
            return

        if resource is None:
            logging.error("Unable to load resource %s", file_path)
            return

        resource_type = resource["resourceType"]
        resource_id = resource["id"]
        url = f"{self.external_fhir_server_url}/{resource_type}/{resource_id}"

        try:
            response = requests.put(
                url, json=resource, headers={"Content-Type": "application/json", **self.external_fhir_server_headers}
            )
            if response.status_code >= 400:
                logging.error(
                    "Unable to update %s via %s (%s): %s", file_path, url, response.status_code, response.text()
                )
            else:
                logging.info("Updated %s via %s (%s)", file_path, url, response.status_code)
        except requests.RequestException:
            logging.exception("Failed to PUT %s via %s", file_path, url)


def start_watcher(external_fhir_server_url: str, external_fhir_server_headers: dict[str, str]):
    event_handler = FileChangeHandler(external_fhir_server_url, external_fhir_server_headers)
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
