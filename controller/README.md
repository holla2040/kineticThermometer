# Controller design — ongoing discussion

The electronics that drive the sculpture: temperature sensor → controller →
linear actuator position. The sim's temp→extension mapping (linear within the
excursion, optional reverse — see FABRICATION.md) is the spec this controller
must implement. Temperature sensor: TI TMP117 (I²C, ±0.1 °C typ).

Layout: `docs/` notes and datasheets, `src/firmware/`, `src/babysteps/`
(bring-up experiments), `src/web/`.

## MCU (decided 2026-08-20)

**ESP32 DevKitC** — owner has plenty on hand. Board references in `docs/`:
DevKitC v4 schematic, DOIT-variant schematic, and two pinout images.

## Motor driver selection (from ChatGPT "Motor Driver Stock Watch", summarized 2026-08-20)

Source: https://chatgpt.com/share/6a87cd95-d654-83e8-84fd-84b7e82c4eb0

Goal: an integrated H-bridge for the actuator, orderable through LCSC and
assemblable at JLC. Operating point assumed **3–5 A continuous**. LCSC exposes
live price tiers; JLC only shows unit price during BOM/pre-order, so all
prices below are LCSC (USD, checked 2026-08-15).

| Part | LCSC # | Stock | 1 pc | 100 pcs | Verdict |
|------|--------|-------|------|---------|---------|
| TI DRV8245HQRXZRQ1 | C5218845 | 224 | $7.73 | $6.09 | Best overall choice |
| ST VNH7070ASTR | C2150622 | 2,209 | $3.93 | $2.74 | Best value / availability |
| Infineon IFX9201SG | C112633 | 427 | $4.30 | $2.77 | Reasonable, not first choice |
| NXP MC33926PNB | C1556870 | 43 | $8.14 | $6.34 | Expensive and old; avoid |
| MPS MP6615GQKT-Z | — | — | — | — | No LCSC listing at first check |
| MPS MP6612GF-Z | — | — | — | — | No LCSC listing |

Reasoning:

- **DRV8245** — best engineering choice: newest architecture, ~32 mΩ bridge
  resistance, 4.5–35 V, built-in current sensing/regulation, compact VQFN.
  Costs ~$3.35 more per unit than the VNH7070 at qty 100.
- **VNH7070** — best cost/availability: $2.74 @100, 2,200+ in stock,
  15 A-class integrated bridge, ~70 mΩ RDS(on).
- **IFX9201** — worth considering only if its SPI diagnostics appeal.
- **MC33926** — costs more than the DRV8245 with dramatically higher losses
  and a larger package; do not design in.

**Follow-up update** (same thread, later check): the **MP6615 is now in the
LCSC/JLC ecosystem** as **C22697501** — TQFN-26 6×6 mm, SMT Extended Library,
4.75–40 V, 8 A continuous, 11 mΩ per MOSFET, ~¥28.08 (≈$3.90). DRV8245 stock
improved to 248. That makes the MP6615 a real third contender it wasn't at
the first check.

### Open decision

**DRV8245 vs VNH7070** (and now MP6615): at 3–5 A continuous, does the
DRV8245's thermal advantage (~32 mΩ vs ~70 mΩ) justify ~$3.35/unit over the
VNH7070? The MP6615's 11 mΩ/FET at ~$3.90 may undercut both — needs the same
thermal comparison. Not yet decided.
