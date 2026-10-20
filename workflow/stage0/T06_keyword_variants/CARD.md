# T06 — Keyword morphology and variants

Reader: worker agent. Human summary of this stage: `workflow/stage0/README.md`.

- **Stage:** 0 · **Worker:** OpenCode + Ollama `qwen3:8b` (local, no web) · **Fallback (after R2):** Codex
- **Time box:** 30 min · **Batches:** run batch 1 (`core`), save, then batch 2 (`site_context`). `topic` terms are not
  needed: they will be matched by lemma later.
- No web access needed. Text work only.

## Goal
Word forms and spelling variants of the site/actor terms so later queries and filters do not miss mentions.

## Inputs (read only these)
- `config/keywords.yaml` — sections `core` and `site_context` only

## Output
`out/variants.yaml`, one entry per input term:
```yaml
- term: "Электрозавод"
  section: core
  case_forms: ["Электрозавод", "Электрозавода", "Электрозаводу", "Электрозаводом", "Электрозаводе"]
  spelling_variants: ["электрозавод"]        # ё/е, hyphenation, letter case — only systematic variants
  proposed_variants: ["Электро-завод"]       # plausible but not confirmed in real texts; will be checked later
  hashtags: ["#электрозавод"]
  regex: "\\b[Ээ]лектрозавод(а|у|ом|е)?\\b"  # must NOT match Электрозаводская / Электрозаводск
  negative_examples: ["Электрозаводская", "Электрозаводск"]
  note: ""
```

## Acceptance criteria
- [ ] A1 every `core` and `site_context` term appears exactly once
- [ ] A2 singular case forms for nouns; multi-word terms inflected as phrases (the head word changes)
- [ ] A3 ё/е variants where relevant (e.g. Семёновская / Семеновская)
- [ ] A4 each regex is meant to match all `case_forms` and none of `negative_examples` (reviewers test this with a script)
- [ ] A5 valid YAML

## Rules quoted for this card
- Do not invent new terms; only inflect and vary the given ones. Mark anything unsure as `proposed_variants`.
- Write only inside `workflow/stage0/T06_keyword_variants/` (and your BOARD row).
