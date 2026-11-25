#!/usr/bin/env python3
"""
scripts/gen_docs.py

Regenerates all <!-- BEGIN:metrics:* --> blocks across README.md, docs/results.md,
and docs/vplan.md strictly from docs/metrics.json.
"""

import json
from pathlib import Path
from doc_blocks import PROJ_DIR, apply_blocks_to_text, render_all_blocks


def main():
    metrics_path = PROJ_DIR / "docs" / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    rendered = render_all_blocks(metrics)
    for rel_path, blocks in rendered.items():
        fpath = PROJ_DIR / rel_path
        old = fpath.read_text(encoding="utf-8")
        new = apply_blocks_to_text(old, blocks)
        fpath.write_text(new, encoding="utf-8")
        print(f"Updated {rel_path} ({len(blocks)} generated blocks).")


if __name__ == "__main__":
    main()
