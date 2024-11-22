import json
import os

import yaml


def load_resources(abs_path):
    resources = {}

    for resource_type in os.listdir(abs_path):
        if not os.path.isdir(os.path.join(abs_path, resource_type)):
            continue
        resources[resource_type] = load_resources_by_ids(abs_path, resource_type)
    return resources


def load_resources_by_ids(abs_path, resource_type):
    resources = {}
    path = os.path.join(abs_path, resource_type)

    for filename in os.listdir(path):
        resource = load_resource(os.path.join(path, filename))
        if not resource:
            continue
        resources[resource["id"]] = resource
    return resources


def load_resource(path: str):
    # path: /path/to/resources/Patient/id.json
    resource_type = path.split("/")[-2]
    file_name = path.split("/")[-1]

    resource_id, file_ext = file_name.rsplit(".", 1)
    if file_ext not in ("yaml", "yml", "json"):
        return None

    with open(path) as f:
        if file_ext in ("yaml", "yml"):
            resource = yaml.safe_load(f)
        elif file_ext == "json":
            resource = json.load(f)
        resource["resourceType"] = resource_type
        resource["id"] = resource_id
        return resource
