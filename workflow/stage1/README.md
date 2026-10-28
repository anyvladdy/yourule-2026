# Stage 1: collecting and preparing the data (cut version)

Reader: people. Goal: what this stage does and who does what. Agent version: the cards `T*/CARD.md` in this folder.

Because of the 1 November deadline, collection, cleaning and analysis run together on 28–30 October (decision D-19).
We do not analyse video content; we read comments, posts and local papers.

What is already done:
- YouTube: comments under 80 videos about Электрозавод, 10,926 in total. Details: `docs/data_cards/corpus_manifest.md`.
- Telegram: a collector for public channels that needs no login, tested on two channels.

Tasks:

| Card | Who | What it gives us |
|---|---|---|
| T11 | Codex | One clean table of all posts and comments: no duplicates, authors replaced by codes, each item marked as on topic or not and inside or outside the June–October window |
| T12 | dsh | Published prices for every kind of cost in the budget, with links, so each budget line has a source |
| T13 | dsh, second session | Local newspapers (party branches, municipal papers) and residents' chats that discussed Электрозавод |

Next, after T11: a shared guide for labelling posts and comments, then labelling split between Claude, Codex and dsh,
with a random re-check by the user (decision D-20).

Comment texts stay on the computer where they were collected. They do not go into git, because the repository is
public (decision D-24); only counts and summaries are committed.
