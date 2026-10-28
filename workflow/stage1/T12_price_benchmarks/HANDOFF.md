# HANDOFF T12 — R1 — dsh — 2026-10-28

**Done:** `out/prices.csv` — 30 rows, all keys K01–K20 covered (1–3 rows each), 24 distinct URLs opened this session.

**Self-check:**
- [x] A1 all 20 keys have at least one row; no `not_found` needed
- [x] A2 every URL opened in this session; prices copied from the page text, no guesses
- [x] A3 every row has unit and `vat`; ranges are published numbers (`excl` never assumed — `unknown` where the page is silent)
- [x] A4 non-Moscow sources labelled `proxy` with the reason: K04–K06 (Voronezh agency), K02 (Russia-wide blog), K17 analyst (wider profile). K01–K03, K07–K16, K18–K20 are Moscow or federal
- [x] A5 one procurement record used: K16, tender 338650762 (bicotender, показан 11.08.2026). zakupki.gov.ru search needs a session and was not reachable for a stable price list
- [x] A6 five weakest keys named below

**Weakest five:** K01 (one source, agency package only, no day rate found), K12 (one "от" price for documentation, closest to a text review), K16 (one contract for a top-level moderator, likely above an open meeting), K08 (one "от" price, no VAT information), K13 (one marketplace offer, session contents unknown).

**Deviations:** the 3% rule in K14 has no ruble price, so its price columns are empty and the rate sits in `what_priced`; only K18–K20 were meant to be empty. Page reading used a one-page text extractor, kept in `tools/fetch_one_page.py`; no crawling or bulk download.

**Unsure / could not verify:** VAT status for commercial prices (print, agencies, venues) — pages do not state it; I did not assume `incl`. Медиалогия, Brand Analytics and Крибрум publish no public tariff; only IQBuzz was priced. ОРД tariffs of Yandex and VK not checked. A second venue and a second law firm were found but their pages showed no price or were unavailable.
