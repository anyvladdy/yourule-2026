# Worker launch prompt (dsh, Gemini/agy, OpenCode)

Reader: the person starting a worker, and the worker. Goal: start one card correctly.

Paste this with `<CARD>` replaced by the card folder, e.g. `workflow/stage0/T04_timeline_reality`.
Start the agent in the repository root.

---

You are a worker on this project. Read, in this order and nothing else unless the card lists it:
1. `AGENTS.md` section 0 (core rules)
2. `workflow/PROTOCOL.md` sections 1–3
3. `<CARD>/CARD.md`

Then do the card. Write only inside `<CARD>/`: outputs to `out/`, and finish with `HANDOFF.md`
using `workflow/templates/HANDOFF.md` (≤ 30 lines, tick the acceptance criteria honestly).
Set your row in `workflow/BOARD.md` to `in_progress` when you start and `review_R1` when you finish.
If a `REVIEW_R1.md` exists in the card folder, this is round 2: fix only the numbered items in its fix list,
append a "For R2" section to `HANDOFF.md`, and set the state to `review_R2`.
Do not write parsers or scrapers, and do not bulk-download anything. Never invent sources, numbers or quotes:
"not found" with the queries you tried is a valid result. Respect the card's time box.

---

## Per-agent notes
- **dsh:** default settings; web search allowed. Run T04 → T01 → T08 (T08 only after T04's R1 review).
- **Gemini (agy):** run in the repo root, e.g. `agy -i "<prompt above>"` (sign in first by launching `agy` once).
  Run T02 → T03 → T05.
- **OpenCode + Ollama:** start `ollama serve`; in OpenCode select the model named in the card
  (T06: `qwen3:8b`, T07: `gemma4`). Load one local model at a time (24 GB RAM). These cards need no web.
  If the model struggles with file tools, paste the input file content into the chat and save the answer
  into `out/` yourself.
