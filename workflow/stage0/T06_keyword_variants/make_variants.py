"""Generate and check the T06 keyword forms using only local inputs."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from itertools import product
from pathlib import Path
import re

import pymorphy3
import yaml


CARD_DIR = Path(__file__).resolve().parent
REPO_ROOT = CARD_DIR.parents[2]
SECTIONS = ("core", "site_context", "exclude")
CASES = ("nomn", "gent", "datv", "accs", "ablt", "loct")
FIELDS = (
    "term", "section", "case_forms", "spelling_variants",
    "proposed_variants", "hashtags", "regex", "negative_examples", "note",
)
SITE_NEGATIVES = (
    "Электрозаводская", "Электрозаводской",
    "Электрозаводск", "электрозаводский",
)


@dataclass(frozen=True)
class Phrase:
    head: int | None
    adjective: int | None = None
    gender: str | None = None
    pos: str = "NOUN"
    quoted_name: int | None = None
    mode: str = "phrase"
    note: str = ""
    proposed: tuple[str, ...] = ()
    negatives: tuple[str, ...] = ()


SPECS = {
    "Электрозавод": Phrase(
        0, negatives=("электрозаводы", "электрозаводов", "электрозаводами"),
        note="Совпадения с одноимёнными предприятиями и нарицательным словом "
        "неразличимы по написанию; нужен контекст московской площадки.",
    ),
    "Московский электрозавод": Phrase(
        1, 0,
        note="У прилагательного вручную задано согласование с неодушевлённым "
        "существительным: винительный падеж «Московский электрозавод», "
        "а не «Московского электрозавод».",
        negatives=("Московская электрозавод", "Московского электрозавод"),
    ),
    "МЭЛЗ": Phrase(
        None, mode="melz",
        note="Ручное исправление: pymorphy3 разбирает МЭЛЗ как форму женского "
        "имени «мэлза». Здесь заданы формы звуковой аббревиатуры мужского рода "
        "с окончаниями -а, -у, -ом, -е; исходное МЭЛЗ покрывает и несклоняемое "
        "употребление. Это языковая модель, употребление на площадке не проверено.",
        negatives=("МЭЛЗы", "МЭЛЗов", "МЭЛЗами", "МЭЛЗация"),
    ),
    "территория Электрозавода": Phrase(
        0,
        note="Склоняется «территория»; зависимое «Электрозавода» остаётся "
        "в родительном падеже.",
        negatives=("территория Электрозавод", "территории Электрозаводу"),
    ),
    "редевелопмент Электрозавода": Phrase(
        0,
        note="Склоняется «редевелопмент»; зависимое «Электрозавода» остаётся "
        "в родительном падеже. Написание через дефис оставлено кандидатом.",
        proposed=("ре-девелопмент Электрозавода",),
        negatives=("редевелопмент Электрозавод", "редевелопмента Электрозаводу"),
    ),
    "Эталон Электрозавод": Phrase(
        None, mode="pair",
        note="Исходная строка содержит два поисковых слова без синтаксической "
        "связи. case_forms перечисляет сочетания их независимых падежных форм, "
        "а не падежи единой фразы. Выражение требует этот порядок и соседство "
        "слов; для свободного текста рекомендуется отдельное условие "
        "совместного упоминания «Эталона» и площадки.",
        negatives=("Эталонный Электрозавод", "Эталон Электрозаводы"),
    ),
    "#электрозавод": Phrase(
        None, mode="hashtag",
        note="Хештег не склоняется. Поле hashtags повторяет исходный термин "
        "и не подтверждает его употребление.",
        negatives=("#электрозавода", "#электрозавод_москва", "##электрозавод"),
    ),
    "#сохранитьэлектрозавод": Phrase(
        None, mode="hashtag",
        note="Входной файл помечает этот хештег как гипотетический. Он сохранён "
        "для покрытия входных терминов; case_forms и hashtags не доказывают "
        "его существования. Проверить на пилоте этапа 1; до проверки не "
        "считать наблюдаемым обозначением кампании. Хештег не склоняется.",
        negatives=(
            "#сохранитьэлектрозавода", "#сохранитьэлектрозавод_москва",
            "##сохранитьэлектрозавод",
        ),
    ),
    "Электрозаводская": Phrase(
        0, pos="ADJF", gender="femn",
        note="Выбрано прилагательное женского рода. Здесь «Электрозаводская» "
        "и «Электрозаводской» являются положительными формами; требование "
        "отклонять их применено к выражениям для существительного "
        "«Электрозавод». Тип объекта по этому слову определить нельзя.",
        negatives=("Электрозаводск", "электрозаводский", "Электрозаводские",
                   "Электрозавод", "Электрозаводов"),
    ),
    "Преображенская": Phrase(
        0, pos="ADJF", gender="femn",
        note="Выбрано прилагательное женского рода. Название, фамилия и "
        "обычное прилагательное по написанию могут совпадать.",
        negatives=("Преображенский", "Преображенское", "Преображенские"),
    ),
    "Преображенское": Phrase(
        0, gender="neut",
        note="Вручную выбран разбор географического названия среднего рода "
        "вместо первого разбора прилагательного. Совпадающие формы других "
        "названий требуют проверки контекста.",
        negatives=("Преображенская", "Преображенский", "Преображенские"),
    ),
    "Соколиная Гора": Phrase(
        1, 0,
        note="Склоняются оба слова с согласованием в женском роде. "
        "Для творительного падежа включены сочетания окончаний -ой и -ою. "
        "Дефисное написание оставлено кандидатом.",
        proposed=("Соколиная-Гора",),
        negatives=("Соколиная Горы", "Соколиной Гора", "Соколиная Горка"),
    ),
    "Семёновская": Phrase(
        0, pos="ADJF", gender="femn",
        note="Вручную выбран разбор прилагательного женского рода, "
        "а не фамилии. Для каждой формы приняты ё/е. Одноимённые объекты "
        "и фамилия требуют проверки контекста.",
        negatives=("Семёновский", "Семеновское", "Семёновские"),
    ),
    "Яуза": Phrase(
        0,
        note="Выбран разбор географического названия. Другие объекты "
        "с тем же названием по одному слову не отделяются.",
        negatives=("Яузский", "Яузская", "Яузский район"),
    ),
    "Эталон": Phrase(
        0,
        note="Название компании и нарицательное «эталон» неразличимы "
        "по этому выражению. Во входном файле задано условие совместного "
        "упоминания с терминами площадки; его нужно сохранить.",
        negatives=("эталонный", "эталонность", "эталоны", "эталонов"),
    ),
    "Группа Эталон": Phrase(
        0, quoted_name=1,
        note="Склоняется «Группа»; название «Эталон» после родового слова "
        "вручную оставлено в исходной форме. Выражение также принимает "
        "парные кавычки «…» и ASCII вокруг названия.",
        negatives=("Группа Эталона", "Группы Эталону", "Группа Эталонный"),
    ),
    "ГК Эталон": Phrase(
        None, quoted_name=1, mode="fixed",
        note="Ручное правило: аббревиатура «ГК» (группа компаний) и следующее "
        "название «Эталон» остаются неизменными. Выражение также принимает "
        "парные кавычки «…» и ASCII вокруг названия.",
        negatives=("ГК Эталона", "ГК Эталону", "ГК Эталонный", "ГКЭталон"),
    ),
    "станция метро Электрозаводская": Phrase(
        0, quoted_name=2,
        note="Склоняется «станция». «Метро» и название станции вручную "
        "оставлены неизменными; название дано как приложение. Выражение "
        "также принимает парные кавычки «…» и ASCII вокруг названия.",
        negatives=("станция метро Электрозаводской",
                   "станция метро Электрозаводские"),
    ),
    "Электрозаводская линия": Phrase(
        1, 0,
        note="Оба слова согласованы в женском роде. Во входном файле "
        "употребление этой фразы оставлено на проверку; формы не подтверждают "
        "существование транспортного названия.",
        negatives=("Электрозаводская линии", "Электрозаводской линия",
                   "Электрозаводские линии"),
    ),
    "закрытие станции": Phrase(
        0,
        note="Склоняется «закрытие»; зависимое «станции» остаётся "
        "в родительном падеже единственного числа. Ручное ограничение: "
        "сокращённое словарное «закрытьем» исключено из основного набора; "
        "используется «закрытием».",
        negatives=("открытие станции", "закрытие станций", "закрытие станция"),
    ),
    "ДТП": Phrase(
        None, mode="fixed",
        note="ДТП (дорожно-транспортное происшествие) не склоняется.",
        negatives=("ДТПшный", "ДТПшник", "ДТП2026"),
    ),
    "вакансия": Phrase(
        0,
        note="«Вакансии» совпадает с формой множественного числа; регулярное "
        "выражение не определяет число и падеж в тексте.",
        negatives=("вакансий", "вакансиями", "вакансионный"),
    ),
}

# Independent grammar checks: six main cases in CASES order, not regex output.
EXPECTED = {
    "Электрозавод": "Электрозавод|Электрозавода|Электрозаводу|Электрозавод|Электрозаводом|Электрозаводе",
    "Московский электрозавод": "Московский электрозавод|Московского электрозавода|Московскому электрозаводу|Московский электрозавод|Московским электрозаводом|Московском электрозаводе",
    "МЭЛЗ": "МЭЛЗ|МЭЛЗа|МЭЛЗу|МЭЛЗ|МЭЛЗом|МЭЛЗе",
    "территория Электрозавода": "территория Электрозавода|территории Электрозавода|территории Электрозавода|территорию Электрозавода|территорией Электрозавода|территории Электрозавода",
    "редевелопмент Электрозавода": "редевелопмент Электрозавода|редевелопмента Электрозавода|редевелопменту Электрозавода|редевелопмент Электрозавода|редевелопментом Электрозавода|редевелопменте Электрозавода",
    "Электрозаводская": "Электрозаводская|Электрозаводской|Электрозаводской|Электрозаводскую|Электрозаводской|Электрозаводской",
    "Преображенская": "Преображенская|Преображенской|Преображенской|Преображенскую|Преображенской|Преображенской",
    "Преображенское": "Преображенское|Преображенского|Преображенскому|Преображенское|Преображенским|Преображенском",
    "Соколиная Гора": "Соколиная Гора|Соколиной Горы|Соколиной Горе|Соколиную Гору|Соколиной Горой|Соколиной Горе",
    "Семёновская": "Семёновская|Семёновской|Семёновской|Семёновскую|Семёновской|Семёновской",
    "Яуза": "Яуза|Яузы|Яузе|Яузу|Яузой|Яузе",
    "Эталон": "Эталон|Эталона|Эталону|Эталон|Эталоном|Эталоне",
    "Группа Эталон": "Группа Эталон|Группы Эталон|Группе Эталон|Группу Эталон|Группой Эталон|Группе Эталон",
    "станция метро Электрозаводская": "станция метро Электрозаводская|станции метро Электрозаводская|станции метро Электрозаводская|станцию метро Электрозаводская|станцией метро Электрозаводская|станции метро Электрозаводская",
    "Электрозаводская линия": "Электрозаводская линия|Электрозаводской линии|Электрозаводской линии|Электрозаводскую линию|Электрозаводской линией|Электрозаводской линии",
    "закрытие станции": "закрытие станции|закрытия станции|закрытию станции|закрытие станции|закрытием станции|закрытии станции",
    "вакансия": "вакансия|вакансии|вакансии|вакансию|вакансией|вакансии",
}


def unique(values):
    return list(dict.fromkeys(values))


def restore_case(word, original):
    if original.isupper():
        return word.upper()
    if original[0].isupper():
        return word[0].upper() + word[1:]
    return word


def select_parse(morph, word, pos, gender=None):
    candidates = [
        p for p in morph.parse(word)
        if p.tag.POS == pos and p.tag.case == "nomn"
        and p.tag.number == "sing" and p.tag.animacy != "anim"
        and (gender is None or p.tag.gender == gender)
    ]
    if not candidates:
        raise ValueError(f"Нет подходящего разбора: {word}, {pos}, {gender}")
    return candidates[0]


def word_forms(parse, original, case, gender=None, adjective=False):
    grammemes = {"sing", case}
    if adjective:
        grammemes.add(gender)
        if case == "accs" and gender == "masc":
            grammemes.add("inan")
    inflected = parse.inflect(grammemes)
    if inflected is None:
        raise ValueError(f"Нет формы: {original}, {case}")
    forms = [restore_case(inflected.word, original)]
    if case == "ablt":
        # Include long feminine endings, not every dictionary alternative.
        forms += [
            restore_case(p.word, original)
            for p in parse.lexeme
            if p.tag.case == case and p.tag.number == "sing"
            and p.tag.gender == (gender or parse.tag.gender)
            and ("V-oy" in p.tag or "V-ey" in p.tag)
        ]
    return unique(forms)


def inflect_phrase(morph, term, spec):
    words = term.split()
    head = select_parse(morph, words[spec.head], spec.pos, spec.gender)
    adjective = (
        select_parse(morph, words[spec.adjective], "ADJF", head.tag.gender)
        if spec.adjective is not None else None
    )
    by_case = {}
    for case in CASES:
        options = [[word] for word in words]
        options[spec.head] = word_forms(
            head, words[spec.head], case, head.tag.gender, spec.pos == "ADJF",
        )
        if adjective is not None:
            options[spec.adjective] = word_forms(
                adjective, words[spec.adjective], case, head.tag.gender, True,
            )
        by_case[case] = [" ".join(parts) for parts in product(*options)]
    return by_case


def make_forms(morph, term, spec):
    if spec.mode in ("fixed", "hashtag"):
        by_case = {case: [term] for case in CASES}
    elif spec.mode == "melz":
        by_case = {
            case: ["МЭЛЗ" + ending]
            for case, ending in zip(CASES, ("", "а", "у", "", "ом", "е"))
        }
    elif spec.mode == "pair":
        left = inflect_phrase(morph, "Эталон", SPECS["Эталон"])
        right = inflect_phrase(morph, "Электрозавод", SPECS["Электрозавод"])
        forms = [
            f"{a} {b}"
            for a, b in product(
                unique(x for forms in left.values() for x in forms),
                unique(x for forms in right.values() for x in forms),
            )
        ]
        return forms, {}
    else:
        by_case = inflect_phrase(morph, term, spec)
    return unique(form for forms in by_case.values() for form in forms), by_case


def make_spellings(forms):
    variants = []
    for form in forms:
        for spelling in unique((form, form.replace("ё", "е").replace("Ё", "Е"))):
            variants.extend((
                spelling, spelling.lower(), spelling.upper(),
                spelling[0].upper() + spelling[1:],
            ))
    return [variant for variant in unique(variants) if variant not in forms]


def token_pattern(token):
    result = []
    for char in token:
        if char.lower() == "ё":
            result.append("[ЕеЁё]")
        elif char.lower() != char.upper():
            result.append(f"[{char.upper()}{char.lower()}]")
        else:
            result.append(re.escape(char))
    return "".join(result)


def make_regex(forms, spec):
    alternatives = []
    for form in forms:
        words = form.split()
        tokens = [token_pattern(word) for word in words]
        start = r"(?<![\w#])" if form.startswith("#") else r"\b"
        if spec.quoted_name is None:
            body = r"\s+".join(tokens) + r"\b"
        else:
            before = r"\s+".join(tokens[:spec.quoted_name])
            name = r"\s+".join(tokens[spec.quoted_name:]) + r"\b"
            body = before + r'\s+(?:' + name + "|«" + name + '»|"' + name + r'")(?!\w)'
        alternatives.append(start + body)
    return "(?:" + "|".join(unique(alternatives)) + ")"


def make_negatives(term, spec):
    negatives = list(spec.negatives)
    if "электрозавод" in term.lower() and term != "Электрозаводская":
        negatives.extend(SITE_NEGATIVES)
        # Also reject the look-alike inside each noun phrase or hashtag.
        if "Электрозаводская" not in term:
            for lookalike in SITE_NEGATIVES:
                negatives.append(re.sub(
                    r"электрозавод(?:а)?", lookalike, term, flags=re.IGNORECASE,
                ))
    negatives.extend(("пред" + term, term + "ский", term + "_1", term + "2026"))
    return unique(negatives)


def make_entry(morph, section, term):
    spec = SPECS[term]
    forms, by_case = make_forms(morph, term, spec)
    note = "inference: " + spec.note
    note += " Формы получены локально; употребление в публикациях не проверялось."
    if spec.mode == "phrase":
        note += " Совпадающие падежные формы записаны один раз."
    if section == "site_context":
        note += " Применять с тематическим условием из входного файла."
    if section == "exclude":
        note += " Применять исключение только при отсутствии совпадения core."
    return {
        "term": term,
        "section": section,
        "case_forms": forms,
        "spelling_variants": make_spellings(forms),
        "proposed_variants": list(spec.proposed),
        "hashtags": [term] if spec.mode == "hashtag" else [],
        "regex": make_regex(forms, spec),
        "negative_examples": make_negatives(term, spec),
        "note": note,
    }, by_case


def test_entries(entries, paradigms, input_terms):
    errors = []
    expected_pairs = [(section, term) for section, term in input_terms]
    actual_pairs = [(entry["section"], entry["term"]) for entry in entries]
    if Counter(actual_pairs) != Counter(expected_pairs):
        errors.append("Состав выходных строк не совпадает с входными терминами.")
    if len(set(term for _, term in input_terms)) != len(input_terms):
        errors.append("Во входных секциях есть повторяющийся термин.")
    lines = [
        "T06: локальные проверки форм и регулярных выражений",
        "Набор: core, site_context, exclude; публикации не проверялись.",
        "re.compile без IGNORECASE и ASCII; регистр задан классами букв.",
    ]
    total_forms = total_negatives = total_extra = 0
    for entry in entries:
        term = entry["term"]
        spec = SPECS[term]
        local = []
        if tuple(entry) != FIELDS:
            local.append("Неверная схема строки.")
        for field in FIELDS:
            if field not in ("term", "section", "regex", "note"):
                values = entry[field]
                if not isinstance(values, list) or not all(isinstance(x, str) for x in values):
                    local.append(f"Неверный тип: {field}.")
                elif len(unique(values)) != len(values):
                    local.append(f"Повтор внутри {field}.")
        regex = re.compile(entry["regex"])
        positive = entry["case_forms"] + entry["spelling_variants"]
        matched = sum(regex.fullmatch(value) is not None for value in positive)
        rejected = sum(regex.search(value) is None for value in entry["negative_examples"])
        for value in positive:
            if not regex.fullmatch(value):
                local.append(f"Не совпала форма: {value!r}")
        for value in entry["negative_examples"]:
            if regex.search(value):
                local.append(f"Совпал отрицательный пример: {value!r}")
        if term not in entry["case_forms"]:
            local.append("Нет исходного термина.")
        if term in EXPECTED:
            actual = [paradigms[term][case][0] for case in CASES]
            if actual != EXPECTED[term].split("|"):
                local.append(f"Неверные основные падежные формы: {actual!r}")
        if spec.mode in ("fixed", "hashtag") and entry["case_forms"] != [term]:
            local.append("Изменён несклоняемый термин или хештег.")
        if spec.mode == "pair" and len(entry["case_forms"]) != 25:
            local.append("Неполный набор независимых сочетаний двух слов.")
        extra = 0
        for form in positive:
            # Exercise Cyrillic boundaries in running text, not just fullmatch.
            mixed_case = "".join(
                char.upper() if index % 2 else char.lower()
                for index, char in enumerate(form)
            )
            for context in (f"({form}),", f"текст: {form}; далее", mixed_case,
                            form.replace(" ", "\u00a0"), form.replace(" ", "\n")):
                extra += 1
                if not regex.search(context):
                    local.append(f"Не совпал контекст: {context!r}")
            for context in ("я" + form, "a" + form, "1" + form, "_" + form,
                            form + "я", form + "a", form + "1", form + "_"):
                extra += 1
                if regex.search(context):
                    local.append(f"Нарушена граница слова: {context!r}")
            if spec.quoted_name is not None:
                words = form.split()
                before = " ".join(words[:spec.quoted_name]) + " "
                name = " ".join(words[spec.quoted_name:])
                for left, right in (("«", "»"), ('"', '"')):
                    quoted = before + left + name + right
                    extra += 1
                    if not regex.fullmatch(quoted):
                        local.append(f"Не совпали парные кавычки: {quoted!r}")
                for left, right in (("«", ""), ("", "»"), ('"', ""),
                                    ("«", '"'), ("", '"')):
                    extra += 1
                    if regex.fullmatch(before + left + name + right):
                        local.append("Приняты непарные кавычки при fullmatch.")
        for candidate in entry["proposed_variants"]:
            extra += 1
            if regex.search(candidate):
                local.append(f"Непроверенный кандидат попал в выражение: {candidate!r}")
        if "ё" in term.lower():
            for form in entry["case_forms"]:
                for variant in (form.replace("ё", "е"), form.upper().replace("Ё", "Е")):
                    extra += 1
                    if not regex.fullmatch(variant):
                        local.append(f"Не покрыт вариант ё/е: {variant!r}")
        total_forms += len(positive)
        total_negatives += len(entry["negative_examples"])
        total_extra += extra
        status = "FAIL" if local else "PASS"
        lines.append(
            f"{status} | {entry['section']} | {term} | "
            f"формы {matched}/{len(positive)} "
            f"(падежные {len(entry['case_forms'])}, написания {len(entry['spelling_variants'])})"
            f" | отрицательные {rejected}/{len(entry['negative_examples'])}"
            f" | дополнительные проверки {extra}"
        )
        errors.extend(f"{term}: {error}" for error in local)
    lines.append(
        f"ИТОГ: {'FAIL' if errors else 'PASS'}; терминов {len(entries)}/{len(input_terms)}; "
        f"форм {total_forms}; отрицательных примеров {total_negatives}; "
        f"дополнительных проверок {total_extra}; ошибок {len(errors)}."
    )
    lines.extend("ОШИБКА: " + error for error in errors)
    lines.append(
        "Ограничение: тесты проверяют написание и границы слов; "
        "географию, смысл и употребление в публикациях они не проверяют."
    )
    return "\n".join(lines) + "\n", errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    source = yaml.safe_load((REPO_ROOT / "config/keywords.yaml").read_text(encoding="utf-8"))
    input_terms = [(section, term) for section in SECTIONS for term in source[section]]
    if set(term for _, term in input_terms) != set(SPECS):
        raise ValueError("Входные термины изменились: нужно проверить правила склонения.")
    morph = pymorphy3.MorphAnalyzer()
    entries = []
    paradigms = {}
    for section, term in input_terms:
        entry, paradigm = make_entry(morph, section, term)
        entries.append(entry)
        paradigms[term] = paradigm
    serialized = yaml.safe_dump(entries, allow_unicode=True, sort_keys=False, width=110)
    # Test what the reviewer will load from YAML, including escaped regexes.
    report, errors = test_entries(yaml.safe_load(serialized), paradigms, input_terms)
    output = CARD_DIR / "out"
    output.mkdir(exist_ok=True)
    (output / "variants.yaml").write_text(serialized, encoding="utf-8")
    (output / "test_report.txt").write_text(report, encoding="utf-8")
    print(report, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
