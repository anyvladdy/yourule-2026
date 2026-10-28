# Stage 1: collecting and preparing the data (cut version)

Reader: people. Goal: what this stage does and who does what. Agent version: the cards `T*/CARD.md` in this folder.

Because of the 1 November deadline, collection, cleaning and analysis run together on 28–30 October (decision D-19).
We do not analyse video content; we read comments, posts and local papers.

What is already done:
- One clean table of YouTube, Telegram and VK: 14,340 posts and comments, 4,919 of them are reactions from June to
  October 2026 used in the analysis (T11). Details: `docs/data_cards/corpus_manifest.md`.
- Dzen: 22 articles and 987 comments, all from June 2026 on (T16).

Tasks:

| Card | Who | What it gives us |
|---|---|---|
| T11 | Codex | One clean table of all posts and comments: no duplicates, authors replaced by codes, each item marked as on topic or not and inside or outside the June–October window |
| T12 | dsh | Published prices for every kind of cost in the budget, with links, so each budget line has a source |
| T13 | dsh, second session | Local newspapers (party branches, municipal papers) and residents' chats that discussed Электрозавод |
| T14 | dsh | What tenants, cultural spaces and deputies said in public about the project |
| T15 | Codex or a local Qwen | The 27 media articles labelled again with the shared guide `docs/codebook.md` |
| T16 | dsh, second session | Dzen: a small test first; a full collection only if it finds something new |
| T17 | dsh | Dzen articles and comments added to the same clean table as T11 |
| T18 | Codex | Who is dissatisfied: youth slang, older register and what people say about themselves, crossed with stance. The texts have no age, so the card may end with "the data cannot answer this" |

Also: VK posts and comments are collected by Claude in a browser where you log in yourself (no API, decision D-21),
and Claude looks at Etalon's own channels to compare what the company said with what people heard. Your own tasks
(Wordstat, Google Trends, petition counts, launching agents) are in `Tasks_for_humans.md`.

Next: a local model labels a sample of about 1,200 reactions with the shared guide `docs/codebook.md`, a simple
classifier labels the rest, and the user re-checks a random part of the sample (decision D-28).

Comment texts stay on the computer where they were collected. They do not go into git, because the repository is
public (decision D-24); only counts and summaries are committed.
