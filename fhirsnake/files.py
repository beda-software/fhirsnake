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
        file_ext = filename[-4:]
        if filename.endswith(".yaml") or filename.endswith(".json"):
            resource_id = filename[:-5]
            with open(os.path.join(path, filename)) as f:
                if file_ext == "yaml":
                    resource = yaml.safe_load(f)
                elif file_ext == "json":
                    resource = json.load(f)
                resource["resourceType"] = resource_type
                resource["id"] = resource_id
                resources[resource_id] = resource
    return resources
