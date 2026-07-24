import gzip
import json

import ndjson
from converter import convert_resources, embed_mapping_into_resources
from files import load_resources
from questionnaire_language import merge_questionnaire_language_variants
from utils import substitute_env_vars


def export_resources(
    input_dirs: list[str],
    output: str,
    external_questionnaire_fce_fhir_converter_url: str | None,
    embed_mapping: bool = False,
) -> None:
    is_ndjson = "ndjson" in output
    gzipped = output.endswith(".gz")
    resources_list = []
    for input_dir in input_dirs:
        resources_list.extend(flatten_resources(load_resources(input_dir)))
    resources_list = merge_questionnaire_language_variants(resources_list)
    if embed_mapping:
        resources_list = embed_mapping_into_resources(resources_list)
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
                        "request": {
                            "method": "PUT",
                            "url": f"/{resource['resourceType']}/{resource['id']}",
                        },
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
