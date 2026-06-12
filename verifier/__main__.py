"""Third-party verifier for the public track-record chain.

Why this exists:
- The promise of the track-record harness is "anyone can audit". This
  module is the thing they run. It must have zero external dependencies
  (so a verifier can pip-install nothing and just run it), it must be
  small enough to read end-to-end, and its CLI exit code must drive
  GitHub Actions or any other CI cleanly.
- The directory layout it expects is exactly what publish_track_record.sh
  produces: one .json file per day, named so a lexicographic sort matches
  chronological order (the publisher uses zero-padded day numbers).
- Non-JSON files are ignored on purpose so README.md, equity.svg,
  index.html, .gitkeep, etc. can sit alongside the chain without breaking
  verification.

CLI:
    python -m verifier [chain_dir]

Exit code 0 = chain valid, exit code 1 = chain broken.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

from verifier.chain import verify_chain

# Suffix used to identify chain entry files. Any file in the chain dir
# without this extension is treated as a sibling artifact (README, SVG,
# HTML, etc.) and skipped.
CHAIN_FILE_SUFFIX = ".json"

# Default chain directory when no CLI argument is provided. Resolves to
# the current working directory so users can `cd` into a cloned chain
# repo and just run `python -m ... verifier`.
DEFAULT_CHAIN_DIR = "."


def verify_directory(path: str) -> Dict[str, Any]:
    """Verify every .json chain entry in the directory.

    Args:
        path: filesystem path to a directory containing chain entries.

    Returns:
        A dict with keys:
            valid: True iff verify_chain() passed.
            days: number of chain entries loaded.
            first_ms / last_ms: as_of_ms boundaries, or None if empty.

    The shape is JSON-serializable so the CLI can dump it directly and
    CI/dashboards can parse the result without bespoke deserialization.
    """
    files = sorted(
        f for f in os.listdir(path) if f.endswith(CHAIN_FILE_SUFFIX)
    )
    chain = []
    for fn in files:
        with open(os.path.join(path, fn)) as f:
            chain.append(json.load(f))
    return {
        "valid": verify_chain(chain),
        "days": len(chain),
        "first_ms": chain[0]["snapshot"]["as_of_ms"] if chain else None,
        "last_ms": chain[-1]["snapshot"]["as_of_ms"] if chain else None,
    }


def main(argv: list[str]) -> int:
    """CLI entrypoint. Returns the exit code so tests can call without
    invoking sys.exit."""
    target = argv[1] if len(argv) > 1 else DEFAULT_CHAIN_DIR
    result = verify_directory(target)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
