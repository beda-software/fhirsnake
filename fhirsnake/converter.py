import requests


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
