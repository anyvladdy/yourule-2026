# Вторая версия анализа

Готовые файлы предыдущей версии не заменяются. Входы: завершённые raw YouTube, Telegram и VK от 28 октября; `_pilot` и `_partial` исключаются, `_v2` дедуплицируются по id. Материалы dsh не используются. Точный список входов и контрольные суммы: `out/build_manifest.json`.

Запуск из корня репозитория в подготовленной `.venv`:

```sh
.venv/bin/python workflow/stage1/T11_processing/v2/test_v2.py
.venv/bin/python workflow/stage1/T11_processing/v2/test_nlp_r2.py
.venv/bin/python workflow/stage1/T11_processing/v2/build_corpus_v2.py
.venv/bin/python workflow/stage1/T11_processing/v2/analyze_nlp_v2.py
.venv/bin/python workflow/stage1/T11_processing/v2/render_executive.py
```

Сборка читает локальный `.secrets/hash_salt`; его нельзя публиковать. Интернет для обработки не нужен. Версии библиотек записаны в `out/environment_versions.json`. Сборщик базовой версии импортируется как модуль; его самостоятельный запуск для v2 не нужен.

Результаты:

- `data/processed/corpus_v2.parquet` — расширенный локальный корпус; тексты не публиковать.
- `out/nlp_annotations.parquet` — локальная разметка тем и условий отбора.
- `out/executive_brief.html` — шесть страниц для показа в браузере, полностью автономный файл.
- `out/figures/` — шесть графиков PNG 2400×1350 и SVG с редактируемым текстом.
- `ANALYSIS.md` — выводы, рекомендации, метод и ограничения.
- `out/etalon_analysis_v2.zip` — комплект для просмотра без исходных текстов и идентификаторов авторов.

`out/build_checks.txt` содержит результаты проверок и предупреждение о пропущенных родителях Telegram. Буквальная приёмка всех критериев исходной T11 требует решения ревьюера; новый корпус не заменяет молча прежний. Для разметки следующего этапа следует использовать путь с `_v2`.

Правки R2 (C1, C3): девять словарных тем без ранжирования; n-граммы считаются один раз на авторский аккаунт, неизвестные авторы исключены. Для пересчёта только аналитики запускать `analyze_nlp_v2.py` и `render_executive.py`, без сборщика корпуса. Поле `unique_author_count` в `ngrams.csv` заменяет прежнее `unique_document_count`.
