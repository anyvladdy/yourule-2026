# HANDOFF T14 — R1 — dsh — 2026-10-28

**Done:** `out/statements.csv` — 12 rows: 8 tenants/cultural users of the site (2025-03-24 «Москвич Mag», 2026-09-30 «Такие дела»), 4 political actors (Московское «Яблоко» ×2, кандидаты в Госдуму по округу 204 Д. Медведев и А. Шатуновская-Бюрно). Page texts kept in `out/pages/`.

**Self-check** (from CARD):
- [x] A1 every URL opened in this session (Chrome headless reader, `read_page.py`); statements, dates, names taken from the opened pages.
- [x] A2 each row is a statement about this site, dated: tenant interviews about the exit and the plant; party/candidate statements about the demolition.
- [ ] A3 both groups covered, or queries listed for the empty one — **tenants covered, deputies not**: no public statement by a municipal deputy of Преображенское, a Moscow City Duma deputy or a State Duma deputy was found. Queries tried: `site:preobr.ru Электрозавод`; preobr.ru news and council pages; `совет депутатов Преображенское Электрозавод обращение`; `депутат Мосгордумы Электрозавод`; `Потапов Мосгордума Электрозавод`; `Электрозавод «депутатский запрос»`; `t.me/s/act_preobrajenka?q=Электрозавод`; `t.me/s/awomandeputy?q=Электрозавод`; VK `public211769320` (council group, no posts on the site); MCD deputies list for ВАО (Преображенское — П. Н. Потапов, no statement found). Political coverage is via party and candidates only.
- [x] A4 private individuals are not named: workshop owners appear by organisation and role; named persons are candidates (public figures).
- [x] A5 R12: no row relies on a designated outlet; «Такие дела», «Москвич Mag», yabloko.ru, msk.kprf.ru, Telegram.

**Deviations from the card:**
- Browsing was done by a local Selenium reader (`read_page.py`, Google Chrome headless, random pauses, short scrolls, one tab, listed URLs only, links not followed) at the user's instruction, instead of by hand. No collector, parser or crawl: 12 pages opened, text saved for reading.
- Stance convention: `neutral` where a tenant describes the exit without judging the project; `oppose` only where the redevelopment itself is criticised. Lines follow `docs/codebook.md`; `loss_of_cultural_spaces` marks statements about the loss of the cluster or of a like-for-like space.
- Two rows share an actor («Яблоко») because they are two dated documents; a third «Яблоко» text is the same June statement republished on 08.07.

**Unsure / could not verify:**
- Whether any municipal deputy spoke in a closed group or a newspaper not indexed online — not found in public web sources.
- Date of the Шатуновская-Бюрно post (channel shows «June 23» without a year); 2026 follows from its content (ГЗК decision) and the channel being her 2026 campaign channel.
- «Красный Вольфрам» and My Pole Space statements come through a journalist's interviews; the organisations' own channels were not found.
