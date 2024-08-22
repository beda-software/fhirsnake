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
        if not filename.endswith(".yaml"):
            continue

        resource_id = filename[:-5]
        with open(os.path.join(path, filename)) as f:
            resource = yaml.safe_load(f)
            resource["resourceType"] = resource_type
            resource["id"] = resource_id
            resources[resource_id] = resource
    return resources
