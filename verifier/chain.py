"""Cryptographic chaining of daily snapshots — the tamper-proofing layer.

Why this exists:
- A signed git commit alone proves *a* commit was made; it does not prove
  what was inside the file at that moment, because anyone with push access
  can rewrite history. Hash chaining each day's snapshot to the prior day's
  hash makes any retroactive edit instantly detectable: changing day N
  invalidates every chain_hash from N+1 onwards, and the verifier (run by
  any third party) reports the break.
- The hash domain is canonical JSON of the snapshot concatenated with a
  separator and the prior hash. Canonical JSON (sort_keys, no whitespace)
  is critical: if field order or whitespace could shift the hash, a future
  Python version could silently invalidate every prior snapshot.
- "GENESIS" is used as the prior-hash value for day 1 instead of an empty
  string so a forged "empty prior" cannot collide with a genuinely-chained
  snapshot whose prior happened to be "".
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

# Marker used as the prior-hash for the genesis (first) snapshot. We use a
# fixed sentinel rather than "" so an attacker cannot replay a published
# genesis snapshot at a later position by claiming its prior was empty.
GENESIS_MARKER = "GENESIS"

# Separator between canonical-snapshot JSON and prior-hash inside the
# pre-image. Two pipes is unambiguous and cannot appear in canonical JSON
# (which only contains strings, numbers, brackets, commas, colons).
HASH_SEPARATOR = b"||"


def compute_chain_hash(
    snapshot: Dict[str, Any], prior_hash: Optional[str]
) -> str:
    """Compute the chain hash for one snapshot.

    Args:
        snapshot: the daily snapshot dict from build_snapshot().
        prior_hash: the chain_hash of the immediately-prior snapshot, or
            None for the genesis (day-1) entry.

    Returns:
        The 64-char lowercase hex sha256 of canonical-JSON-snapshot
        concatenated with HASH_SEPARATOR and the prior hash (or
        GENESIS_MARKER when prior_hash is None).

    The result is fully deterministic across machines and Python versions:
    json.dumps with sort_keys=True and the compact separators removes all
    field-order and whitespace ambiguity from the pre-image.
    """
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    h = hashlib.sha256()
    h.update(canonical)
    h.update(HASH_SEPARATOR)
    h.update((prior_hash or GENESIS_MARKER).encode())
    return h.hexdigest()


def verify_chain(chain: List[Dict[str, Any]]) -> bool:
    """Verify that every entry's chain_hash matches its inputs.

    Args:
        chain: list of entries each shaped
            {"snapshot": {...}, "chain_hash": "...", "prior_hash": "..."|None}
            in chronological order.

    Returns:
        True iff every entry's recorded chain_hash equals the recomputed
        hash AND every entry's prior_hash equals the prior entry's
        chain_hash. False on the first inconsistency.

    A False result means somebody has tampered with the published artifact
    (or there's a code bug); either way, the public verifier output should
    halt the use of the artifact as proof.
    """
    prior = None
    for entry in chain:
        recorded_prior = entry.get("prior_hash")
        # Continuity check: every entry's prior_hash must match the prior
        # entry's chain_hash. Catches forged inserts and reorderings.
        if recorded_prior != prior:
            return False
        expected = compute_chain_hash(entry["snapshot"], recorded_prior)
        if expected != entry.get("chain_hash"):
            return False
        prior = entry["chain_hash"]
    return True
