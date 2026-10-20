# Prompts for Codex (planning and fact checks)

Run in the repository root, e.g. `codex exec "<prompt>"` or interactively.

## Plan critique (once per stage, after Claude drafts the cards)
Read `AGENTS.md`, `workflow/README.md`, `workflow/BOARD.md` and every `CARD.md` of stage <N>.
Critique the plan, do not rewrite it. Write `workflow/stage<N>/PLAN_CRITIQUE.md` (≤ 60 lines) with:
(1) gaps: what later stages or the 5 grading criteria in the brief will need that no card produces;
(2) cards that are too big for their worker, ambiguous, or whose acceptance criteria cannot be checked;
(3) a better assignment of cards to workers, if any; (4) what you would do differently, as numbered,
concrete proposals. Do not edit cards; Claude settles the plan.

## Review round <n>: facts and format
Card: `<CARD>`. Read `<CARD>/CARD.md`, `<CARD>/HANDOFF.md`, `<CARD>/out/*`, and for R2 `<CARD>/REVIEW_R1.md`.
Copy `workflow/templates/REVIEW.md` to `<CARD>/REVIEW_R<n>.md` and fill only the "Facts and format" part:
run the script checks on the whole files, check every acceptance criterion, open the links of every important-fact
row and of a random 20% of the other rows (rules in `workflow/README.md` §2, "How much to check"); an invented or
wrong row fails the criterion. In round 2 check the fix-list items and whatever they affect.
Propose fix items (numbered, atomic) under the fix list. Leave the "Content" part and the verdict to Claude.
Do not edit outputs. Then set the card's state in `workflow/BOARD.md` to `review_R<n>` and note "facts checked" in its row.
