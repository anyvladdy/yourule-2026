# YouRule 2026: communications strategy for Электрозавод

This page is for people. AI agents work from `AGENTS.md`, which has the same rules in a stricter form.

This repository holds our solution to a case competition. Группа «Эталон» is redeveloping the Электрозавод
site in Moscow, and the plan has caused a public conflict. We need to write a communications strategy in Russian
that runs until construction starts in March 2027, with a budget of up to 10 million RUB.
The full brief is in [`Коммуникации отбор.md`](Коммуникации%20отбор.md).

Before writing the strategy, we want to understand what people actually think about the project. So we collect
public discussion (Telegram, VK, petitions, media), analyse it, and build the strategy on that evidence.

## Who does the work

Several AI agents share the work, and each has a different job:

| Who | Job |
|-----|-----|
| Claude and Codex | Plan each stage, check every result, and fix whatever is still wrong after two attempts |
| dsh (DeepSeek) | Research with web search: checking facts, timelines, official documents, Telegram |
| Gemini (Antigravity) | Research with web search: VK, petitions, media, similar cases |
| Local models in OpenCode (qwen3, gemma4) | Simple text tasks without the internet: word forms, reformatting lists |

Using different models gives us more than one view. Giving each one small, clear tasks keeps any single agent
from being overloaded.

## How a task moves

The work is split into small tasks. Each task has a card that says what to do, what to read, what to produce
and how we will know it is done.

1. Claude writes the task cards for a stage. Codex reads them once and points out problems. Claude settles the plan.
2. A worker (dsh, Gemini or a local model) does the task and writes a short note on what it did.
3. Codex checks the facts and the format. Claude checks whether the result is useful for the report.
   They write one review together.
4. If something is wrong, the review lists numbered fixes. The worker fixes only those, and the result is checked again.
5. If it is still wrong after the second check, Claude or Codex finishes those parts themselves.
6. When every task in a stage is accepted, Claude and Codex write a short summary and plan the next stage.

To save effort, reviewers check every row of the important facts (heritage status, official decisions, dates)
and a random sample of the rest. If any sampled row turns out to be wrong, the whole file is checked again.

## Stages

| Stage | What happens | Status |
|-------|--------------|--------|
| 0. Scoping | Find the sources and check which facts from the brief can be confirmed. No data collection yet. | in progress |
| 1. Collection | Write collectors and gather posts, comments and articles | not started |
| 2. Processing | Clean the data and keep what is relevant | not started |
| 3. Analysis | Find out who thinks what, the main criticisms and the key actors | not started |
| 4. Strategy | Public image, messages, answers to criticism, channels | not started |
| 5. Budget and plan | Spending up to 10M RUB and a calendar to March 2027 | not started |
| 6. Report | The final report in Russian, up to 8 pages | not started |

## Branches

| Branch | What is in it |
|--------|---------------|
| `main` | The brief, the instructions, how the workflow runs, templates and prompts. Finished stages are merged here. |
| `stage-0-discovery` | The current stage: search terms, the source list, hypotheses, the task board and stage 0 cards with their results |
| `stage-1-collection` … `stage-6-report` | Created when each stage starts |

## Where to find things

Most documents come in two versions: one for people and one for the agents. They cover the same ground.

| Topic | For people | For agents |
|-------|-----------|------------|
| The project and its rules | `README.md` (this page) | `AGENTS.md` (`CLAUDE.md` points to it) |
| How the work moves | `workflow/README.md` | `workflow/PROTOCOL.md` |
| The current stage | `workflow/stage0/README.md` | `workflow/stage0/T*/CARD.md` |
| Starting an agent | `workflow/README.md` | `workflow/prompts/` |

Shared by everyone, on the stage branch: `workflow/BOARD.md` (who has which task), `docs/decisions.md`
(what we decided and why), `docs/hypotheses.md` (what we want to test), `config/` (search terms and sources).

## Starting a worker

1. Switch to the current stage branch: `git checkout stage-0-discovery`.
2. Open `workflow/BOARD.md` and pick a task marked `ready` for that worker.
3. Start the agent in the repository folder and paste the prompt from `workflow/prompts/worker.md`,
   with the task folder filled in.
4. When the worker finishes, ask Claude or Codex to review it.

Notes for each tool:
- Gemini: run `agy` once to sign in, then start it in this folder.
- Local models: run `ollama serve` first. Use one model at a time, because gemma4 alone takes about 10 GB of memory.

## Rules everyone follows

- Do not make anything up. Every fact needs a link that was actually opened. "Not found" is an acceptable answer.
- Public content only, and private people are not named.
- No bots, fake accounts or pressure on critics in our recommendations.
- Write plainly, so a person can read it without effort.
