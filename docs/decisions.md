# Decisions Log / Журнал решений

Format: `date — decision — why`. Newest on top. Entries may be in English or Russian.
Schema changes (PLAN.md §2) MUST be announced here the same day.

- 2026-07-12 — **Каскад вернулся в пилот**: прогоны успели пройти в Colab, поэтому предзащита показывает 4 прогона (2 системы × 2 промпта); запись «каскад перенесён в основную фазу» ниже — устарела. Итоги: `results/pilot_summary.md`.
- 2026-07-12 — Категория B размечена вручную M1 (93 ответа, по полным текстам, `judge: "manual-M1"`); в `judge.py` для неразмеченных B correctness = None и accuracy_B считается только по размеченным; добавлена метрика `no_abstain_rate_on_c`; `run_eval.py` переведён на argparse.
- 2026-07-12 — **Пилот заморожен**: 100 элементов (30 A / 30 B / 40 C: 12 absent-entity + 12 missing-attribute + 8 false-presupposition + 8 off-topic); согласие проверяющих на 20 общих строках = 16/20 (80%); 4 спорных строки авто-дропнуты (sq-0714-B2, sq-3032-C7, sq-0774-B3, sq-3234-C7). `pilot.jsonl` дальше только append-only.
- 2026-07-12 — Каскад (Whisper→LLM) перенесён в основную фазу; прогоны предзащиты = Qwen2-Audio × {plain, s1_idk}.
- 2026-07-10 — До предзащиты коммитим прямо в main без PR (мало времени, команда из 3); правило PR+ревью возвращается в основной фазе.
- 2026-07-10 — LLM-судья на пилоте НЕ используется: категорию B размечаем вручную втроём (~120 ответов); выбор модели-судьи — решение основной фазы. Correctness для B до ручной разметки = None (не 0!).
- 2026-07-10 — Выходная схема прогонов дополнена полем `asr_transcript` (только для cascade) — нужно M3 для sanity-проверки транскриптов.
- 2026-07-08 — Canonical data schemas live in [PLAN.md §2](en/PLAN.md); role files hold convenience copies — one source of truth for field names.
- 2026-07-08 — Literature PDFs are local-only (gitignored); reading guide with sources stays in [papers/README.md](../papers/README.md) — keeps clones small (~70 MB saved).
- 2026-07-08 — Project docs unified and moved into this repo (README/PROPOSAL/PLAN/GLOSSARY ×2 languages + roles/); superseded drafts remain outside the repo in the SMILES folder `archive/` — single living home for docs.
- 2026-07-08 — Repo skeleton created per [PLAN.md §6](en/PLAN.md): data/manifests, src/models, src/prompts, configs, notebooks, results, docs.
