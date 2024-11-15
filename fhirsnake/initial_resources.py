import logging
import os
import sys

from files import load_resources

REPOSITORY_URL = "https://github.com/beda-software/fhirsnake/"
RESOURCE_DIR = "resources"

root_dir = os.path.dirname(os.path.abspath(__name__))
resources_abs_path = os.path.join(root_dir, RESOURCE_DIR)

if not os.path.isdir(resources_abs_path):
    logging.error(
        f"Required directory '{resources_abs_path}' does not exist. \
        Check {REPOSITORY_URL} for details. Stopping application."
    )
    sys.exit(1)

initial_resources = load_resources(resources_abs_path)
