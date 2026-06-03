import json
import sys

sys.path.insert(0, "fhirsnake")

from converter import QUESTIONNAIRE_MAPPER_URL, embed_mapping_into_questionnaire, embed_mapping_into_resources

MAPPING = {"resourceType": "Mapping", "id": "patient-create", "body": {"key": "value"}}
QUESTIONNAIRE = {"resourceType": "Questionnaire", "id": "patient", "status": "active"}


def mapper_extensions(questionnaire):
    return [e for e in questionnaire.get("extension", []) if e.get("url") == QUESTIONNAIRE_MAPPER_URL]


class TestEmbedMappingIntoQuestionnaire:
    def test_reference_is_resolved_to_json_string(self):
        q = {**QUESTIONNAIRE, "mapping": [{"reference": "Mapping/patient-create"}]}
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING})

        exts = mapper_extensions(result)
        assert len(exts) == 1
        assert json.loads(exts[0]["valueString"]) == MAPPING

    def test_string_ref_is_passed_through_as_is(self):
        raw = json.dumps(MAPPING)
        q = {**QUESTIONNAIRE, "mapping": [raw]}
        result = embed_mapping_into_questionnaire(q, {})

        exts = mapper_extensions(result)
        assert len(exts) == 1
        assert exts[0]["valueString"] == raw

    def test_unknown_reference_is_skipped(self):
        q = {**QUESTIONNAIRE, "mapping": [{"reference": "Mapping/unknown"}]}
        result = embed_mapping_into_questionnaire(q, {})

        assert mapper_extensions(result) == []

    def test_existing_extensions_are_preserved(self):
        existing_ext = {"url": "http://example.com/other", "valueString": "x"}
        q = {**QUESTIONNAIRE, "extension": [existing_ext], "mapping": [{"reference": "Mapping/patient-create"}]}
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING})

        assert existing_ext in result["extension"]
        assert len(mapper_extensions(result)) == 1

    def test_mapping_field_is_removed_from_output(self):
        q = {**QUESTIONNAIRE, "mapping": [{"reference": "Mapping/patient-create"}]}
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING})

        assert "mapping" not in result

    def test_no_mapping_field_leaves_questionnaire_unchanged(self):
        result = embed_mapping_into_questionnaire(QUESTIONNAIRE, {"patient-create": MAPPING})

        assert result == QUESTIONNAIRE

    def test_does_not_mutate_input(self):
        q = {**QUESTIONNAIRE, "mapping": [{"reference": "Mapping/patient-create"}]}
        original = dict(q)
        embed_mapping_into_questionnaire(q, {"patient-create": MAPPING})

        assert q == original

    def test_urn_reference_is_resolved(self):
        q = {**QUESTIONNAIRE, "mapping": [{"reference": "urn:uuid:Mapping:patient-create"}]}
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING})

        exts = mapper_extensions(result)
        assert len(exts) == 1
        assert json.loads(exts[0]["valueString"]) == MAPPING

    def test_multiple_mappings_produce_multiple_extensions(self):
        mapping2 = {"resourceType": "Mapping", "id": "patient-edit", "body": {}}
        q = {
            **QUESTIONNAIRE,
            "mapping": [
                {"reference": "Mapping/patient-create"},
                {"reference": "Mapping/patient-edit"},
            ],
        }
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING, "patient-edit": mapping2})

        exts = mapper_extensions(result)
        assert len(exts) == 2
        ids = {json.loads(e["valueString"])["id"] for e in exts}
        assert ids == {"patient-create", "patient-edit"}


class TestEmbedMappingIntoResources:
    def test_mapping_is_excluded_from_output(self):
        resources = [MAPPING, QUESTIONNAIRE]
        result = embed_mapping_into_resources(resources)

        types = [r["resourceType"] for r in result]
        assert "Mapping" not in types

    def test_questionnaire_without_mapping_field_is_unchanged(self):
        resources = [MAPPING, QUESTIONNAIRE]
        result = embed_mapping_into_resources(resources)

        q = next(r for r in result if r["resourceType"] == "Questionnaire")
        assert q == QUESTIONNAIRE

    def test_questionnaire_with_mapping_gets_extension(self):
        q = {**QUESTIONNAIRE, "mapping": [{"reference": "Mapping/patient-create"}]}
        result = embed_mapping_into_resources([MAPPING, q])

        q_out = next(r for r in result if r["resourceType"] == "Questionnaire")
        assert len(mapper_extensions(q_out)) == 1

    def test_non_questionnaire_non_mapping_resources_pass_through(self):
        patient = {"resourceType": "Patient", "id": "p1"}
        result = embed_mapping_into_resources([MAPPING, patient])

        assert patient in result

    def test_unreferenced_mapping_is_still_excluded(self):
        result = embed_mapping_into_resources([MAPPING, QUESTIONNAIRE])

        assert all(r["resourceType"] != "Mapping" for r in result)
