import json

import requests
from utils import convert_uri_to_reference

QUESTIONNAIRE_MAPPER_URL = "https://emr-core.beda.software/StructureDefinition/questionnaire-mapper"


def _mapping_language(mapping: dict) -> str:
    return "fpml" if mapping.get("type") == "FHIRPath" else "jute"


def embed_mapping_into_questionnaire(questionnaire: dict, mappings_by_id: dict[str, dict]) -> dict:
    questionnaire = {**questionnaire}
    mapping_refs = questionnaire.pop("mapping", [])
    new_extensions = []
    for item in mapping_refs:
        if "valueExpression" in item:
            new_extensions.append({"url": QUESTIONNAIRE_MAPPER_URL, "valueExpression": item["valueExpression"]})
        elif "valueReference" in item:
            ref_str = item["valueReference"].get("reference", "")
            mapping_id = convert_uri_to_reference(ref_str).split("/")[-1]
            mapping = mappings_by_id.get(mapping_id)
            if mapping:
                new_extensions.append(
                    {
                        "url": QUESTIONNAIRE_MAPPER_URL,
                        "valueExpression": {"language": _mapping_language(mapping), "expression": json.dumps(mapping)},
                    }
                )
            else:
                new_extensions.append({"url": QUESTIONNAIRE_MAPPER_URL, "valueReference": item["valueReference"]})
        elif "reference" in item:
            ref_str = item["reference"]
            mapping_id = convert_uri_to_reference(ref_str).split("/")[-1]
            mapping = mappings_by_id.get(mapping_id)
            if mapping:
                new_extensions.append(
                    {
                        "url": QUESTIONNAIRE_MAPPER_URL,
                        "valueExpression": {"language": _mapping_language(mapping), "expression": json.dumps(mapping)},
                    }
                )
            else:
                new_extensions.append({"url": QUESTIONNAIRE_MAPPER_URL, "valueReference": {"reference": ref_str}})
    if new_extensions:
        questionnaire["extension"] = questionnaire.get("extension", []) + new_extensions
    return questionnaire


def embed_mapping_into_resources(resources_list: list[dict]) -> list[dict]:
    mappings_by_id = {r["id"]: r for r in resources_list if r["resourceType"] == "Mapping"}
    result = []
    for resource in resources_list:
        if resource["resourceType"] == "Mapping":
            continue
        if resource["resourceType"] == "Questionnaire" and "mapping" in resource:
            resource = embed_mapping_into_questionnaire(resource, mappings_by_id)
        result.append(resource)
    return result


def convert_resources(resources_list: list[dict], external_questionnaire_fce_fhir_converter_url: str) -> list[dict]:
    new_resources_list: list[dict] = []
    for resource in resources_list:
        if resource["resourceType"] == "Questionnaire":
            resource = convert_questionnaire_fce_to_fhir(resource, external_questionnaire_fce_fhir_converter_url)

        new_resources_list.append(resource)

    return new_resources_list


def convert_questionnaire_fce_to_fhir(resource: dict, external_questionnaire_fce_fhir_converter_url: str) -> dict:
    response = requests.post(
        external_questionnaire_fce_fhir_converter_url,
        json=resource,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    return response.json()
