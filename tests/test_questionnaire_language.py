import copy
import os
import sys

import pytest

sys.path.insert(0, "fhirsnake")

from export import flatten_resources
from files import load_resources
from questionnaire_language import merge_questionnaire_language_variants

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "..", "resources")

PAIN_LEVEL_BASELINE = {
    "linkId": "pain-level",
    "type": "choice",
    "text": "Pain level",
    "answerOption": [
        {
            "valueCoding": {
                "code": "mild",
                "system": "http://example.org/pain-level",
                "display": "Mild",
            }
        },
        {
            "valueCoding": {
                "code": "severe",
                "system": "http://example.org/pain-level",
                "display": "Severe",
            }
        },
    ],
}

PAIN_LEVEL_VARIANT_DE = {
    "linkId": "pain-level",
    "type": "choice",
    "text": "Schmerzintensität",
    "answerOption": [
        {"valueCoding": {"code": "mild", "display": "Leicht"}},
        {"valueCoding": {"code": "severe", "display": "Schwer"}},
    ],
}

PAIN_LEVEL_VARIANT_FR = {
    "linkId": "pain-level",
    "type": "choice",
    "text": "Niveau de douleur",
    "answerOption": [
        {"valueCoding": {"code": "severe", "display": "Sévère"}},
        {"valueCoding": {"code": "mild", "display": "Léger"}},
    ],
}

PAIN_LEVEL_MERGED_EN_DE = {
    "linkId": "pain-level",
    "type": "choice",
    "text": "Pain level",
    "_text": {
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "de"},
                    {"url": "content", "valueString": "Schmerzintensität"},
                ],
            },
        ]
    },
    "answerOption": [
        {
            "valueCoding": {
                "code": "mild",
                "system": "http://example.org/pain-level",
                "display": "Mild",
                "_display": {
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/translation",
                            "extension": [
                                {"url": "lang", "valueCode": "de"},
                                {"url": "content", "valueString": "Leicht"},
                            ],
                        },
                    ]
                },
            }
        },
        {
            "valueCoding": {
                "code": "severe",
                "system": "http://example.org/pain-level",
                "display": "Severe",
                "_display": {
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/translation",
                            "extension": [
                                {"url": "lang", "valueCode": "de"},
                                {"url": "content", "valueString": "Schwer"},
                            ],
                        },
                    ]
                },
            }
        },
    ],
}

PAIN_LEVEL_MERGED_EN_DE_FR = {
    "linkId": "pain-level",
    "type": "choice",
    "text": "Pain level",
    "_text": {
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "de"},
                    {"url": "content", "valueString": "Schmerzintensität"},
                ],
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "fr"},
                    {"url": "content", "valueString": "Niveau de douleur"},
                ],
            },
        ]
    },
    "answerOption": [
        {
            "valueCoding": {
                "code": "mild",
                "system": "http://example.org/pain-level",
                "display": "Mild",
                "_display": {
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/translation",
                            "extension": [
                                {"url": "lang", "valueCode": "de"},
                                {"url": "content", "valueString": "Leicht"},
                            ],
                        },
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/translation",
                            "extension": [
                                {"url": "lang", "valueCode": "fr"},
                                {"url": "content", "valueString": "Léger"},
                            ],
                        },
                    ]
                },
            }
        },
        {
            "valueCoding": {
                "code": "severe",
                "system": "http://example.org/pain-level",
                "display": "Severe",
                "_display": {
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/translation",
                            "extension": [
                                {"url": "lang", "valueCode": "de"},
                                {"url": "content", "valueString": "Schwer"},
                            ],
                        },
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/translation",
                            "extension": [
                                {"url": "lang", "valueCode": "fr"},
                                {"url": "content", "valueString": "Sévère"},
                            ],
                        },
                    ]
                },
            }
        },
    ],
}

BASELINE = {
    "resourceType": "Questionnaire",
    "id": "demo-questionnaire",
    "url": "demo-questionnaire",
    "language": "en",
    "status": "active",
    "title": "Demo questionnaire",
    "description": "A short demo questionnaire for language merging",
    "item": [
        {
            "type": "group",
            "linkId": "group-1",
            "text": "Group 1",
            "item": [
                {
                    "linkId": "chief-complaint",
                    "type": "string",
                    "text": "Chief complaint",
                }
            ],
        },
        copy.deepcopy(PAIN_LEVEL_BASELINE),
    ],
}

