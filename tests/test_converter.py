import json
import sys

sys.path.insert(0, "fhirsnake")

from converter import QUESTIONNAIRE_MAPPER_URL, embed_mapping_into_questionnaire, embed_mapping_into_resources

MAPPING_JUTE = {"resourceType": "Mapping", "id": "patient-create", "body": {"key": "value"}}
MAPPING_FPML = {"resourceType": "Mapping", "id": "patient-edit", "type": "FHIRPath", "body": {"key": "value"}}
QUESTIONNAIRE = {"resourceType": "Questionnaire", "id": "patient", "status": "active"}


def mapper_extensions(questionnaire):
    return [e for e in questionnaire.get("extension", []) if e.get("url") == QUESTIONNAIRE_MAPPER_URL]


class TestEmbedMappingIntoQuestionnaire:
    def test_value_reference_resolved_to_value_expression(self):
        q = {**QUESTIONNAIRE, "mapping": [{"valueReference": {"reference": "Mapping/patient-create"}}]}
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING_JUTE})

        exts = mapper_extensions(result)
        assert len(exts) == 1
        assert "valueExpression" in exts[0]
        assert json.loads(exts[0]["valueExpression"]["expression"]) == MAPPING_JUTE

    def test_language_is_jute_by_default(self):
        q = {**QUESTIONNAIRE, "mapping": [{"valueReference": {"reference": "Mapping/patient-create"}}]}
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING_JUTE})

        assert mapper_extensions(result)[0]["valueExpression"]["language"] == "jute"

    def test_language_is_fpml_for_fhirpath_type(self):
        q = {**QUESTIONNAIRE, "mapping": [{"valueReference": {"reference": "Mapping/patient-edit"}}]}
        result = embed_mapping_into_questionnaire(q, {"patient-edit": MAPPING_FPML})

        assert mapper_extensions(result)[0]["valueExpression"]["language"] == "fpml"

    def test_value_expression_item_is_passed_through(self):
        expr = {"language": "jute", "expression": json.dumps(MAPPING_JUTE)}
        q = {**QUESTIONNAIRE, "mapping": [{"valueExpression": expr}]}
        result = embed_mapping_into_questionnaire(q, {})

        exts = mapper_extensions(result)
        assert len(exts) == 1
        assert exts[0]["valueExpression"] == expr

    def test_unresolvable_value_reference_becomes_value_reference_extension(self):
        q = {**QUESTIONNAIRE, "mapping": [{"valueReference": {"reference": "Mapping/unknown"}}]}
        result = embed_mapping_into_questionnaire(q, {})

        exts = mapper_extensions(result)
        assert len(exts) == 1
        assert exts[0]["valueReference"] == {"reference": "Mapping/unknown"}

    def test_bare_reference_is_resolved(self):
        q = {**QUESTIONNAIRE, "mapping": [{"reference": "Mapping/patient-create"}]}
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING_JUTE})

        exts = mapper_extensions(result)
        assert len(exts) == 1
        assert json.loads(exts[0]["valueExpression"]["expression"]) == MAPPING_JUTE

    def test_bare_unresolvable_reference_becomes_value_reference_extension(self):
        q = {**QUESTIONNAIRE, "mapping": [{"reference": "Mapping/unknown"}]}
        result = embed_mapping_into_questionnaire(q, {})

        exts = mapper_extensions(result)
        assert len(exts) == 1
        assert exts[0]["valueReference"] == {"reference": "Mapping/unknown"}

    def test_urn_value_reference_is_resolved(self):
        q = {**QUESTIONNAIRE, "mapping": [{"valueReference": {"reference": "urn:uuid:Mapping:patient-create"}}]}
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING_JUTE})

        exts = mapper_extensions(result)
        assert len(exts) == 1
        assert json.loads(exts[0]["valueExpression"]["expression"]) == MAPPING_JUTE

    def test_existing_extensions_are_preserved(self):
        existing_ext = {"url": "http://example.com/other", "valueString": "x"}
        q = {
            **QUESTIONNAIRE,
            "extension": [existing_ext],
            "mapping": [{"valueReference": {"reference": "Mapping/patient-create"}}],
        }
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING_JUTE})

        assert existing_ext in result["extension"]
        assert len(mapper_extensions(result)) == 1

    def test_mapping_field_is_removed_from_output(self):
        q = {**QUESTIONNAIRE, "mapping": [{"valueReference": {"reference": "Mapping/patient-create"}}]}
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING_JUTE})

        assert "mapping" not in result

    def test_no_mapping_field_leaves_questionnaire_unchanged(self):
        result = embed_mapping_into_questionnaire(QUESTIONNAIRE, {"patient-create": MAPPING_JUTE})

        assert result == QUESTIONNAIRE

    def test_does_not_mutate_input(self):
        q = {**QUESTIONNAIRE, "mapping": [{"valueReference": {"reference": "Mapping/patient-create"}}]}
        original = dict(q)
        embed_mapping_into_questionnaire(q, {"patient-create": MAPPING_JUTE})

        assert q == original

    def test_multiple_mappings_produce_multiple_extensions(self):
        q = {
            **QUESTIONNAIRE,
            "mapping": [
                {"valueReference": {"reference": "Mapping/patient-create"}},
                {"valueReference": {"reference": "Mapping/patient-edit"}},
            ],
        }
        result = embed_mapping_into_questionnaire(q, {"patient-create": MAPPING_JUTE, "patient-edit": MAPPING_FPML})

        exts = mapper_extensions(result)
        assert len(exts) == 2
        ids = {json.loads(e["valueExpression"]["expression"])["id"] for e in exts}
        assert ids == {"patient-create", "patient-edit"}


class TestEmbedMappingIntoResources:
    def test_mapping_is_excluded_from_output(self):
        result = embed_mapping_into_resources([MAPPING_JUTE, QUESTIONNAIRE])

        assert all(r["resourceType"] != "Mapping" for r in result)

    def test_questionnaire_without_mapping_field_is_unchanged(self):
        result = embed_mapping_into_resources([MAPPING_JUTE, QUESTIONNAIRE])

        q = next(r for r in result if r["resourceType"] == "Questionnaire")
        assert q == QUESTIONNAIRE

    def test_questionnaire_with_mapping_gets_extension(self):
        q = {**QUESTIONNAIRE, "mapping": [{"valueReference": {"reference": "Mapping/patient-create"}}]}
        result = embed_mapping_into_resources([MAPPING_JUTE, q])

        q_out = next(r for r in result if r["resourceType"] == "Questionnaire")
        assert len(mapper_extensions(q_out)) == 1

    def test_non_questionnaire_non_mapping_resources_pass_through(self):
        patient = {"resourceType": "Patient", "id": "p1"}
        result = embed_mapping_into_resources([MAPPING_JUTE, patient])

        assert patient in result

    def test_unreferenced_mapping_is_still_excluded(self):
        result = embed_mapping_into_resources([MAPPING_JUTE, QUESTIONNAIRE])

        assert all(r["resourceType"] != "Mapping" for r in result)
