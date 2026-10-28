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
| Local models in OpenCode (qwen3, gemma4) | Simple text tasks without the internet: reformatting lists, labelling small batches |

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

## Stages and dates

The report is due on 1 November 2026. Research and report writing run side by side.

| Dates | Research | Report |
|-------|----------|--------|
| 20–21 Oct | Stage 0: find sources, check the brief's facts | Outline, budget and plan skeletons |
| 22–24 Oct | Stages 1–2: collect and clean data from the main sources | Draft audiences and the public image |
| 25–26 Oct | Stage 3: analysis | Strategy and answers to criticism |
| 27–28 Oct | Extra research where gaps remain | Final budget and plan |
| 29–30 Oct | Fact check of every number | Russian text, Word file, length checks |
| 31 Oct | | Final review and submission |

On 28 Oct the work was behind this plan. Stages 1–3 now run on 28–30 Oct in a cut form: YouTube comments, Telegram,
VK, district newspapers; no video content (decision D-19). Who does what: `workflow/BOARD.md`.

## Branches

| Branch | What is in it |
|--------|---------------|
| `main` | The brief, the instructions, how the workflow runs, templates and prompts. Finished stages are merged here. |
| `stage-0-discovery` | Stage 0: search terms, the source list, hypotheses and stage 0 cards with their results. Merged into `main` on 28 Oct before its checklist was closed (D-18) |
| `stage-1-collection` | The current branch: stages 1–3 (collection, cleaning, analysis), cut to fit the deadline |
| `stage-4-…` … `stage-6-report` | Created when each stage starts |

## Where to find things

Most documents come in two versions: one for people and one for the agents. They cover the same ground.

| Topic | For people | For agents |
|-------|-----------|------------|
| The project and its rules | `README.md` (this page) | `AGENTS.md` (`CLAUDE.md` points to it) |
| How the work moves | `workflow/README.md` | `workflow/PROTOCOL.md` |
| The current stage | `workflow/stage0/README.md` | `workflow/stage0/T*/CARD.md` |
| Starting an agent | `workflow/README.md` | `workflow/prompts/` |

Tasks only a person can do (exports, launching agents, re-checks) are in `Tasks_for_humans.md`.

Shared by everyone, on the stage branch: `workflow/BOARD.md` (who has which task), `docs/decisions.md`
(what we decided and why), `docs/hypotheses.md` (what we want to test), `config/` (search terms and sources).

## Starting a worker

1. Switch to the current stage branch: `git checkout stage-1-collection`.
2. Open `workflow/BOARD.md` and pick a task marked `ready` for that worker.
3. Start the agent in the repository folder and paste the prompt from `workflow/prompts/worker.md`,
   with the task folder filled in.
4. When the worker finishes, ask Claude or Codex to review it.

Notes for each tool:
- Gemini: run `agy` once to sign in, then start it in this folder.
- Local models: run `ollama serve` first. Use one model at a time, because gemma4 alone takes about 10 GB of memory.

## Collecting data

Keys go in `.env` (copy `.env.example`; `.env` is not in git). Raw results and the run log `_run.json`
go to `data/raw/<source>/<date>/`, which is not in git either.

- YouTube, official API: `.venv/bin/python src/collectors/youtube_comments.py search` finds videos and prints a list;
  `... comments --video <id>` saves all comments of a video. `--help` lists the options.
- Telegram channels, no login needed: `.venv/bin/python src/collectors/telegram_web.py` searches the public channel
  pages and opens the public comment widgets in a hidden Chrome. `--channel <name> --max-comment-posts 2` is a pilot.
- VK and closed Telegram chats: Selenium in your own logged-in browser, at reading pace. A captcha or a block stops
  the run; we do not get around it (decision D-21).
- What has been collected and how it was selected: `docs/data_cards/corpus_manifest.md`.

## Rules everyone follows

- Do not make anything up. Every fact needs a link that was actually opened. "Not found" is an acceptable answer.
- The report does not cite outlets banned in Russia as undesirable organisations, such as Meduza. Agents may
  note them, but every fact needs another source.
- Public content only, and private people are not named.
- No bots, fake accounts or pressure on critics in our recommendations.
- Write plainly, so a person can read it without effort.

## Повторная проверка этапа 0

Из корня репозитория: `.venv/bin/python workflow/stage0/validate_factcheck.py`.
Команда читает CSV, YAML и результаты T06, выводит JSON с результатами и не меняет исходные файлы.
Проверка содержания веб-источников выполняется отдельно; её результаты от 26 октября 2026 года
сведены в `workflow/stage0/FACTCHECK_CODEX_2026-10-26.md`.
