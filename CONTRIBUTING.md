# Contributing

Contributions are welcome. This list is generated from structured JSON data.

Please edit `data/sections.json`, not the generated `README.md`. The data file is described by `data/schema.json`.

```bash
python3 scripts/update_github_metrics.py
python3 gen_readme.py
python3 gen_readme.py --check
```

## Entry Criteria

- Prefer real, installable, public projects over blog-only announcements.
- Link the canonical upstream repository, not an unmaintained fork.
- Keep descriptions factual, one sentence long, and specific about what the tool does.
- Use `status: ["open_source"]` for public-source / open-source projects.
- Add `research` to `status` for papers, benchmarks, datasets, and research frameworks.
- Use `commercial_open` in `status` for commercial products that still provide meaningful open components.
- Add a caveat flag and/or `note` when the project has a restrictive, non-commercial, unclear, missing, or copyleft license.
- Very new repositories, zero-star projects, and projects without a clear root license may be tracked in `WATCHLIST.md` first instead of the main README; they can graduate once license, adoption, and maintenance signals are clearer.

## Entry Format

```json
{
  "name": "ExampleTool",
  "repo": "OWNER/REPO",
  "status": ["open_source"],
  "license": "MIT",
  "flags": ["early_stage"],
  "desc": "One factual sentence about what the tool does.",
  "metrics": {"stars": 123, "updated": "2026-07-23", "snapshot": "2026-07-23"},
  "note": "— **note:** young project with limited independent adoption signal.",
  "related": [
    {"label": "Sibling tool", "url": "https://github.com/OWNER/SIBLING"}
  ]
}
```

Rendered emoji badges are generated from structured fields:

- `open_source` → `🟢`
- `status: [research]` → legacy research-only classification (`🔬`)
- `commercial_open` → `🟠`
- warning flags such as `license_caveat`, `no_license`, `noncommercial`, `copyleft`, or `abliterated_or_uncensored` → `⚠️`
- `flags: [research]` → marks an open-source or commercial-open entry as a research/evaluation artifact (`🔬` when the legacy `research` status is not already present)
- `telemetry` → the tool can emit usage or operational telemetry; disclose defaults and opt-out controls in `note`
- `model_dependent` → material behavior or verdict quality depends on an LLM/model; disclose provider, credential, data-egress, and reproducibility constraints in `note`

Related awesome-list entries use `kind: "awesome_list"` and live in the regular `Related Awesome Lists` section in `data/sections.json`.

GitHub stars and last-commit dates are static snapshots in the optional `metrics` field. Refresh them before release with `python3 scripts/update_github_metrics.py`; do not add live per-entry badge URLs.

If a repository is inaccessible, first check for a canonical move. For a confirmed unresolved case, add a dated availability caveat to the entry and use `--skip-repo OWNER/REPO` (repeatable) to refresh the rest. This preserves its previous metrics and snapshot date and prints a warning; it does not mark them as freshly verified. Unknown skips and all unskipped API errors still fail the refresh without writing the data file.

The badges are generated automatically by `gen_readme.py`; do not paste badge Markdown by hand in the source data.
