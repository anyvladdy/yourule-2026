# How the work is organised

This page is for people. It explains how tasks are shared between the AI agents and how to run them.
The agents follow a stricter version of the same rules in `PROTOCOL.md`.

## The idea

We use several AI models because each one notices different things. To keep any one of them from being
overloaded, the work is cut into small tasks, and every result is checked before we build on it.

Claude and Codex plan and check. dsh (DeepSeek), Gemini and two local models do the tasks.

| Agent | What it is good at | What we give it |
|-------|--------------------|-----------------|
| dsh | Careful research on the web, long tasks, cheap to run | Checking facts, timelines, official documents, Telegram sources |
| Gemini | Searching widely, reading long documents, writing in Russian | VK, petitions, media coverage, similar cases |
| Local models in OpenCode | Free and private, but no internet and short memory | Simple text jobs: word forms, reformatting lists |
| Claude and Codex | Planning and judging quality | Task cards, reviews, finishing what others could not |

## What happens to a task

Each task has a card: what to do, what to read, what to hand in, and a checklist for "done".

1. Claude writes the cards for a stage. Codex reads them once and points out problems. Claude decides the final plan.
2. A worker does the task and writes a short note about it.
3. Codex checks facts and format. Claude checks whether the result is useful for the report and decides.
4. If something is wrong, the worker gets a short numbered list of fixes and does only those.
5. If it is still wrong after the second check, Claude or Codex fixes those parts themselves.
6. When all tasks in a stage are done, Claude and Codex write a short summary and plan the next stage.

Reviewers check every important fact (heritage status, official decisions, dates) and a random sample of
everything else. One wrong row in the sample means the whole file is checked again.

## How to run a task

1. `git checkout stage-0-discovery` (or whichever stage is current).
2. Open `BOARD.md` on that branch and find a task marked `ready` for the agent you want to run.
3. Start the agent in the repository folder.
4. Paste the prompt from `prompts/worker.md`, with the task folder filled in.
5. When the agent says it is done, ask Claude to run the review (Claude starts Codex for its part).

Before the first run:
- Gemini: run `agy` once and sign in.
- Local models: run `ollama serve`. Load one model at a time; gemma4 alone uses about 10 GB of memory.

## Where things are

| File | For | What it is |
|------|-----|-----------|
| `BOARD.md` | everyone | Who has which task and its status |
| `stage0/README.md` | people | What stage 0 is for and its tasks in plain words |
| `stage0/T*/CARD.md` | agents | The exact task instructions |
| `PROTOCOL.md` | agents | The exact rules of this process |
| `prompts/` | agents | Text to paste when starting an agent |
| `templates/` | agents | Formats for cards, handoff notes and reviews |
