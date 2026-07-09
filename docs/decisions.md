# Decisions Log / Журнал решений

Format: `date — decision — why`. Newest on top. Entries may be in English or Russian.
Schema changes (PLAN.md §2) MUST be announced here the same day.

- 2026-07-08 — Canonical data schemas live in [PLAN.md §2](en/PLAN.md); role files hold convenience copies — one source of truth for field names.
- 2026-07-08 — Literature PDFs are local-only (gitignored); reading guide with sources stays in [papers/README.md](../papers/README.md) — keeps clones small (~70 MB saved).
- 2026-07-08 — Project docs unified and moved into this repo (README/PROPOSAL/PLAN/GLOSSARY ×2 languages + roles/); superseded drafts remain outside the repo in the SMILES folder `archive/` — single living home for docs.
- 2026-07-08 — Repo skeleton created per [PLAN.md §6](en/PLAN.md): data/manifests, src/models, src/prompts, configs, notebooks, results, docs.
