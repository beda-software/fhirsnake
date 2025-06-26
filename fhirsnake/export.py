import gzip
import json

import ndjson
from converter import convert_resources
from initial_resources import initial_resources
from utils import substitute_env_vars


def export_resources(output: str, external_questionnaire_fce_fhir_converter_url: str | None) -> None:
    is_ndjson = "ndjson" in output
    gzipped = output.endswith(".gz")
    resources_list = flatten_resources(initial_resources)

    if external_questionnaire_fce_fhir_converter_url:
        resources_list = convert_resources(resources_list, external_questionnaire_fce_fhir_converter_url)

    if is_ndjson:
        dumped_resources = ndjson.dumps(resources_list)
    else:
        dumped_resources = json.dumps(
            {
                "resourceType": "Bundle",
                "type": "transaction",
                "entry": [
                    {
                        "fullUrl": f"urn:uuid:{resource['resourceType']}:{resource['id']}",
                        "request": {"method": "PUT", "url": f"/{resource['resourceType']}/{resource['id']}"},
                        "resource": resource,
                    }
                    for resource in resources_list
                ],
            }
        )

    if gzipped:
        with gzip.open(output, "w+") as f:
            f.write(dumped_resources.encode())
    else:
        with open(output, "w+") as f:
            f.write(dumped_resources)


def flatten_resources(resources: dict[str, dict[str, dict]]) -> list[dict]:
    return [
        substitute_env_vars(resource)
        for by_resource_type in resources.values()
        for resource in by_resource_type.values()
    ]
