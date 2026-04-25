# Apex — Public Track Record

[![Verify Chain](https://github.com/qengine13/apex-track-record/actions/workflows/verify-chain.yml/badge.svg?branch=main)](https://github.com/qengine13/apex-track-record/actions/workflows/verify-chain.yml)

This is the **public, tamper-proof PnL record** for the Apex algorithmic trading
system. Every trading day, a frozen JSON snapshot of the day's performance is
generated, cryptographically chained to the prior day's hash, committed here,
and pushed. A static dashboard rendering of the latest state lives in
[`public/`](public/index.html).

The chain is **third-party verifiable**: anyone can clone this repo, run the
verifier from the open-source `qengine13/trade` repository, and confirm that
no historical entry has been retroactively edited. Any tampering breaks the
hash chain from that day forward and is reported by the verifier.

This repository contains **no source code, no credentials, no live system
state** — only daily snapshots and the rendered dashboard. The trading system
itself is private.

---

## Layout

| Path | Contents |
|------|----------|
| [`chain/`](chain/) | One JSON file per trading day: `{snapshot, prior_hash, chain_hash}`. Filenames are zero-padded UTC day numbers so a lexicographic sort is chronological. |
| [`public/`](public/) | Static HTML dashboard + SVG equity curve. Open `public/index.html` directly or host on GitHub Pages. |
| [`.github/workflows/verify-chain.yml`](.github/workflows/verify-chain.yml) | CI that re-runs the verifier on every push to `main`. The badge above goes red the moment any chain file is tampered with. |

---

## Verify the chain yourself

```bash
git clone https://github.com/qengine13/apex-track-record.git
git clone https://github.com/qengine13/trade.git
cd apex-track-record
python3 -m intelligence_core.track_record.verifier chain/
```

(Adjust `PYTHONPATH` to point at the cloned `trade` repo if the verifier is
not on your import path — the GitHub Action does exactly this.)

Expected output on a healthy chain:

```json
{
  "days": <N>,
  "first_ms": <epoch ms of first entry>,
  "last_ms": <epoch ms of latest entry>,
  "valid": true
}
```

Exit code `0` = chain valid. Exit code `1` = chain broken; inspect which
day's `chain_hash` no longer matches and treat the public record as
compromised from that point forward.

---

## What the snapshot contains

Each daily JSON entry has a `snapshot` object with these fields (spec
versioned via `spec_version`):

- `equity_gbp` — cumulative realized PnL on a £1-staked-per-trade basis
- `win_rate_lifetime` — wins / (wins + losses + flats)
- `drawdown_pct` — worst peak-to-trough drawdown observed to date
- `sharpe_30d` — trailing-30d Sharpe approximation (per-trade, annualized √365)
- `trade_count_lifetime` — total ledger rows ever recorded
- `trade_count_today` — closed trades inside the UTC day window
- `trades_today[]` — per-trade rows: ticker, side, entry, exit, pnl_bps, outcome, horizon_ms

The chaining layer adds `prior_hash` (sha256 of the prior entry, or `GENESIS`
for day 1) and `chain_hash` (sha256 of canonical-JSON snapshot ‖ prior_hash).

---

## Status

Bootstrapped 2026-04-25. Awaiting first paper-trading replay completion before
real PnL data begins flowing into the chain. Until then, the only entries here
are bootstrap and smoke-test snapshots; the chain-verification machinery is
already live so the moment real data lands it is immutably recorded.

---

## License

MIT — see [`LICENSE`](LICENSE).
