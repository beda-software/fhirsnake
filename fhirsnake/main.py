import logging
import os
import sys
import uuid

from fastapi import FastAPI, HTTPException

from files import load_resources

logging.basicConfig(level=logging.INFO)

REPOSITORY_URL = "https://github.com/beda-software/fhirsnake/"

app = FastAPI()


@app.on_event("startup")
async def load_app_data():
    root_dir = os.path.dirname(os.path.abspath(__name__))
    logging.warning(root_dir)
    resource_dir = "resources"
    resources_abs_path = os.path.join(root_dir, resource_dir)

    if not os.path.isdir(resources_abs_path):
        logging.error(
            f"Required directory '{resources_abs_path}' does not exist. \
            Check {REPOSITORY_URL} for details. Stopping application."
        )
        sys.exit(1)

    app.state.resources = load_resources(resources_abs_path)


@app.get("/")
def read_root():
    return {
        "resourceType": "CapabilityStatement",
        "text": {
            "status": "generated",
            "div": "<div>This FHIR server provides read, \
            create and update operations for all resource types</div>",
        },
        "status": "active",
        "format": ["json"],
    }


@app.get("/$index")
def show_index():
    return app.state.resources


@app.get("/{resource_type}")
def read_resources(resource_type: str):
    return make_bundle([resource for id, resource in app.state.resources.get(resource_type, {}).items()])


@app.get("/{resource_type}/{id}")
def read_resource(resource_type: str, id: str):
    resource = app.state.resources[resource_type].get(id)
    if resource is None:
        raise HTTPException(status_code=404)
    return resource


@app.post("/{resource_type}")
def create_resource(resource_type: str, resource: dict):
    if resource_type != resource.get("resourceType"):
        raise HTTPException(status_code=400, detail="resourceType is ambiguous")
    id = resource.get("id", uuid.uuid4())
    resource["id"] = id
    if not app.state.resources.get(resource_type):
        app.state.resources[resource_type] = {}

    if app.state.resources[resource_type].get(id):
        raise HTTPException(status_code=400, detail="Resource with the same id already exists")

    app.state.resources[resource_type][id] = resource
    return resource


@app.put("/{resource_type}/{id}")
def update_resource(resource_type: str, id: str, resource: dict):
    if resource_type != resource.get("resourceType"):
        raise HTTPException(status_code=400, detail="'resourceType' is ambiguous")
    if id != resource["id"]:
        raise HTTPException(status_code=400, detail="'id' is ambiguous")

    if not app.state.resources.get(resource_type):
        app.state.resources[resource_type] = {}

    app.state.resources[resource_type][id] = resource
    return resource


def make_bundle(resource_list):
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(resource_list),
        "entry": [{"resource": resource} for resource in resource_list],
    }
