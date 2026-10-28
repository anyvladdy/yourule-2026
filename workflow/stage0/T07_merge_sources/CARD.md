# T07 — Merge discovered sources into the registry format

Reader: worker agent. Human summary of this stage: `workflow/stage0/README.md`.

- **Stage:** 0 (wave 2) · **Worker:** OpenCode + Ollama `gemma4` (local, no web) · **Fallback (after R2):** Codex
- **Status: DRAFT — not ready.** Planners finalise this card when T01, T02, T03, T08 are accepted, adding:
  1. an explicit column → field mapping per input file, with allowed nulls (fields absent in inputs stay null);
  2. source vs evidence: a channel/outlet/group is a source; a post/article/document is evidence attached to it;
  3. id rules (`tg_`, `vk_`, `pet_`, `vid_`, `med_`, `off_`, `dev_` + slug) and collision handling with existing ids;
  4. `verified` means "URL opened by a web worker in an accepted card", copied from inputs, never set by this card;
  5. one input file per batch (local model context);
  6. a disposition count per input row: added | updated_seed | merged_duplicate | rejected (+ reason).
- Mechanical checks (valid YAML, unique ids, counts) are done by reviewers with a script, not by the model.

## Goal
Convert accepted discovery outputs into entries for `config/sources.yaml` without adding or changing information.
