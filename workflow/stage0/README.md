# Stage 0: finding the sources

This page is for people. The agents work from the task cards in each `T*` folder.

## What this stage is for

Before we collect anything, we need to know three things:

1. Which parts of the brief's story can be confirmed in public sources. The 2026 conflict may be partly invented
   for the competition. Where nothing can be found, we will use clearly labelled stand-ins, such as general
   discussion of Электрозавод, Etalon's reputation and similar conflicts elsewhere.
2. Where people discuss the project: which Telegram channels, VK groups, petitions and media.
3. What is officially true about the site: which buildings are protected, what the developer has said publicly,
   and what has been decided.

Nothing is downloaded or scraped in this stage. Agents search and read by hand, and record what they find
with links and dates.

## The tasks

| Task | Who | What it answers |
|------|-----|-----------------|
| T04 | dsh | Which claims in the brief are real, and what happened when. Runs first. |
| T02 | Gemini | Which VK groups and petitions exist, how many signatures, what they demand |
| T06 | local qwen3 | All word forms of our search terms, so later searches miss nothing |
| T01 | dsh | Which Telegram channels and videos discuss the project |
| T03 | Gemini | How the media covered it and what the main criticisms are |
| T08 | dsh | Official documents, the developer's statements, and the status of each building |
| T05 | Gemini | How similar conflicts went elsewhere and what helped |
| T07 | local gemma4 | Reformats the found sources into our source list (planned once T01–T03 and T08 are done) |

T08 is checked line by line, because a wrong fact about which buildings are kept would hurt the client most.

## When the stage is done

All tasks are accepted, and Claude and Codex have:
- updated the search terms and the source list;
- recorded where we have real data and where we use stand-ins;
- mapped which evidence supports each of the six report sections;
- drafted the list of audiences to study;
- planned stage 1, the actual data collection.

Then this branch is merged into `main` and stage 1 starts on a new branch.

Codex's critique of the first plan, and what we changed because of it, are in `PLAN_CRITIQUE.md` and
`docs/decisions.md` (D-05 to D-07).
