# Chain break + honest re-genesis — 2026-05-18

This file exists because the whole point of this repo is that
discontinuities are **declared, never silently papered over**. A hash
chain that gets quietly "fixed" is indistinguishable from a tampered one.
So: here is exactly what happened, why, and what was done.

## What was found

On 2026-05-18 a direct verifier run reported the public chain
**`valid: false`**. It had only **2 entries, 22 days apart**:

| File          | Day   | Written (UTC)        | prior_hash        | chain_hash        |
| ------------- | ----- | -------------------- | ----------------- | ----------------- |
| `020568.json` | 20568 | 2026-04-25T22:14:22Z | `None` (genesis)  | `d3e08965dc3d…`   |
| `020590.json` | 20590 | 2026-05-17T22:00:03Z | `fe8ebb6ad6d6…`   | `c20c8d816e98…`   |

The break: `020590.prior_hash` (`fe8ebb6ad6d6…`) does **not** equal
`020568.chain_hash` (`d3e08965dc3d…`), so the continuity check fails.

## Root cause (a real bug, not data corruption)

`git log` shows **two commits for day 20590** on 2026-05-17 — one at
18:08Z, one at 22:00Z. The publisher ran twice that day.

The old publisher (an untested bash heredoc) chose the prior entry as
`sorted(chain_dir)[-1]`. After the 18:08 run wrote `020590.json`, the
22:00 run's `[-1]` was **that same file** — it chained day 20590 onto
*itself*, then overwrote `020590.json`. The resulting `prior_hash`
(`fe8ebb6a…`) pointed at the now-overwritten 18:08 intermediate hash,
which no file on disk contains. Any same-day re-run corrupted the chain.

The two snapshots held only near-empty shadow-mode noise (equity
−£15.91 → −£50.84, ~11–13% win-rate, `spec_version v1.0`). **No
meaningful performance history is lost by re-genesising.**

## What was done (2026-05-18)

1. The chain-linking logic was extracted to
   `intelligence_core/track_record/publisher.py` with a unit-tested
   anti-corruption contract: the prior entry is the newest entry
   **strictly before today**, and an existing day file is **never
   rewritten** (re-publish is a true no-op). `scripts/publish_track_record.sh`
   is now a thin caller. Regression test:
   `tests/track_record/test_publisher.py::test_same_day_rerun_is_noop_and_chain_stays_valid`.
2. The two broken entries were moved to `_archive_broken_chain_2026-05-18/`
   (kept, not deleted — full audit trail).
3. The chain was re-genesised cleanly from this date. The new chain's
   genesis is the first entry under `chain/` dated on/after 2026-05-18.

The pre-freeze "≥14 valid daily entries" clock therefore restarts from
the new genesis. That honest cost is the point of catching this now
rather than at the finish line.

## Addendum — genesis finalized under converged code (same day)

The publisher was hardened across three independent cross-provider
(codex) review rounds on 2026-05-18, each closing a backdating hole in a
"cleverer" attempt:

1. an early fire sealed an incomplete in-progress day;
2. `trade_count_lifetime` / `win_rate_lifetime` were whole-ledger, not
   point-in-time (a delayed publish backdated current totals);
3. a "catch up yesterday with a synthesised as-of" step sealed a past
   day from a later clock — future-outcome-knowledge backdating.

The converged model deletes catch-up entirely: the snapshot's as-of is
**always the real run clock**, only **today** is sealed and only after
its US close, and a fully-missed evening is an honest **gap**, never a
back-filled entry. Snapshot semantics changed (point-in-time lifetime /
win-rate, as-of-bounded `trades_today`) so `SPEC_VERSION` was bumped
**v1.0 → v1.1**.

Two intermediate genesis entries (`020591.json`, then `020590.json`)
were produced by the *interim* iterations before the model converged —
valid hash entries, but written by code that no longer exists and tagged
v1.0. To keep the live chain's provenance 100% shipped-code and avoid a
v1.0/v1.1 mix in one chain, the last interim genesis was moved to
`_archive_superseded_2026-05-18/` (kept, not deleted — audit trail).
The live `chain/` is intentionally empty until the converged code seals
its first true genesis at the next post-close (22:00 UTC) window. Gate
1.3 honestly reads `valid=True days=0` until then. No performance data
is lost (shadow-mode, near-empty).
