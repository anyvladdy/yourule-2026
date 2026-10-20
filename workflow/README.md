# How the work is organised

Every agent reads section 0 of `AGENTS.md`, then this file, then only its own task card and the files the card lists.
For a shorter overview, see the main `README.md`.

## 1. Roles

| Role | Who | What they do | What they do not do |
|------|-----|--------------|---------------------|
| Planners | Claude and Codex | Write the task cards for a stage and settle disagreements | Do the tasks themselves in the first two rounds |
| Workers | dsh (DeepSeek), Gemini (Antigravity `agy`), OpenCode with local models (qwen3:8b, gemma4, gemma3:4b) | Do one card: save results in `out/`, write `HANDOFF.md`, update their own row in `BOARD.md` | Edit anything else |
| Reviewers | Claude and Codex | Review each finished card and write `REVIEW_R1.md` or `REVIEW_R2.md` | Rewrite the worker's results in rounds 1 and 2 (they list fixes instead) |

After review, Claude moves accepted results into `config/`, `docs/` (including `docs/sources.md`) and
`deliverables/`, keeping card and row IDs so every item can be traced back. Codex runs the mechanical checks
with scripts: whether the files open, whether IDs are unique, row counts, regular-expression tests.

Which worker gets which card:

| Worker | Strengths | Typical cards |
|--------|-----------|---------------|
| dsh | Reasoning, web research, long tasks, low cost | Checking facts, timelines, official documents, similar cases, analysis scripts later |
| Gemini | Long documents, Google search, good Russian | Media and stakeholder searches, reading long documents, Russian drafts later |
| OpenCode with local models | Free and private, but no internet and a short memory | Word forms, reformatting lists, labelling small batches, counting characters, translating short texts |

The computer has 24 GB of memory, so run one local model at a time (gemma4 takes about 9.6 GB, qwen3:8b about 5 GB).
Give local models tasks whose input fits in one short file and needs no web access.

## 2. How a card moves

```
Plan:    Claude drafts the cards; Codex critiques them once; Claude decides
Round 1: the worker does the card; Codex and Claude review it
         accepted: Claude moves the results into the project files
         not accepted: the review lists numbered fixes
Round 2: the worker fixes only those items; they are reviewed again
         accepted: results moved into the project files
         still wrong: Claude or Codex finishes the failing items
Stage done: when every card is accepted, Claude and Codex write a summary of up to 20 lines in BOARD.md
```

- The board counts rounds for each card. After two failed rounds there is no third worker round.
  Only the failing items go to Claude or Codex, not the whole card.
- In round 2 the work centres on the listed fixes. Anyone who notices a new serious error still reports it,
  and reviewers re-check anything a fix affects (IDs, counts, conclusions based on a corrected row).
- Cards within a stage can run at the same time. A card from the next wave can start as soon as its inputs are accepted.

### Two kinds of review
Codex checks the facts and the format: does the card's checklist pass, do the links open and say what the row
claims, is anything invented or duplicated. Claude checks the content: what is missing, whether the result helps
the report score on the five criteria, whether the sources lean one way, and what later stages will need.
Claude reads Codex's review first and does not repeat its checks. Either of them can point out anything serious.

### How much to check
- Important facts are checked in full: heritage status, what will be kept or demolished, official decisions,
  dates used in the plan, and any number that will appear in the report. In stage 0 that means rows C01–C08
  in T04 and everything in T08.
- For the other rows, check a random 20% of each file (at least 5 and at most 15 rows, never more than the file has),
  spread across types of source. List which rows were checked.
- If a checked row is invented or seriously wrong, the fix is "re-check every row in this file".
  If the problem is only formatting, fix those rows.
- The worker's own checklist helps reviewers decide where to start, but it does not replace checking the important rows.
- Simple checks (does the file open, row counts, duplicates) run on the whole file every round, using a script.

## 3. Files

```
workflow/
  README.md          this file
  BOARD.md           one row per card: who has it, which round, status; stage summaries
  prompts/           text to paste when starting each agent
  templates/         CARD.md, HANDOFF.md, REVIEW.md
  stage<N>/T<NN>_<name>/
      CARD.md        written by the planners; not changed once work starts (changes are noted in the review)
      out/           the worker's results (tables or YAML)
      HANDOFF.md     the worker's note, up to 30 lines
      REVIEW_R1.md   first review (both reviewers in one file)
      REVIEW_R2.md   second review
```

Card status on the board: `ready`, `in_progress`, `review_R1`, `fix_R2`, `review_R2`, `accepted`, `integrated`,
or `escalated`. The worker sets `in_progress` and `review_R1` (or `review_R2`); the reviewers set the rest.

## 4. Saving effort without lowering quality

1. Agents read only what their card lists. Each card repeats the rules that matter for it.
2. Results are tables with fixed columns, not prose. They are quicker to write, check and combine.
3. Handoff notes are short: what was done, what changed from the card, what is uncertain, and the checklist.
4. The worker ticks the checklist before handing over, so reviewers know where to look first.
5. The two reviewers check different things, and they check samples rather than every row (except important facts).
6. Fixes are numbered and small, so round 2 touches only what needs it.
7. Prompts point to file paths instead of pasting file contents. A local model that cannot read files gets one short input file.
8. Simple work goes to the free local models. The stronger models plan and review.
9. Codex critiques each plan once. A second pass happens only if Claude and Codex disagree on something important.
10. The stage summary lists accepted results, IDs, open questions and decisions. The next stage reads it instead
    of old reviews, but still opens the evidence when it needs it.
11. Later cards refer to facts already checked, by ID, instead of searching for them again.
12. Size limits are maximums, not targets. A search stops after 5 searches in a row find nothing new.
13. Scripts, not models, do validation, counting, ID generation and duplicate checks.
