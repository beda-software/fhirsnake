import copy
import logging
from collections import defaultdict

TRANSLATION_URL = "http://hl7.org/fhir/StructureDefinition/translation"
DEFAULT_BASELINE_LANGUAGE = "en"
ROOT_TRANSLATABLE_FIELDS = ("title", "description")


def merge_questionnaire_language_variants(resources_list: list[dict]) -> list[dict]:
    """Merge Questionnaire resources that share the same url (fallback: id) but differ by language.

    Non-Questionnaire resources and single-questionnaire groups pass through unchanged.
    Multiple language variants are combined into one baseline resource with FHIR translation
    extensions on item.text, item.answerOption[].valueCoding.display, title, and description.
    """
    groups: dict[str, list[dict]] = defaultdict(list)
    non_questionnaires: list[dict] = []
    for resource in resources_list:
        if resource.get("resourceType") != "Questionnaire":
            non_questionnaires.append(resource)
            continue
        groups[_group_key(resource)].append(resource)

    result = list(non_questionnaires)
    for key, questionnaires in groups.items():
        if len(questionnaires) == 1:
            result.append(questionnaires[0])
        else:
            result.append(_merge_group(key, questionnaires))
    return result


def _group_key(resource: dict) -> str:
    return resource.get("url") or resource["id"]


def questionnaire_group_key(resource: dict) -> str:
    """Return the key used to group Questionnaire language variants (url, else id)."""
    return _group_key(resource)


def _is_baseline_language(language: str | None) -> bool:
    return language is None or language == DEFAULT_BASELINE_LANGUAGE


def _merge_group(key: str, questionnaires: list[dict]) -> dict:
    baselines = [q for q in questionnaires if _is_baseline_language(q.get("language"))]
    if not baselines:
        raise ValueError(
            f"No baseline Questionnaire found for '{key}' "
            f"(expected language missing or '{DEFAULT_BASELINE_LANGUAGE}')"
        )
    if len(baselines) > 1:
        raise ValueError(
            f"Multiple baseline Questionnaires found for '{key}' "
            f"(language missing or '{DEFAULT_BASELINE_LANGUAGE}')"
        )

    baseline = copy.deepcopy(baselines[0])
    baseline.setdefault("language", DEFAULT_BASELINE_LANGUAGE)

    variants = [q for q in questionnaires if q is not baselines[0]]
    seen_languages: set[str] = set()
    prepared: list[tuple[str, dict]] = []
    for variant in variants:
        language = variant.get("language")
        if not language:
            raise ValueError(f"Questionnaire language variant for '{key}' is missing 'language'")
        if _is_baseline_language(language):
            raise ValueError(f"Questionnaire language variant for '{key}' has baseline language '{language}'")
        if language in seen_languages:
            raise ValueError(f"Duplicate Questionnaire language '{language}' for '{key}'")
        seen_languages.add(language)
        prepared.append((language, variant))

    for language, variant in sorted(prepared, key=lambda item: item[0]):
        _apply_variant(baseline, variant, language, key)

    return baseline


def _apply_variant(baseline: dict, variant: dict, language: str, key: str) -> None:
    for field in ROOT_TRANSLATABLE_FIELDS:
        content = variant.get(field)
        if content is not None and field in baseline:
            _upsert_translation(baseline, field, language, content)

    translations_by_link_id = _collect_translations_by_link_id(variant.get("item", []), language, key)
    applied_link_ids = _apply_item_translations(baseline.get("item", []), translations_by_link_id, language, key)

    skipped = set(translations_by_link_id) - applied_link_ids
    for link_id in sorted(skipped):
        logging.warning(
            "Skipping translation for linkId '%s' in language '%s' for Questionnaire '%s': "
            "linkId not present in baseline",
            link_id,
            language,
            key,
        )


def _coding_key(coding: dict) -> str | None:
    return coding.get("code")


def _collect_translations_by_link_id(items: list[dict], language: str, key: str) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for item in items:
        link_id = item["linkId"]
        entry: dict = {}
        if "text" in item:
            entry["text"] = item["text"]

        answer_options: dict[str, str] = {}
        for option in item.get("answerOption", []):
            coding = option.get("valueCoding")
            if not coding:
                continue
            code = _coding_key(coding)
            if not code:
                logging.warning(
                    "Skipping answerOption without code in linkId '%s' in language '%s' "
                    "for Questionnaire '%s'",
                    link_id,
                    language,
                    key,
                )
                continue
            if "display" in coding:
                answer_options[code] = coding["display"]

        if answer_options:
            entry["answerOption"] = answer_options

        if entry:
            result[link_id] = entry

        result.update(_collect_translations_by_link_id(item.get("item", []), language, key))
    return result


def _apply_item_translations(
    items: list[dict],
    translations_by_link_id: dict[str, dict],
    language: str,
    key: str,
) -> set[str]:
    applied: set[str] = set()
    for item in items:
        link_id = item["linkId"]
        if link_id in translations_by_link_id:
            translations = translations_by_link_id[link_id]

            if "text" in translations:
                if "text" not in item:
                    raise ValueError(
                        f"Questionnaire '{key}' baseline item '{link_id}' is missing 'text'; "
                        f"add the origin text to the baseline resource before translating to '{language}'"
                    )
                _upsert_translation(item, "text", language, translations["text"])

            if "answerOption" in translations:
                _apply_answer_option_translations(item, translations["answerOption"], language, key, link_id)

            applied.add(link_id)
        applied.update(_apply_item_translations(item.get("item", []), translations_by_link_id, language, key))
    return applied


def _apply_answer_option_translations(
    item: dict,
    option_displays: dict[str, str],
    language: str,
    key: str,
    link_id: str,
) -> None:
    baseline_by_code: dict[str, dict] = {}
    for option in item.get("answerOption", []):
        coding = option.get("valueCoding")
        if not coding:
            continue
        code = _coding_key(coding)
        if code:
            baseline_by_code[code] = coding

    for code, display in option_displays.items():
        coding = baseline_by_code.get(code)
        if coding is None:
            raise ValueError(
                f"Questionnaire '{key}' baseline item '{link_id}' has no answerOption with code '{code}'; "
                f"add the origin option to the baseline resource before translating to '{language}'"
            )
        if "display" not in coding:
            raise ValueError(
                f"Questionnaire '{key}' baseline item '{link_id}' answerOption '{code}' is missing 'display'; "
                f"add the origin display to the baseline resource before translating to '{language}'"
            )
        _upsert_translation(coding, "display", language, display)


def _upsert_translation(node: dict, field: str, language: str, content: str) -> None:
    # http://hl7.org/fhir/StructureDefinition/translation always has extension: [lang, content]
    element_key = f"_{field}"
    element = node.setdefault(element_key, {})
    extensions = element.setdefault("extension", [])

    for extension in extensions:
        if extension.get("url") != TRANSLATION_URL:
            continue
        nested = extension["extension"]
        lang = next(e["valueCode"] for e in nested if e["url"] == "lang")
        if lang == language:
            content_ext = next(e for e in nested if e["url"] == "content")
            content_ext["valueString"] = content
            return

    extensions.append(
        {
            "url": TRANSLATION_URL,
            "extension": [
                {"url": "lang", "valueCode": language},
                {"url": "content", "valueString": content},
            ],
        }
    )