VARIANT_DE_NESTED = {
    "resourceType": "Questionnaire",
    "id": "demo-questionnaire.de",
    "url": "demo-questionnaire",
    "language": "de",
    "status": "active",
    "title": "Demo-Fragebogen",
    "description": "Ein kurzer Demo-Fragebogen für Sprachzusammenführung",
    "item": [
        {
            "type": "group",
            "linkId": "group-1",
            "text": "Gruppe 1",
            "item": [
                {
                    "linkId": "chief-complaint",
                    "type": "string",
                    "text": "Hauptbeschwerde",
                }
            ],
        },
        copy.deepcopy(PAIN_LEVEL_VARIANT_DE),
    ],
}

VARIANT_FR_FLAT = {
    "resourceType": "Questionnaire",
    "id": "demo-questionnaire.fr",
    "url": "demo-questionnaire",
    "language": "fr",
    "status": "active",
    "title": "Questionnaire de démonstration",
    "description": "Un court questionnaire de démonstration pour la fusion de langues",
    "item": [
        {
            "type": "group",
            "linkId": "group-1",
            "text": "Groupe 1",
        },
        {
            "linkId": "chief-complaint",
            "type": "string",
            "text": "Motif de consultation",
        },
        copy.deepcopy(PAIN_LEVEL_VARIANT_FR),
    ],
}

MERGED_EN_DE_FR = {
    "resourceType": "Questionnaire",
    "id": "demo-questionnaire",
    "url": "demo-questionnaire",
    "language": "en",
    "status": "active",
    "title": "Demo questionnaire",
    "description": "A short demo questionnaire for language merging",
    "_title": {
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "de"},
                    {"url": "content", "valueString": "Demo-Fragebogen"},
                ],
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "fr"},
                    {"url": "content", "valueString": "Questionnaire de démonstration"},
                ],
            },
        ]
    },
    "_description": {
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "de"},
                    {"url": "content", "valueString": "Ein kurzer Demo-Fragebogen für Sprachzusammenführung"},
                ],
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "fr"},
                    {
                        "url": "content",
                        "valueString": "Un court questionnaire de démonstration pour la fusion de langues",
                    },
                ],
            },
        ]
    },
    "item": [
        {
            "type": "group",
            "linkId": "group-1",
            "text": "Group 1",
            "_text": {
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/translation",
                        "extension": [
                            {"url": "lang", "valueCode": "de"},
                            {"url": "content", "valueString": "Gruppe 1"},
                        ],
                    },
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/translation",
                        "extension": [
                            {"url": "lang", "valueCode": "fr"},
                            {"url": "content", "valueString": "Groupe 1"},
                        ],
                    },
                ]
            },
            "item": [
                {
                    "linkId": "chief-complaint",
                    "type": "string",
                    "text": "Chief complaint",
                    "_text": {
                        "extension": [
                            {
                                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                                "extension": [
                                    {"url": "lang", "valueCode": "de"},
                                    {"url": "content", "valueString": "Hauptbeschwerde"},
                                ],
                            },
                            {
                                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                                "extension": [
                                    {"url": "lang", "valueCode": "fr"},
                                    {"url": "content", "valueString": "Motif de consultation"},
                                ],
                            },
                        ]
                    },
                }
            ],
        },
        copy.deepcopy(PAIN_LEVEL_MERGED_EN_DE_FR),
    ],
}

MERGED_EN_DE = {
    "resourceType": "Questionnaire",
    "id": "demo-questionnaire",
    "url": "demo-questionnaire",
    "language": "en",
    "status": "active",
    "title": "Demo questionnaire",
    "description": "A short demo questionnaire for language merging",
    "_title": {
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "de"},
                    {"url": "content", "valueString": "Demo-Fragebogen"},
                ],
            },
        ]
    },
    "_description": {
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "de"},
                    {"url": "content", "valueString": "Ein kurzer Demo-Fragebogen für Sprachzusammenführung"},
                ],
            },
        ]
    },
    "item": [
        {
            "type": "group",
            "linkId": "group-1",
            "text": "Group 1",
            "_text": {
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/translation",
                        "extension": [
                            {"url": "lang", "valueCode": "de"},
                            {"url": "content", "valueString": "Gruppe 1"},
                        ],
                    },
                ]
            },
            "item": [
                {
                    "linkId": "chief-complaint",
                    "type": "string",
                    "text": "Chief complaint",
                    "_text": {
                        "extension": [
                            {
                                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                                "extension": [
                                    {"url": "lang", "valueCode": "de"},
                                    {"url": "content", "valueString": "Hauptbeschwerde"},
                                ],
                            },
                        ]
                    },
                }
            ],
        },
        copy.deepcopy(PAIN_LEVEL_MERGED_EN_DE),
    ],
}


