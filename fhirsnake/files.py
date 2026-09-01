import json
import logging
import os

import yaml


def load_resources(root_path: str, prefer_resource_id: bool = False):
    resources = {}

    for resource_type in os.listdir(root_path):
        if not os.path.isdir(os.path.join(root_path, resource_type)):
            continue
        resources[resource_type] = load_resources_by_ids(root_path, resource_type, prefer_resource_id)
    return resources


def load_resources_by_ids(root_path: str, resource_type: str, prefer_resource_id: bool = False):
    resources = {}
    for abs_files_dir, _, files in os.walk(os.path.join(root_path, resource_type)):
        for filename in files:
            resource = load_resource(root_path, os.path.join(abs_files_dir, filename), prefer_resource_id)
            if not resource:
                continue
            resources[resource["id"]] = resource
    return resources


def load_resource(root_path: str, abs_path: str, prefer_resource_id: bool = False):
    path = os.path.relpath(abs_path, root_path)
    # path: Patient/id.json or Patient/subdir/id.json
    resource_type, *_, file_name = path.split("/")
    if "." not in file_name:
        return None

    resource_id, file_ext = file_name.rsplit(".", 1)

    if file_ext not in ("yaml", "yml", "json"):
        return None

    with open(abs_path) as f:
        if file_ext in ("yaml", "yml"):
            resource = yaml.safe_load(f)
        elif file_ext == "json":
            resource = json.load(f)
        resource["resourceType"] = resource_type
        declared_id = resource.get("id")
        if prefer_resource_id and declared_id:
            resource["id"] = declared_id
        else:
            if declared_id and declared_id != resource_id:
                logging.warning(
                    "%s: declared id '%s' differs from filename-derived id '%s', using '%s'; "
                    "pass --prefer-resource-id to use the declared id",
                    path,
                    declared_id,
                    resource_id,
                    resource_id,
                )
            resource["id"] = resource_id
        return resource