class TestMergeQuestionnaireLanguageVariants:
    def test_single_questionnaire_passes_through_unchanged(self):
        questionnaire = {
            "resourceType": "Questionnaire",
            "id": "alone",
            "url": "alone",
            "status": "active",
            "title": "Alone",
            "item": [{"linkId": "q1", "type": "string", "text": "Question"}],
        }

        result = merge_questionnaire_language_variants([questionnaire])

        assert result == [questionnaire]

    def test_single_questionnaire_with_non_en_language_passes_through(self):
        questionnaire = {
            "resourceType": "Questionnaire",
            "id": "de-only",
            "url": "de-only",
            "language": "de",
            "status": "active",
            "title": "Nur Deutsch",
            "item": [{"linkId": "q1", "type": "string", "text": "Frage"}],
        }

        result = merge_questionnaire_language_variants([questionnaire])

        assert result == [questionnaire]

    def test_single_questionnaire_without_language_passes_through(self):
        questionnaire = {
            "resourceType": "Questionnaire",
            "id": "no-lang",
            "status": "active",
            "title": "No language",
            "item": [{"linkId": "q1", "type": "string", "text": "Question"}],
        }

        result = merge_questionnaire_language_variants([questionnaire])

        assert result == [questionnaire]

    def test_two_variants_merge_nested_de(self):
        result = merge_questionnaire_language_variants([copy.deepcopy(BASELINE), copy.deepcopy(VARIANT_DE_NESTED)])

        assert result == [MERGED_EN_DE]

    def test_flat_and_nested_variants_produce_same_merged_result(self):
        variant_de_flat = {
            "resourceType": "Questionnaire",
            "id": "demo-questionnaire.de",
            "url": "demo-questionnaire",
            "language": "de",
            "status": "active",
            "title": "Demo-Fragebogen",
            "description": "Ein kurzer Demo-Fragebogen für Sprachzusammenführung",
            "item": [
                {"type": "group", "linkId": "group-1", "text": "Gruppe 1"},
                {"linkId": "chief-complaint", "type": "string", "text": "Hauptbeschwerde"},
                copy.deepcopy(PAIN_LEVEL_VARIANT_DE),
            ],
        }

        nested_result = merge_questionnaire_language_variants(
            [copy.deepcopy(BASELINE), copy.deepcopy(VARIANT_DE_NESTED)]
        )
        flat_result = merge_questionnaire_language_variants([copy.deepcopy(BASELINE), variant_de_flat])

        assert nested_result == [MERGED_EN_DE]
        assert flat_result == [MERGED_EN_DE]
        assert nested_result == flat_result

    def test_three_variants_merge_en_de_fr(self):
        result = merge_questionnaire_language_variants(
            [copy.deepcopy(BASELINE), copy.deepcopy(VARIANT_DE_NESTED), copy.deepcopy(VARIANT_FR_FLAT)]
        )

        assert result == [MERGED_EN_DE_FR]

    def test_grouping_falls_back_to_id_when_url_missing(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "shared-id",
            "language": "en",
            "status": "active",
            "title": "Shared",
            "item": [{"linkId": "q1", "type": "string", "text": "Hello"}],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "shared-id",
            "language": "de",
            "status": "active",
            "title": "Geteilt",
            "item": [{"linkId": "q1", "type": "string", "text": "Hallo"}],
        }

        result = merge_questionnaire_language_variants([baseline, variant])

        expected = {
            "resourceType": "Questionnaire",
            "id": "shared-id",
            "language": "en",
            "status": "active",
            "title": "Shared",
            "_title": {
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/translation",
                        "extension": [
                            {"url": "lang", "valueCode": "de"},
                            {"url": "content", "valueString": "Geteilt"},
                        ],
                    },
                ]
            },
            "item": [
                {
                    "linkId": "q1",
                    "type": "string",
                    "text": "Hello",
                    "_text": {
                        "extension": [
                            {
                                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                                "extension": [
                                    {"url": "lang", "valueCode": "de"},
                                    {"url": "content", "valueString": "Hallo"},
                                ],
                            },
                        ]
                    },
                }
            ],
        }
        assert result == [expected]

    def test_defaults_missing_baseline_language_to_en(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "status": "active",
            "title": "Demo",
            "item": [{"linkId": "q1", "type": "string", "text": "Hello"}],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "demo.de",
            "url": "demo",
            "language": "de",
            "status": "active",
            "title": "Demo DE",
            "item": [{"linkId": "q1", "type": "string", "text": "Hallo"}],
        }

        result = merge_questionnaire_language_variants([baseline, variant])

        expected = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "title": "Demo",
            "_title": {
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/translation",
                        "extension": [
                            {"url": "lang", "valueCode": "de"},
                            {"url": "content", "valueString": "Demo DE"},
                        ],
                    },
                ]
            },
            "item": [
                {
                    "linkId": "q1",
                    "type": "string",
                    "text": "Hello",
                    "_text": {
                        "extension": [
                            {
                                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                                "extension": [
                                    {"url": "lang", "valueCode": "de"},
                                    {"url": "content", "valueString": "Hallo"},
                                ],
                            },
                        ]
                    },
                }
            ],
        }
        assert result == [expected]

    def test_raises_when_no_baseline(self):
        de = {
            "resourceType": "Questionnaire",
            "id": "demo.de",
            "url": "demo",
            "language": "de",
            "status": "active",
            "item": [],
        }
        fr = {
            "resourceType": "Questionnaire",
            "id": "demo.fr",
            "url": "demo",
            "language": "fr",
            "status": "active",
            "item": [],
        }

        with pytest.raises(ValueError, match="No baseline Questionnaire"):
            merge_questionnaire_language_variants([de, fr])

    def test_raises_when_multiple_baselines(self):
        first = {
            "resourceType": "Questionnaire",
            "id": "demo-1",
            "url": "demo",
            "language": "en",
            "status": "active",
            "item": [],
        }
        second = {
            "resourceType": "Questionnaire",
            "id": "demo-2",
            "url": "demo",
            "status": "active",
            "item": [],
        }

        with pytest.raises(ValueError, match="Multiple baseline Questionnaires"):
            merge_questionnaire_language_variants([first, second])

    def test_raises_when_variant_has_empty_language(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "item": [],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "demo-variant",
            "url": "demo",
            "language": "",
            "status": "active",
            "item": [],
        }

        with pytest.raises(ValueError, match="missing 'language'"):
            merge_questionnaire_language_variants([baseline, variant])

    def test_raises_when_duplicate_variant_language(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "item": [],
        }
        first_de = {
            "resourceType": "Questionnaire",
            "id": "demo.de-1",
            "url": "demo",
            "language": "de",
            "status": "active",
            "item": [],
        }
        second_de = {
            "resourceType": "Questionnaire",
            "id": "demo.de-2",
            "url": "demo",
            "language": "de",
            "status": "active",
            "item": [],
        }

        with pytest.raises(ValueError, match="Duplicate Questionnaire language"):
            merge_questionnaire_language_variants([baseline, first_de, second_de])

    def test_skips_variant_link_id_missing_from_baseline(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "title": "Demo",
            "item": [{"linkId": "known", "type": "string", "text": "Known"}],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "demo.fr",
            "url": "demo",
            "language": "fr",
            "status": "active",
            "title": "Démo",
            "item": [
                {"linkId": "known", "type": "string", "text": "Connu"},
                {"linkId": "extra-only-in-fr", "type": "string", "text": "Extra"},
            ],
        }

        result = merge_questionnaire_language_variants([baseline, variant])

        expected = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "title": "Demo",
            "_title": {
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/translation",
                        "extension": [
                            {"url": "lang", "valueCode": "fr"},
                            {"url": "content", "valueString": "Démo"},
                        ],
                    },
                ]
            },
            "item": [
                {
                    "linkId": "known",
                    "type": "string",
                    "text": "Known",
                    "_text": {
                        "extension": [
                            {
                                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                                "extension": [
                                    {"url": "lang", "valueCode": "fr"},
                                    {"url": "content", "valueString": "Connu"},
                                ],
                            },
                        ]
                    },
                }
            ],
        }
        assert result == [expected]

    def test_raises_when_baseline_item_missing_text(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "item": [{"linkId": "q1", "type": "string"}],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "demo.fr",
            "url": "demo",
            "language": "fr",
            "status": "active",
            "item": [{"linkId": "q1", "type": "string", "text": "Question"}],
        }

        with pytest.raises(ValueError, match="baseline item 'q1' is missing 'text'"):
            merge_questionnaire_language_variants([baseline, variant])

    def test_raises_when_variant_answer_option_code_missing_from_baseline(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Pain level",
                    "answerOption": [
                        {"valueCoding": {"code": "mild", "display": "Mild"}},
                    ],
                }
            ],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "demo.de",
            "url": "demo",
            "language": "de",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Schmerzintensität",
                    "answerOption": [
                        {"valueCoding": {"code": "mild", "display": "Leicht"}},
                        {"valueCoding": {"code": "unknown", "display": "Unbekannt"}},
                    ],
                }
            ],
        }

        with pytest.raises(ValueError, match="has no answerOption with code 'unknown'"):
            merge_questionnaire_language_variants([baseline, variant])

    def test_raises_when_baseline_answer_option_missing_display(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Pain level",
                    "answerOption": [
                        {"valueCoding": {"code": "mild"}},
                    ],
                }
            ],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "demo.de",
            "url": "demo",
            "language": "de",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Schmerzintensität",
                    "answerOption": [
                        {"valueCoding": {"code": "mild", "display": "Leicht"}},
                    ],
                }
            ],
        }

        with pytest.raises(ValueError, match="answerOption 'mild' is missing 'display'"):
            merge_questionnaire_language_variants([baseline, variant])

    def test_skips_variant_answer_option_without_code(self, caplog):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Pain level",
                    "answerOption": [
                        {"valueCoding": {"code": "mild", "display": "Mild"}},
                    ],
                }
            ],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "demo.de",
            "url": "demo",
            "language": "de",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Schmerzintensität",
                    "answerOption": [
                        {"valueCoding": {"code": "mild", "display": "Leicht"}},
                        {"valueCoding": {"display": "Ohne Code"}},
                    ],
                }
            ],
        }

        with caplog.at_level("WARNING"):
            result = merge_questionnaire_language_variants([baseline, variant])

        assert (
            "Skipping answerOption without code in linkId 'pain-level' "
            "in language 'de' for Questionnaire 'demo'"
        ) in caplog.text
        assert result[0]["item"][0]["answerOption"][0]["valueCoding"]["_display"]["extension"] == [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "de"},
                    {"url": "content", "valueString": "Leicht"},
                ],
            },
        ]

    def test_skips_baseline_answer_option_without_code(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Pain level",
                    "answerOption": [
                        {"valueCoding": {"display": "No code"}},
                        {"valueCoding": {"code": "mild", "display": "Mild"}},
                    ],
                }
            ],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "demo.de",
            "url": "demo",
            "language": "de",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Schmerzintensität",
                    "answerOption": [
                        {"valueCoding": {"code": "mild", "display": "Leicht"}},
                    ],
                }
            ],
        }

        result = merge_questionnaire_language_variants([baseline, variant])

        assert result[0]["item"][0]["answerOption"][0] == {"valueCoding": {"display": "No code"}}
        assert result[0]["item"][0]["answerOption"][1]["valueCoding"]["_display"]["extension"] == [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "de"},
                    {"url": "content", "valueString": "Leicht"},
                ],
            },
        ]

    def test_skips_answer_option_without_value_coding(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Pain level",
                    "answerOption": [
                        {"valueString": "free text"},
                        {"valueCoding": {"code": "mild", "display": "Mild"}},
                    ],
                }
            ],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "demo.de",
            "url": "demo",
            "language": "de",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Schmerzintensität",
                    "answerOption": [
                        {"valueString": "freier Text"},
                        {"valueCoding": {"code": "mild", "display": "Leicht"}},
                    ],
                }
            ],
        }

        result = merge_questionnaire_language_variants([baseline, variant])

        assert result[0]["item"][0]["answerOption"][0] == {"valueString": "free text"}
        assert result[0]["item"][0]["answerOption"][1]["valueCoding"]["_display"]["extension"] == [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "de"},
                    {"url": "content", "valueString": "Leicht"},
                ],
            },
        ]

    def test_duplicate_answer_option_codes_use_last_display(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Pain level",
                    "answerOption": [
                        {
                            "valueCoding": {
                                "code": "mild",
                                "system": "http://example.org/a",
                                "display": "Mild A",
                            }
                        },
                        {
                            "valueCoding": {
                                "code": "mild",
                                "system": "http://example.org/b",
                                "display": "Mild B",
                            }
                        },
                    ],
                }
            ],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "demo.de",
            "url": "demo",
            "language": "de",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Schmerzintensität",
                    "answerOption": [
                        {"valueCoding": {"code": "mild", "display": "Leicht zuerst"}},
                        {"valueCoding": {"code": "mild", "display": "Leicht zuletzt"}},
                    ],
                }
            ],
        }

        result = merge_questionnaire_language_variants([baseline, variant])

        options = result[0]["item"][0]["answerOption"]
        assert options[0]["valueCoding"] == {
            "code": "mild",
            "system": "http://example.org/a",
            "display": "Mild A",
        }
        assert options[1]["valueCoding"]["_display"]["extension"] == [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "de"},
                    {"url": "content", "valueString": "Leicht zuletzt"},
                ],
            },
        ]

    def test_matches_answer_option_by_code_ignoring_system(self):
        baseline = {
            "resourceType": "Questionnaire",
            "id": "demo",
            "url": "demo",
            "language": "en",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Pain level",
                    "answerOption": [
                        {
                            "valueCoding": {
                                "code": "mild",
                                "system": "http://example.org/pain-level",
                                "display": "Mild",
                            }
                        },
                    ],
                }
            ],
        }
        variant = {
            "resourceType": "Questionnaire",
            "id": "demo.de",
            "url": "demo",
            "language": "de",
            "status": "active",
            "item": [
                {
                    "linkId": "pain-level",
                    "type": "choice",
                    "text": "Schmerzintensität",
                    "answerOption": [
                        {
                            "valueCoding": {
                                "code": "mild",
                                "system": "http://example.org/other-system",
                                "display": "Leicht",
                            }
                        },
                    ],
                }
            ],
        }

        result = merge_questionnaire_language_variants([baseline, variant])

        coding = result[0]["item"][0]["answerOption"][0]["valueCoding"]
        assert coding["system"] == "http://example.org/pain-level"
        assert coding["_display"]["extension"] == [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/translation",
                "extension": [
                    {"url": "lang", "valueCode": "de"},
                    {"url": "content", "valueString": "Leicht"},
                ],
            },
        ]

    def test_preserves_non_questionnaire_and_unrelated_questionnaires(self):
        patient = {"resourceType": "Patient", "id": "p1", "name": [{"family": "Doe"}]}
        other = {
            "resourceType": "Questionnaire",
            "id": "other",
            "url": "other",
            "status": "active",
            "title": "Other",
            "item": [{"linkId": "o1", "type": "string", "text": "Other Q"}],
        }

        result = merge_questionnaire_language_variants(
            [
                patient,
                copy.deepcopy(BASELINE),
                other,
                copy.deepcopy(VARIANT_DE_NESTED),
                copy.deepcopy(VARIANT_FR_FLAT),
            ]
        )

        assert len(result) == 3
        assert patient in result
        assert other in result
        assert MERGED_EN_DE_FR in result

    def test_does_not_mutate_input_resources(self):
        baseline = copy.deepcopy(BASELINE)
        variant_de = copy.deepcopy(VARIANT_DE_NESTED)
        variant_fr = copy.deepcopy(VARIANT_FR_FLAT)
        original_baseline = copy.deepcopy(baseline)
        original_de = copy.deepcopy(variant_de)
        original_fr = copy.deepcopy(variant_fr)

        merge_questionnaire_language_variants([baseline, variant_de, variant_fr])

        assert baseline == original_baseline
        assert variant_de == original_de
        assert variant_fr == original_fr

    def test_loads_and_merges_demo_resources_from_resources_dir(self):
        loaded = flatten_resources(load_resources(RESOURCES_DIR))
        demo_resources = [
            resource
            for resource in loaded
            if resource.get("resourceType") == "Questionnaire" and resource.get("url") == "demo-questionnaire"
        ]

        result = merge_questionnaire_language_variants(demo_resources)

        assert result == [MERGED_EN_DE_FR]
