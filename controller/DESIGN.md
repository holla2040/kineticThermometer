# Controller design — ongoing discussion

The electronics that drive the sculpture: temperature sensor → controller →
linear actuator position. The sim's temp→extension mapping (linear within the
excursion, optional reverse — see FABRICATION.md) is the spec this controller
must implement.

System bus: **12 V or 24 V** — the design must run on either. That choice
ripples through every section below (battery config, solar charge controller,
motor driver voltage ratings, buck regulator input range). *Note: the
off-the-shelf solar panel decision effectively pins this to 12 V — see
[Solar](#solar-interface-for-charging).*

Layout: `docs/` notes and datasheets, `src/firmware/`, `src/babysteps/`
(bring-up experiments), `src/web/`.

**Document rules (owner, 2026-08-20):** this file is the **single point of
truth** for the controller. Every research finding lands here — URLs, prices,
part numbers, measurements, decisions *and their rationale* — so no decision
ever gets rehashed and a future agent needs nothing from chat scrollback. If
research turns up a source, the source goes in this file.

**Provenance note:** a longer motor-driver selection conversation predates the
ChatGPT share linked in the Motor drivers section — the share opens mid-thread
("the parts we discussed"). Searched for on 2026-08-20 in this repo, this
project's session transcripts, and memory: not found. If the owner surfaces
the original thread, fold it in here.

---

## Contents

- [Decision summary](#decision-summary)
- [Hardware](#hardware)
  - [MCU](#mcu---decided-2026-08-20)
    - [Production board: ESP32-S3-WROOM module](#production-board-esp32-s3-wroom-module-on-the-controller-pcb---decided-2026-08-20)
      - [PCB reference: a WROOM board drawn end to end in KiCad](#pcb-reference-a-wroom-board-drawn-end-to-end-in-kicad--2026-08-21)
  - [Motor drivers (need 2)](#motor-drivers-need-2---decided-2026-08-20-ti-drv8245-q1)
  - [Temperature sensor](#temperature-sensor---decided-2026-08-20)
  - [Power supply](#power-supply---open)
  - [Battery and charger](#battery-and-charger---battery-decided-2026-08-20)
  - [Solar interface for charging](#solar-interface-for-charging)
  - [Enclosure](#enclosure---open)
- [Firmware](#firmware)
  - [Homing cycle and position feedback](#homing-cycle-and-position-feedback--required)
  - [Calibration](#calibration--required)
  - [Power management](#power-management)
  - [Dashboard](#dashboard)
  - [OTA updates](#ota-updates--required)
  - [Network / discovery](#network--discovery--required)
- [Features](#features)
  - [Walk-up forecast mode](#walk-up-forecast-mode---proposed-2026-08-20)

---

## Decision summary

Status markers used throughout: ✅ decided · 🔶 open · 💡 proposed

| Topic | Status | Decision |
|-------|--------|----------|
| MCU, bring-up | ✅ 2026-08-20 | ESP32 DevKitC (owner has many) |
| MCU, production | ✅ 2026-08-20 | ESP32-S3-WROOM-1 module on the controller PCB |
| Battery | ✅ 2026-08-20 | 12 V 7 Ah UPS-style sealed AGM |
| Solar panel | ⏸ deferred 2026-08-20 | Retail trickle maintainer, **5 W tier** — see [Panel research round 2](#panel-research-round-2-2026-08-20); top pick on record: SUNER POWER BC-5W Pro. Load ≤2.5 Wh/day (WiFi always on), so 5 W is the smallest framed+weatherproof+float-regulated retail box, not a capacity need. Undersized → customer buys bigger |
| Temperature sensor | ✅ 2026-08-20 | TI TMP117 |
| Bus voltage | 🔶 | 12 V or 24 V required; retail panel choice pushes 12 V — confirm |
| Motor driver | ✅ 2026-08-20 | TI DRV8245-Q1 — quality over cost |
| Charge controller | 🔶 | Must float-regulate SLA; pick with the panel |
| Forecast provider | 🔶 | NWS/weather.gov leading (free, keyless, US-only) |
| Walk-up forecast mode + servo dial | 💡 | Proposed feature, spec'd below |

---

## Hardware

### MCU — ✅ decided 2026-08-20

**Bring-up: ESP32 DevKitC** — owner has plenty on hand. Board references in
`docs/`: DevKitC v4 schematic, DOIT-variant schematic, and two pinout images.

#### Production board: ESP32-S3-WROOM module on the controller PCB — ✅ decided 2026-08-20

Skip the daughter-card-and-header-pins arrangement entirely: solder an
**ESP32-S3-WROOM-1 module** down on the controller PCB itself. Owner's
verdict on module-vs-bare-chip: "a no-brainer" — the module carries flash,
RF matching and antenna built in, is FCC/CE **pre-certified** as an
intentional radiator (key for the for-sale version), and is stocked at
LCSC / assembled at JLC (table below). The bare-chip + own-PCB-antenna route
(cheaper BOM, but we'd own RF layout and radio certification) is **rejected**.

**LCSC/JLC availability (checked 2026-08-20): yes** — same pipeline as the
motor drivers:

| Variant | LCSC # | Notes |
|---------|--------|-------|
| ESP32-S3-WROOM-1-N8 | C2913198 | 8 MB flash, ~$3.03, in stock |
| ESP32-S3-WROOM-1-N16 | C2913199 | 16 MB flash |
| ESP32-S3-WROOM-1-N8R8 | C2913201 | 8 MB flash + 8 MB PSRAM |
| ESP32-S3-WROOM-1-N16R8 | C2913202 | 16 MB flash + 8 MB PSRAM |
| ESP32-S3-WROOM-1U-N8 | C2980297 | U = external-antenna connector version |

The N8 covers this firmware easily (web UI + OTA needs dual app partitions —
8 MB is roomy; PSRAM is for camera/LLM-class loads we don't have). The 1U
variant is the escape hatch if the metal sculpture ends up shadowing the
on-module antenna.

S3 side benefits over the classic ESP32: native USB (no CP2102 bridge), and
none of the devkit's AMS1117/USB-bridge quiescent draw — the board can be
designed to actually reach the low-power numbers the Power-management
section wants.

Plan: **DevKitC for bring-up (`src/babysteps/`), integrated S3 board as the
production design.**

Sources (checked 2026-08-20):

- N8 at LCSC (~$3.03, in stock): <https://lcsc.com/product-detail/WiFi-Modules_Espressif-Systems-ESP32-S3-WROOM-1-N8_C2913198.html>
- N16R8 at LCSC: <https://www.lcsc.com/product-detail/WiFi-Modules_Espressif-Systems-ESP32-S3-WROOM-1-N16R8_C2913202.html>
- JLC assembly listing (N16R8 example): <https://jlcpcb.com/partdetail/3198300-ESP32_S3_WROOM_1N16R8/C2913202>
- Module datasheet: <https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf>
- Espressif hardware design guidelines (schematic/layout/antenna keep-out): <https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/>

#### PCB reference: a WROOM board drawn end to end in KiCad — 2026-08-21

Video reference for drawing this board: *"ESP32-S3 Simple TestBoard designed in
KiCad"*, **made by morten**, 2:29:31, uploaded 2026-08-21 —
<https://www.youtube.com/watch?v=Z5AQMZh3qXw>. An unbroken real-time build of an
ESP32-S3-WROOM-1 board: blank schematic → symbols → footprints → BOM →
45 × 45 mm 4-layer stackup → routing → copper zones → silkscreen → DRC →
Gerbers → fab upload. Machine-transcribed here 2026-08-21 (Whisper
`large-v3-turbo`); digested notes with a timestamp index in
[`docs/video-kicad-esp32s3-morten.md`](docs/video-kicad-esp32s3-morten.md), full
transcript in
[`docs/video-kicad-esp32s3-morten-transcript.md`](docs/video-kicad-esp32s3-morten-transcript.md).
His board is orderable at
<https://www.pcbway.com/project/shareproject/ESP32_S3_SIMPLE_TestBoard_b77edcef.html>.

The findings that touch decisions in this document:

- **PSRAM costs three GPIOs.** On `-R8` (octal-PSRAM) WROOM variants **IO35,
  IO36 and IO37 are used internally** and are unusable. We chose the N8, so they
  are ours — but the `1U`/R8 escape hatch above stops being free the moment
  firmware hard-codes them. Keep IO35–37 unassigned if it costs nothing.
- **Strapping pins**: GPIO0, GPIO3, GPIO45, GPIO46. We have pins to spare —
  don't use them. GPIO3 takes a 10 kΩ pull-up; GPIO0 + EN + RX/TX belong to the
  programming header.
- **EN/reset network**: button EN→GND, 10 kΩ pull-up, 1 µF EN→GND for the reset
  RC, **and an ESD diode on EN** because a finger reaches that button. That last
  part generalises: the walk-up forecast button below is a user-touched GPIO on
  an outdoor metal sculpture, so **every user-facing GPIO gets an ESD part**.
- **Decoupling**: 10 µF + 100 nF at the module, with the **100 nF closest to the
  module VCC pin** in layout.
- **Qwiic (JST SH 4-pin, SM04B-SRSS-TB) for the I²C sensor** — pin 1 GND, 2 VCC,
  3 SDA, 4 SCL; pull-ups **2.2 kΩ** (10 k was drawn and corrected); default S3
  I²C is IO8 SDA / IO9 SCL. 💡 This is the tidy way to put the **TMP117** on a
  cable, off the board and out of its self-heating — spec at
  <https://www.sparkfun.com/qwiic>. 🔶 Open: whether the sensor hangs on a Qwiic
  cable or gets its own sealed gland-and-terminal run, given the outdoor
  environment (JST SH is an indoor connector).
- **A 6-pin ESP-Prog programming header** (EN, TXD, RXD, 3V3, GND, IO0) is a
  complete substitute for on-board USB-UART. We picked the S3 partly *for*
  native USB, so this is not a replacement — but footprinting the header is
  cheap insurance if native-USB bring-up stalls.
- **4-layer stackup that suits us**: top signal / In1 **GND plane** / In2
  **3V3 plane** / bottom signal. Zone settings used: clearance 0.2 mm, thermal
  gap 0.2 mm, spoke 0.3 mm.
- **Workflow**: assign footprints in the *schematic* editor (Tools → Edit Symbol
  Fields), not the PCB editor, so the PCB can't silently substitute one; the same
  dialog carries custom BOM columns (distributor part numbers) and the
  exclude-from-BOM / DNP flags. Annotate before the final BOM export.

**Do not treat it as a template for the whole controller PCB.** It is a
milliamp signal board: linear LM1117 from 5 V (not our 12 V buck), 0.6 mm
"power" tracks, no motor drivers, no high-current copper or thermal work, no
return-path/plane splitting, no impedance control (skipped even on USB), and
nothing about surge, reverse-polarity or transient protection on field wiring.
Those are the hard parts of *our* layout and this video does not touch them.

---

### Motor drivers (need 2) — ✅ decided 2026-08-20: TI DRV8245-Q1

Two driver channels required. The shortlist below was compiled for one
channel at 3–5 A continuous; whatever is chosen, use two (or a dual-channel
part covering both).

**Current sensing is a hard requirement** (added 2026-08-20): the homing
cycle detects the actuator's internal end stops by the motor current
dropping to zero (see [Homing](#homing-cycle-and-position-feedback--required)).
The chosen driver must expose motor current to the ESP32 — the DRV8245's
integrated current-sense mirror fits this exactly; for others, check for a
current-sense pin or budget an external shunt.

**24 V check needed**: the shortlist was drawn up before the 12-or-24 V
requirement. DRV8245 (4.5–35 V) and MP6615 (4.75–40 V) cover a 24 V bus with
headroom; the VNH7070 is an automotive 12 V-class part — verify its max
supply rating before keeping it on a 24 V design. (Moot if the bus is pinned
to 12 V by the solar decision.)

#### Shortlist (from ChatGPT "Motor Driver Stock Watch", summarized 2026-08-20)

Source: <https://chatgpt.com/share/6a87cd95-d654-83e8-84fd-84b7e82c4eb0>

Goal: an integrated H-bridge, orderable through LCSC and assemblable at JLC.
LCSC exposes live price tiers; JLC only shows unit price during
BOM/pre-order, so all prices below are LCSC (USD, checked 2026-08-15).

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
  Ratings clarified 2026-08-20 (owner asked "is it a 32 A device?"): yes —
  TI headlines it as a **40-V, 32-A peak** H-bridge; the identical "32" in
  mΩ and A is coincidence. At our 3–5 A continuous it has huge margin;
  32 A is peak/stall handling, continuous is thermally limited far above
  our operating point. Datasheet:
  <https://www.ti.com/lit/ds/symlink/drv8245-q1.pdf>
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

#### Decision — ✅ TI DRV8245-Q1 (2026-08-20)

Owner: "a no-brainer. I'm not too concerned about the cost of the device.
I'm more concerned about the quality." The ~$3.35/unit premium over the
VNH7070 is accepted. Rationale:

- Newest part on the list: datasheet SLVSFJ1E dated **November 2021**
  (rev. June 2026), TI's current-generation DRV824x-Q1 automotive family.
  The ST VNH7070AS is a mid-2010s design (~2016); the NXP MC33926 is
  2008-era.
- **Datasheet-verified 2026-08-20** (PDF pulled and read, first 3 pages):
  I<sub>OUT</sub> max **32 A**, R<sub>ON</sub> **32 mΩ** in VQFN-HR-16 (the
  LCSC part's package; HTSSOP-28 variant is 40 mΩ/32 A), 4.5–35 V operating,
  40 V abs max, **integrated current sense with proportional IPROPI output**
  — exactly what the homing cycle's current-drop detection needs, no
  external shunt. Huge margin at our 3–5 A.
- LCSC C5218845, ~$6.09 @100 (2026-08-15 pricing above).

Note: the owner asked whether the TI part is newer than "the Toshiba part" —
**no Toshiba device was in this shortlist**; the nearest intended comparison
is the ST VNH7070. If a Toshiba TB67-series part was discussed, it was in
the unrecovered pre-share thread (see Provenance note).

The question this closed, kept for the record: *at 3–5 A continuous, does
the DRV8245's thermal advantage (~32 mΩ vs the VNH7070's ~70 mΩ) justify
~$3.35/unit? And does the MP6615's 11 mΩ/FET at ~$3.90 undercut both?*
Answer: moot — cost was dropped as a criterion; quality/newness decided it.
The full shortlist, per-part reasoning, prices, and the MP6615 follow-up
remain above; the VNH7070 (best value) and MP6615 (best mΩ/$) stay recorded
as the fallbacks if the DRV8245's supply ever dries up.

Part references:

- TI DRV8245-Q1 product page: <https://www.ti.com/product/DRV8245-Q1>
- ST VNH7070AS product page: <https://www.st.com/en/automotive-analog-and-power/vnh7070as.html>
- MPS MP6615: <https://www.monolithicpower.com/> (search MP6615)
- LCSC part pages resolve from the C-numbers in the table, e.g.
  <https://www.lcsc.com/search?q=C5218845>

---

### Temperature sensor — ✅ decided 2026-08-20

**TI TMP117** — I²C, 1.8–5.5 V supply, wired to the ESP32's I²C. Accuracy
**±0.1 °C over −20 to +50 °C** — owner reviewed that figure and accepted it
as sufficient for this sculpture (2026-08-20). Product page / datasheet:
<https://www.ti.com/product/TMP117>

🔶 Open: outdoor placement/housing (radiation shield, cable run) so it reads
air temperature, not enclosure temperature — and outside the electronics
enclosure's self-heating (see [Enclosure](#enclosure)).

---

### Power supply — 🔶 open

Battery bus (12 V or 24 V) → logic rails for the ESP32 and sensors.

- Needs a wide-input buck covering both buses (roughly 9–30 V in) → 5 V for
  the DevKitC's VIN, which regulates 3.3 V on-board.
- 🔶 Open: part selection, quiescent draw (this runs 24/7 outdoors — idle
  current matters more than peak), reverse-polarity and surge protection at
  the battery input.

---

### Battery and charger — ✅ battery decided 2026-08-20

**Lead-acid, UPS-style:** the standard 12 V 7 Ah sealed AGM brick
(CSB GP1272 / Power-Sonic PS-1270 / Yuasa NP7-12 — interchangeable,
~$20–30). Case 151 × 65 × 94 mm, F2 faston terminals preferred. Charges fine
below freezing, unlike LiFePO4 — right for a −20 °F outdoor piece.
One battery = 12 V bus; two in series = 24 V (exactly how 24 V UPSes are
built). Float 13.6–13.8 V, cycle 14.4–14.7 V per battery.

- 🔶 Open: capacity check — is 7 Ah enough for actuator duty cycle + ESP32
  idle draw through winter nights? Same case family goes to 9 Ah (e.g.
  PS-1290) if not.
- 🔶 Open: charger — likely combined with the solar charge controller rather
  than a separate unit.

Sources (checked 2026-08-20):

- CSB GP1272F2 (the APC OEM cell): <https://www.amazon.com/CSB-GP1272F2-Volt-Sealed-Battery/dp/B00HKJ1FW6>
  and <https://www.osibatteries.com/csb-gp1272f2-battery-12v-7-2ah-sealed-lead-acid>
- Power-Sonic PS-1270F1 at Home Depot: <https://www.homedepot.com/p/12-Volt-7-Ah-F1-Terminal-Sealed-Lead-Acid-SLA-Rechargeable-Battery-PS-1270F1/312948092>
- Yuasa NP7-12: <https://www.amazon.com/Yuasa-NP7-12-Sealed-Battery-Terminal/dp/B00FA61Q1G>

---

### Solar interface for charging

> **Read [Panel research round 2](#panel-research-round-2-2026-08-20) at the
> end of this section first.** The load was restated on 2026-08-20 (ESP32
> duty-cycled, 1 s awake per 30 s → ~0.5 Wh/day), which supersedes the 10 W
> recommendation below and re-targets the panel to the **5 W** tier.
> Everything between here and there is kept as the record of how the earlier
> number was reached, and the round-1 candidate list did not survive re-check.

**STATUS 2026-08-20: panel decision DEFERRED (owner).** Assume some
5–10 W retail trickle charger that is suitable, easily available, and
replaceable; pick the exact model later. If a customer's panel proves too
small for their site, they buy a bigger one — that's the virtue of the
off-the-shelf decision. The power analysis in Firmware → Power management
puts the load at ≤2.5 Wh/day with WiFi always on, so any 5–10 W maintainer
has multiples of margin. Everything below (budget history, sizing math,
candidates, remote placement, cautions) stands as research for that later
pick — none of it blocks the rest of the design.

#### Energy budget (researched 2026-08-20)

Operating scheme (owner): firmware polls the TMP117 continuously and moves
the motor only on a **≥1° change** — short ~1 A @ 12 V bursts, MCU-only the
rest of the time.

- **Motor: negligible.** 1°F ≈ 0.12″ of extension (15.5″ over ~130 °F);
  at a rough 0.5″/s that's ~0.25 s × 12 W ≈ 3 J per move. Even 100 moves
  plus a full homing stroke is **< 0.5 Wh/day**.
- **ESP32 DevKitC: dominates.** Community measurements: ~**40 mA @ 5 V
  average WiFi-connected with modem sleep** (spikes ~150 mA), so ~0.2 W;
  light sleep drops the board to 2–5 mA, floored by the DevKitC's AMS1117
  LDO (~5 mA quiescent) and USB bridge. With buck overhead, design at
  **0.25–0.5 W continuous → 6–12 Wh/day**. This, not the motor, sizes the
  panel — and night light-sleep roughly halves it.

Design number: **~7 Wh/day** (modem-sleep days, light-sleep nights),
**~15 Wh/day** worst case (always fully on).

**REVISED 2026-08-20 — production S3 board changes this.** The figures
above assumed the DevKitC always-on (AMS1117 + USB-bridge leakage, no sleep
discipline) and the owner rejected them as the sizing basis ("we can power
everything down… we're not going to consume 15 Wh a day"). On the custom
S3 board with sleep modes: WiFi up with modem sleep during the day only
(~0.1 W × ~12 h ≈ 1.2 Wh), light/deep sleep nights (mW-level), µA-level
TMP117 polling → realistic **~1–3 Wh/day**. New design number: **3 Wh/day**.
The old 7–15 Wh numbers stay above as the record of what the *devkit* would
burn, and as the bound if firmware power management never ships.

Policy caveat that actually drives this budget: mDNS/dashboard reachability
requires the WiFi radio listening — 🔶 pick a policy (daytime-on/night-off
is the assumption behind 3 Wh/day; always-reachable costs ~2× that).

**REVISED AGAIN 2026-08-20 — owner set the operating model:** temperature
doesn't change that fast; **wake every 30 s, run ~1 s, sleep the rest**
(~3% duty cycle). Budget: ~3% × ~60 mA active + deep-sleep floor ≈ ~2 mA
average @ 3.3 V ≈ **~0.5 Wh/day** all-in, including a handful of WiFi
sessions (forecast fetches, occasional dashboard use) and motor bursts.
This is the **current design number: 0.5 Wh/day**.

Consequence: a deep-sleeping ESP32 is NOT reachable by mDNS/dashboard
between wakes. Resolution: the walk-up **button is an RTC-GPIO wake
source** — a press wakes the device and brings WiFi up for a service
window (e.g. 10 min) for the dashboard/calibration; forecast fetches run
on schedule during a wake. 🔶 Confirm the service-window length and
whether any additional scheduled WiFi windows are wanted.

ESP32 consumption sources (checked 2026-08-20):

- Dev-board measurements (40 mA WiFi-connected w/ modem sleep, ~150 mA
  spikes every 100 ms; light sleep 2–5 mA floored by the AMS1117's ~5 mA):
  <https://hubble.com/community/guides/esp32-power-consumption-datasheet-vs-reality/>
- Sleep-mode overview: <https://lastminuteengineers.com/esp32-sleep-modes-power-consumption/>
  and <https://deepbluembedded.com/esp32-sleep-modes-power-consumption/>
- Forum thread with measured numbers: <https://esp32.com/viewtopic.php?t=2662>

#### Panel sizing

Usable harvest ≈ rated W × peak-sun-hours × ~0.7 (controller, dust, angle).

| Scenario | Winter peak-sun-hrs | 5 W panel | 10 W panel |
|----------|--------------------:|-----------|------------|
| Owner (SW Colorado, excellent sun) | ~4 | ~14 Wh/day ✓ | ~28 Wh/day ✓✓ |
| Northern customer (Seattle/New England Dec) | ~1–1.5 | ~4 Wh/day ✗ | ~8 Wh/day — enough **only with night light-sleep** |

Size reality check on the owner's 5×5″/6×6″ guess: 6×6″ of cell at ~20%
efficiency is only ~4.6 W theoretical — commercial panels run bigger:
**5 W ≈ 12.6×6.3″, 10 W ≈ 13.3×8.1″** (standard 12 V "battery maintainer"
panels, IP65, ~$20–35).

**Recommendation (superseded):** the first pass recommended a 10 W panel —
sized against the DevKitC's 7–15 Wh/day worst case for a northern-winter
customer. The owner challenged it as overkill ("the panels are gonna be
huge") — correctly, once the budget was re-based on the production S3 board.

**Recommendation (current, 2026-08-20): 5 W** (~12.6×6.3″). At the 30-s
duty-cycle budget (**~0.5 Wh/day**) even a 2–3 W maintainer balances a
northern December (3 W × 1.2 PSH × 0.7 ≈ 2.5 Wh/day), so wattage is no
longer the constraint — 5 W stays the pick because at retail it is the
smallest tier that reliably comes framed, weatherproof, and with real
float regulation; the 1.5–2.5 W dashboard-style trickle panels are often
unregulated. 10 W is documented insurance only (firmware power management
slips, or an exceptionally bad site). Battery reserve at 0.5 Wh/day:
7 Ah × 12 V = 84 Wh, ~42 Wh usable at 50% DoD → **months** of autonomy;
the battery outlasts any plausible cloudy stretch.

Panel-size sources (checked 2026-08-20): 5 W = 12.6×6.3″
(<https://www.acopower.com/products/hy005-12m>), 10 W = 13.3×8.1×0.7″
(<https://www.amazon.com/ECO-WORTHY-Battery-Charger-Portable-Electrical/dp/B00OZC3X1C>),
sizing guidance <https://voltagebasics.com/what-size-solar-panel-to-trickle-charge-a-12v-battery/>

#### Panel: off-the-shelf retail only — ✅ decided 2026-08-20

Owner's call: **no bare panels, no custom panel enclosure.** Use a consumer
"tractor battery maintainer"-style product the customer can buy and replace
themselves if it breaks — we recommend models rather than bundle glass. The
criterion is **easy retail availability**, not any one store: Harbor Freight
was an example; Amazon, Walmart, REI, Big 5, an auto-parts store — anywhere
common works. Candidates (all 10 W, 12 V, framed/weatherproof, checked
2026-08-20):

| Product | Where | Price | Notes |
|---------|-------|-------|-------|
| Harbor Freight Thunderbolt Solar 10 W Trickle Charger (SKU 70830) | Harbor Freight | $44.99 reg, routinely $25–35 on coupon | The owner's named example; framed panel |
| ECO-WORTHY 10 W maintainer kit | Walmart, Amazon | ~$27–33 | Panel + charge controller + adjustable mount bracket + SAE/clip cables — most complete kit |
| Renogy 10 W trickle maintainer | Amazon, renogy.com | ~$30–40 | SAE + lighter plug + clips; reputable brand |

Wiring is easy in every case: they all terminate in an SAE pigtail with
clip/ring adapters — land it on the battery terminals.

Candidate sources (checked 2026-08-20):

- HF Thunderbolt 10 W (SKU 70830): <https://www.harborfreight.com/10-watt-solar-trickle-charger-70830.html>
  — coupon/price history: <https://hfpricetracker.com/tools/70830>
- ECO-WORTHY 10 W kit (panel + controller + bracket + SAE):
  <https://www.amazon.com/ECO-WORTHY-Controller-Maintainer-Waterproof-Adjustable/dp/B0CSMX7PTL>
  — also at Walmart: <https://www.walmart.com/ip/2718794859>
- Renogy 10 W: <https://www.renogy.com/products/10w-solar-battery-trickle-charger-maintainer>
  — also <https://www.amazon.com/Renogy-Solar-Battery-Maintainer-Trickle/dp/B07QBY7626>

#### Remote panel placement

The customer may site the panel away from the sculpture — to hide that the
piece is solar-powered, or because the sculpture itself sits in shade (a
garden nook, north side of the house) while the panel needs sun. Either way
the wire run may be **buried**. Provide for it:

- Voltage drop is mild at trickle current (~0.6 A), but spec a wire table
  anyway — e.g. 18 AWG to ~25 ft, 14 AWG to ~100 ft — since maintainer
  pigtails are short and thin.
- The extension must be outdoor/direct-burial rated (UF cable, or low-voltage
  landscape-lighting wire in conduit); splice to the panel's SAE pigtail
  with a weatherproof junction.
- Put the charge controller at the **battery end**, not the panel end, so
  the buried run's drop doesn't skew the float voltage.

#### Two cautions

- These maintainers assume a big car battery. Into our small 7 Ah SLA, a
  10 W panel is ~C/12 — a bare blocking-diode panel would overcharge it.
  **Require real float regulation**: either a maintainer with a built-in
  controller (the ECO-WORTHY kit ships one) or add a small inline PWM
  controller with an SLA profile (13.6–13.8 V float). MPPT buys nothing
  under 20 W.
- **These products are all 12 V-only — choosing them effectively pins the
  bus to 12 V** (one battery, no series pair). That simplifies everything
  else; 🔶 confirm in the bus decision.

#### Panel research round 2 (2026-08-20)

**The sizing premise changed on this date, so read this subsection over the
one above.** The owner restated the load: the ESP32 is **duty-cycled, 1 s
awake per 30 s**, motor bursts still negligible → **~0.5 Wh/day** total, not
the 7–15 Wh/day the "Energy budget" subsection above assumed for an always-on
MCU. That earlier budget is kept for the record (it is what an always-on
DevKitC really costs) but it no longer sizes the panel.

*Reconciliation note (added after this research ran): the owner has since
replaced the 30-s duty-cycle model with WiFi-always-on + DFS at
**≤2.5 Wh/day** (see Firmware → Power management). Every conclusion below
survives that change — 5 W × 1.2 PSH × 0.7 ≈ 4.2 Wh/day still clears the
worst site — only this paragraph's 0.5 Wh figure is dated.*

At 0.5 Wh/day, **capacity stopped being the constraint.** Even 2 W balances
the worst customer site: 2 W × 1 peak-sun-hour × 0.7 derate = 1.4 Wh/day, ~3×
the load. So the 10 W recommendation above is superseded — not because 10 W
is wrong, but because it is 20× more panel than the load needs and the owner
wants the panel visually unobtrusive in a garden.

**Why 5 W is still the floor, and it is a market fact rather than an
electrical one.** Below ~5 W the retail category stops being framed
glass-and-aluminium maintainers and becomes dashboard/amorphous trickle
panels: a cell, a blocking diode, suction cups, and no regulator at all. That
is precisely what a 7 Ah SLA must never see. Every sub-5 W product checked
below (Schumacher 2.4 W, and Harbor Freight's discontinued 1.5 W) is
unregulated, and the amorphous ones are physically **larger** than a 5 W mono
panel despite making half the power. 5 W mono is the smallest size where
framed + weatherproof + float-regulated all arrive in one box.

**All three round-1 candidates fail on re-check.** This is the main result of
round 2:

- **ECO-WORTHY 10 W kit (B0CSMX7PTL)** — the round-1 "most complete kit" — is
  **Currently unavailable** on Amazon ("We don't know when or if this item
  will be back in stock"), checked 2026-08-20. The ECO-WORTHY 10 W that *is*
  in stock (B017K6PH1S, $29.99, 6,457 ratings) is a **different, unregulated
  product** — its feature bullets say "built-in blocking diode", the spec box
  lists an 18.7 V output, and no controller is claimed.
- **Renogy 10 W** is two problems. On renogy.com the RSP10TC is $39.99 and
  listed **Unavailable** in the clearance section. The in-stock Amazon item
  (B07QBY7626, $24.94) is a **fabric/PET windshield panel, not framed or
  weatherproof** — Amazon's own review summary flags "the fabric disintegrates
  in sunlight and it's not weatherproof" — and a detailed verified review from
  a van-electrical installer reports **no voltage regulation at all**, taking
  a 9 Ah battery past 15.5 V, with Renogy's manual itself saying not to leave
  it connected unattended. Fails requirements 1 and 3.
- **Harbor Freight Thunderbolt 10 W (SKU 70830)** survives but with two
  caveats found in its manual and listing: it is **In-Store Only** (no
  shipping — the customer needs an HF within driving distance), and its rated
  output is **"14.6 VDC Max"** with an LED-driven cutoff, i.e. an
  absorption-voltage on/off clamp, **not a 13.6–13.8 V float**. The manual
  also says it is "intended only to keep a fully charged battery from losing
  its charge. It will not work to charge a battery that is discharged", and
  warns "Do not leave battery clips attached indefinitely" — awkward wording
  for a product that is our *only* charger.

**No 5 W sibling exists for any of the three.** Harbor Freight's 1.5 W
maintainer (SKU 64251 / 62449 / 44768 / 68692) 404s and is absent from HF's
own solar search results — discontinued; HF's small-panel line is the 10 W
alone. ECO-WORTHY's small units (7.5 W $24.99, 5 W, 2.5 W) are the
blocking-diode family, not the controller kit. Renogy's 5 W is the same
fabric windshield panel in a smaller size.

##### Comparison table (all prices and stock checked 2026-08-20)

| Product | W | Panel size (in) | Price | Retailer(s) | Controller? | Connector / lead | Bracket? | Warranty | URL |
|---------|--:|-----------------|-------|-------------|-------------|------------------|----------|----------|-----|
| **SUNER POWER BC-5W Pro** | 5 | *unverified* — omitted from both the Amazon spec table and the maker's page | $49.99 Amazon / $49.95 maker | Amazon (In Stock, sold by SUNER POWER, FBA); sunerpower.com | **Built in** — MPPT, "3-stages (Bulk, Absorption, Float)" | SAE; 3-piece SAE cable kit (clips / rings / lighter). Lead length unverified; the 10 W sibling is 9.8 ft | No — "Pro" is the portable trim; bracket models sold separately | 12 mo + lifetime tech support (maker) | <https://www.amazon.com/SUNER-POWER-Waterproof-Maintainer-UltraSmart/dp/B0DRFGBX5J> · <https://sunerpower.com/products/bc-5w-solar-battery-charger-pro> |
| **POWOXI 7.5 W** | 7.5 | 14.76 × 9.06 × 1.89 | $37.99 (list $44.99) | Amazon (In Stock, 6.4K ratings); POWOXI has a Walmart brand page | **Built in** — "Upgrade Intelligent Charge Controller"; setpoints unpublished | SAE + cigarette lighter + alligator clips; lead length unverified | Not stated | 12 mo | <https://www.amazon.com/Battery-Portable-Waterproof-Maintainer-conversion/dp/B07JLWFPX6> |
| **SUNER POWER 10 W (B07XNZZHK5)** | 10 | 13.8 × 9.2 × 0.7, 3.4 lb | $59.95 | Amazon (In Stock, FBA, 721 ratings) | **Built in** — MPPT, 3-stage bulk/absorption/float | SAE harness, **3 m / 9.8 ft** — longest verified stock lead here | **Yes** — 360° adjustable ball mount | unverified (12 mo per maker's other listings) | <https://www.amazon.com/SUNER-POWER-Waterproof-Battery-Maintainer/dp/B07XNZZHK5> |
| HF Thunderbolt Solar 10 W (SKU 70830) | 10 | 13.8 × 8.8 × 1.0, IP65, 600 mA | $44.99 (ITC coupon $34.99 expired 2026-07-03; historic low $24.99) | Harbor Freight — **In-Store Only**, in stock Montrose CO aisle 5 | Built in, but **14.6 VDC max cutoff, not a float** | SAE, **8 ft** + clip / ring / 12 V-outlet adapters | Suction cups (4) + carabiners (2) only | 90 days | <https://www.harborfreight.com/10-watt-solar-trickle-charger-70830.html> |
| Callsun 7.5 W | 7.5 | *unverified* | $19.98 (list $21.99) | Amazon (sold by Callsun-US, 165 ratings) | Claimed built in — "IP68 Smart Controller"; **unverified**, not inspected past Amazon's comparison module | SAE-to-SAE | unverified | unverified | (Amazon comparison module on <https://www.amazon.com/Renogy-Solar-Battery-Maintainer-Trickle/dp/B07QBY7626>) |
| Battery Tender 5 W (021-1171) | 5 | *unverified* | $74.95 maker (**Sold out**) / $54.55 Amazon | batterytender.com **sold out**; Amazon; Battery Tender has the broadest auto-parts distribution of any brand here | **Built in** — 3-step microprocessor w/ temperature compensation | Quick-disconnect harness; ring/clip leads sold separately ($12.95 / $15.95) | Windshield mount | **5 yr** | <https://www.batterytender.com/collections/solar-panels> |
| ECO-WORTHY 10 W kit (B0CSMX7PTL) | 10 | 14 × 8.86 × 1.38, IP65 | — | Amazon: **Currently unavailable** | Built in (3-stage per user reports) | SAE, 200 cm + 50 cm clip and ring adapters | Yes — 360° metal | unverified | <https://www.amazon.com/ECO-WORTHY-Controller-Maintainer-Waterproof-Adjustable/dp/B0CSMX7PTL> |
| Battery Tender 10 W (021-1164) | 10 | 28 × 14 × 1 (amorphous — huge) | — | **Discontinued**: absent from batterytender.com; Amazon "Currently unavailable" | Built in, 3-step | 8 ft cord | — | 5 yr | <https://www.amazon.com/Battery-Tender-021-1164-Maintainer-Microprocessor/dp/B004Q86JJ8> |

##### Top 2 recommendations

1. **SUNER POWER BC-5W Pro — $49.99, Amazon, in stock.** The only verified
   5 W product that is framed, weatherproof, and genuinely **float**-regulated
   (a published bulk/absorption/float 3-stage controller, which is exactly
   requirement 3), on an SAE pigtail, Amazon-fulfilled so a customer can
   replace it in two clicks. Buy one and measure it before designing a mount —
   its dimensions are published nowhere.
2. **POWOXI 7.5 W — $37.99, Amazon, in stock.** The second source, from a
   different vendor, and the cheapest regulated unit verified in stock, with
   6,457 ratings behind it. It costs ~20 % more panel area than the 5 W and
   its controller's setpoints are unpublished — take it as the fallback if
   SUNER POWER is out, not as the first pick.

**Bracket-included variant of #1:** the **SUNER POWER 10 W (B07XNZZHK5),
$59.95** — same controller family, dimensions actually published
(13.8 × 9.2 × 0.7″), and it ships the 360° mount and a 9.8 ft SAE lead. Worth
$10 and ~3″ of extra width if the mount and the long lead save fabrication;
the extra 5 W buys nothing at 0.5 Wh/day.

##### Disqualified, with the reason (so these don't get re-proposed)

- **Renogy 10 W (B07QBY7626), $24.94, in stock** — fabric windshield panel,
  not framed/weatherproof; **no voltage regulation**. Fails req 1 and 3.
- **Renogy RSP10TC (renogy.com), $39.99** — listed **Unavailable**, clearance.
- **ECO-WORTHY 10 W (B017K6PH1S), $29.99, in stock** — **blocking diode
  only**, 18.7 V listed output. Would need an inline controller added.
- **ACOPOWER 5 W HY005-12M, $22.90** — 12.6 × 6.3 × 1.0″, IP65, framed,
  10-yr workmanship / 25-yr output warranty, and it is the source of the
  "5 W ≈ 12.6 × 6.3″" figure cited earlier in this section. But it is a
  **bare panel**: no controller, no maintainer cabling. Fails req 1 and 3.
  Good size reference, not a product we can point a customer at.
- **Coleman / Sunforce 6 W (58022)** — 18 × 14.5 × 1.5″ amorphous for 6 W,
  **blocking diode only**. Superb retail breadth (Walmart, Advance Auto
  Parts, Tractor Supply, Home Depot) and still fails req 3, and it is three
  times the area of a 5 W mono panel.
- **Coleman / Sunforce 10 W** — same family; Sunforce's own copy says "a
  charge controller is not required for a 10 Watt solar panel… recommended
  for panels greater than 15 Watts." True for a 50 Ah car battery, **false
  for our 7 Ah**: 667 mA into 7 Ah is ~C/10.
- **Coleman / Sunforce 18 W kit (58032 / 58033)** — this one *does* include a
  7 A charge controller and is stocked at Tractor Supply and Home Depot, but
  18 W is outside the band and it is a large amorphous panel. Noted only as
  the brick-and-mortar option if the Amazon route ever closes.
- **Schumacher SP-200, 2.4 W** — the broadest retail of anything here
  (Walmart, Home Depot, Amazon, farm stores; $15–$40 street, $59.99 MSRP) and
  it still fails: **19.38 × 10.25 × 1.38″ for 2.4 W**, "water-resistant" not
  weatherproof, and no charge controller listed among its components.
- **Harbor Freight Thunderbolt 1.5 W maintainer (SKU 64251)** —
  **discontinued**; product page 404s and it no longer appears in HF's own
  solar search results.
- **Battery Tender solar line generally** — best warranty in the category
  (5 yr) and the best chance of a customer finding one in an auto-parts
  store, but **every panel in it is sold out on batterytender.com** as of
  2026-08-20 (5 W $74.95, 5 W handlebar $89.95, 17 W $134.95, 35 W $179.95)
  and the 10 W is gone entirely. Can't spec a part the maker isn't shipping.

##### If a sub-5 W or unregulated panel is ever wanted anyway

Add one inline controller at the **battery** end (see "Remote panel
placement" above). In stock as of 2026-08-20:

- Battery Tender Solar Charge Controller, SKU 400-0365-BT — **$19.95**
- Battery Tender 5–45 W Automatic Solar Controller, SKU 021-1162 — **$34.95**;
  3 A max out, 32 V max in, 3-stage, AGM/GEL/SLA/flooded/lithium. Setpoints
  not published; the maker's own pages disagree on 1-yr vs 5-yr warranty.
- Harbor Freight Thunderbolt 100 W Solar Charge Regulator — **$14.99**

**One trap, from a verified buyer of the ECO-WORTHY kit:** a panel with a
built-in controller **will not drive a second controller in series** — the two
confuse each other and the panel stops passing current. Pick exactly one
regulator in the chain, either in the panel or inline, never both.

##### Cabling notes for the buried run

All qualifying candidates terminate in **SAE**, so the SAE joint is the
natural splice point for the buried extension, and SAE extension leads are a
stock item. Verified stock lead lengths: SUNER POWER 9.8 ft (longest),
Harbor Freight 8 ft, ECO-WORTHY 2 m (~6.6 ft) — all short enough that a
remote panel needs an extension in every case. Two field reports worth
having: an ECO-WORTHY buyer added 25 ft of 18 AWG speaker wire with no
trouble (consistent with the wire table above at ~0.6 A), and a Renogy buyer
notes none of the supplied leads are fused — **put an inline fuse at the
battery end** of any permanently-installed ring-terminal lead.

Round-2 sources (all checked 2026-08-20):

- Harbor Freight 70830 listing (price, IP65, 600 mA, 24 V Voc, 8 ft cable,
  90-day warranty): <https://www.harborfreight.com/10-watt-solar-trickle-charger-70830.html>
  — owner's manual, source of the "14.6 VDC Max" rating and the
  fully-charged-battery-only caveat:
  <https://manuals.harborfreight.com/manuals/70000-70999/70830-193175515018.pdf>
  — coupon history: <https://hfpricetracker.com/tools/70830> and
  <https://go.harborfreight.com/coupons/2026/05/184727-70830/>
  — HF solar line-up (proves the 1.5 W is gone and the 10 W is In-Store Only):
  <https://www.harborfreight.com/search?q=solar+battery+charger>
- SUNER POWER 5 W Pro: <https://www.amazon.com/SUNER-POWER-Waterproof-Maintainer-UltraSmart/dp/B0DRFGBX5J>
  and <https://sunerpower.com/products/bc-5w-solar-battery-charger-pro>
- SUNER POWER 10 W: <https://www.amazon.com/SUNER-POWER-Waterproof-Battery-Maintainer/dp/B07XNZZHK5>
  — maker's 10 W page (3 m cable, tubular mount, 12-mo warranty):
  <https://sunerpower.com/products/12v-waterproof-solar-battery-trickle-charger-maintainer-10-watts-solar-panel-built-in-intelligent-mppt-solar-charge-controller-tubular-mount-bracket-sae-connection-cable-kits>
- POWOXI 7.5 W: <https://www.amazon.com/Battery-Portable-Waterproof-Maintainer-conversion/dp/B07JLWFPX6>
- ECO-WORTHY 10 W kit, now unavailable: <https://www.amazon.com/ECO-WORTHY-Controller-Maintainer-Waterproof-Adjustable/dp/B0CSMX7PTL>
- ECO-WORTHY 10 W blocking-diode model, in stock: <https://www.amazon.com/ECO-WORTHY-Portable-Backup-Alligator-Adapter/dp/B017K6PH1S>
- Renogy 10 W on Amazon (fabric panel, unregulated per review): <https://www.amazon.com/Renogy-Solar-Battery-Maintainer-Trickle/dp/B07QBY7626>
- Renogy RSP10TC, Unavailable: <https://www.renogy.com/products/10w-solar-battery-trickle-charger-maintainer>
- Battery Tender solar collection (all panels sold out; controller prices):
  <https://www.batterytender.com/collections/solar-panels>
  — 021-1164 10 W, discontinued: <https://www.amazon.com/Battery-Tender-021-1164-Maintainer-Microprocessor/dp/B004Q86JJ8>
  — 021-1162 5–45 W controller: <https://www.batterytender.com/products/battery-tender%C2%AE-5-45w-automatic-solar-controller>
  — 021-1173 17 W (dimensions, 5-yr warranty): <https://www.batterytender.com/products/battery-tender%C2%AE-12v-17-watt-mountable-solar-battery-charger>
- ACOPOWER 5 W HY005-12M (bare panel, dimensions, warranties): <https://www.acopower.com/products/hy005-12m>
- Coleman/Sunforce 6 W 58022: <https://www.amazon.com/Sunforce-58022-Coleman-Battery-Trickle/dp/B004RCR0ZU>
  and <https://shop.advanceautoparts.com/p/coleman-6-watt-12-volt-solar-battery-trickle-charger-58022/10645131-P>
- Coleman/Sunforce 10 W ("no controller needed under 15 W"): <https://www.cabelas.com/p/coleman-10w-solar-battery-trickle-charger-and-maintainer>
- Coleman/Sunforce 18 W kit with 7 A controller: <https://sunforceproducts.com/renewable-energy-products-wind-solar-sunforce/coleman-solar-products/18-watt-12-volt-solar-battery-charger-kit/>
  and <https://www.tractorsupply.com/tsc/product/coleman-18-watt-12v-solar-battery-charger-kit>
- Schumacher SP-200 2.4 W: <https://www.schumacherelectric.com/products/2-4w-solar-battery-maintainer/>
  and <https://www.amazon.com/Schumacher-SP-200-Solar-Battery-Maintainer/dp/B004ZC3TFC>
- Harbor Freight 1.5 W maintainer, now 404: <https://www.harborfreight.com/15-watt-solar-battery-maintainer-64251.html>


---

### Enclosure — 🔶 open

An enclosure for the electronics, with **glanceable status on the outside** —
a walker-by can tell the thermometer is working and the battery is healthy
without opening anything or pulling up the dashboard (which carries the same
info in full).

- **Working indicator**: a slow heartbeat blink (alive + temperature loop
  running). A brief blink every few seconds costs ~nothing from the power
  budget; a solid-on LED would be one of the larger loads — don't.
- **Battery indicator**: state shown simply — e.g. green blink = charging /
  good, red = low. 🔶 Open: one bi-color LED vs two, thresholds (tie to the
  same voltage measurement the dashboard logs).
- Must be readable in daylight (high-brightness LED or light pipe) yet not
  glaring at night in a garden.
- Enclosure itself: outdoor-rated (IP65-ish), gasketed cable entries
  (battery, actuator, sensor, panel SAE, button, servo), and the TMP117
  mounted *outside* the box airflow-wise — electronics self-heating must
  not touch the reading (see Temperature sensor).
- 🔶 Open: off-the-shelf gasketed box vs printed; mounting on/in the
  sculpture base.

---

## Firmware

### Homing cycle and position feedback — required

**On reset the CPU runs a homing cycle** before displaying anything.

Position feedback — two mechanisms, both on the actuator:

- **Encoder: a reed switch** in the actuator. Two wires → one ESP32 input
  pin with a pull-up resistor. Position is relative: count pulses in
  firmware (debounced) from the home reference.
- **End stops: internal limit switches, sensed by motor current.** The
  limits are electrical switches inside the motor with no separate signal
  wires. Commanding the motor **inward** (retract, shortest length) until it
  reaches the stop opens the internal switch — **motor current drops to
  zero, and that current drop IS the stop detection**. The switch only cuts
  drive in the stop's direction: commanding **out** again always moves; the
  actuator never drives backwards through a stop. Motion is strictly in/out.

Homing sequence: drive in → watch motor current → current ≈ 0 means the
inner stop → that's home; zero the reed-switch count there, then move out to
the position for the current temperature.

The actuator is the Joyce QS11940 (measured dimensions and mounting in
FABRICATION.md). 🔶 Open: reed-switch pulses per inch of stroke — measure
during bring-up; it sets the position resolution the calibration can hold.

**Consequence for the motor-driver choice: current sensing is a hard
requirement** (see Motor drivers) — it's the only way to see the stops.

### Calibration — required

Provision for calibrating actuator movement against the actual engraved
scale on the built mechanism — the sim's temp→extension mapping is the
starting spec, but the real linkage/scale will not match it perfectly.

- **Done from a phone**: a web UI served by the ESP32 (lives in `src/web/`).
  Jog the actuator, mark where the indicator actually sits on the engraved
  scale, store the correction persistently (NVS).
- 🔶 Open: calibration model — two-point (offset+gain over the linear
  temp→extension map) vs a multi-point table interpolated along the scale.
  The scale is deliberately non-linear in *arc length*, but temp→extension
  is linear by design, so two-point may suffice; multi-point is the fallback
  if the built mechanism deviates.

### Power management

**Operating model (owner, 2026-08-20): wake every 30 s, run ~1 s, deep-sleep
the rest** — temperature doesn't change fast enough to justify staying up.
Read the TMP117, move the motor if the reading crossed a 1° step, back to
sleep. WiFi comes up only in service windows (button wake) and scheduled
fetches — see the Solar energy budget for the numbers (~0.5 Wh/day) and the
reachability consequence. Day/night distinction stops mattering at this
duty cycle.

**RESOLVED 2026-08-20 — comprehensive power analysis, WiFi ON.** The owner
asked for a realistic number at reduced CPU speed with WiFi kept open, and
directed: don't design around power-saving heroics. Official Espressif
measurements for the ESP32-S3 in Wi-Fi scenarios
(<https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/low-power-mode/low-power-mode-wifi.html>):

| Mode (WiFi connected & reachable) | Average current @3.3 V |
|-----------------------------------|------------------------|
| Modem sleep, DFS ON (CPU auto-downclocks when idle) | **19.5–20.7 mA** (DTIM10–1) |
| Modem sleep, DFS OFF (CPU pegged at 160 MHz) | 38.2–40.1 mA |
| Auto light-sleep, still associated (wakes per DTIM beacon) | **0.93–2.45 mA** |
| Deep sleep (WiFi disconnected) | 6.9 µA |

Readings:

- **DFS (dynamic frequency scaling) IS the "run the CPU slower" idea**, done
  automatically by ESP-IDF: enabling it halves consumption vs a pegged CPU
  (20 mA vs 39 mA) with WiFi fully open. Standalone CPU-frequency baselines
  agree: ~20–31 mA at 80 MHz vs ~30–50 mA at 240 MHz
  (<https://www.luisllamas.es/en/esp32-power-consumption/>,
  <https://www.makerguides.com/measuring-esp32-power-consumption-with-power-profiler-kit-ii/>).
- **Design number: WiFi always on, modem sleep + DFS → ~20 mA ≈ 66 mW ≈
  1.6 Wh/day at the 3.3 V rail, call it ~2 Wh/day from the battery** with
  buck losses. Motor bursts add <0.5 Wh/day. Total **≤ 2.5 Wh/day** with
  zero sleep heroics and the dashboard reachable 24/7.
- Auto light-sleep is a free 10× on top (1–2.5 mA, *still associated and
  mDNS-reachable*, latency = DTIM interval) if ever wanted — but it is not
  needed for the panel to balance, which is the point.
- 💡 Parked (owner, undecided): a double-button-press "enter WiFi mode"
  gesture. Unnecessary for power at these numbers — WiFi can simply stay
  on — but kept as an idea if reachability is ever restricted on purpose.

Earlier framings, kept for the record (both superseded by the analysis
above — the first assumed the MCU stays on all day at devkit-class draw,
the second was a 30-s wake/sleep duty-cycle model the owner set before
directing "let's not even worry about power saving mode"):

- **Explore the DevKitC's low-power modes.** The ESP32 chip deep-sleeps at
  ~10 µA, but the DevKitC board carries a USB bridge and LDO that draw
  quiescent current regardless — measure what the *board* actually pulls in
  deep sleep before counting on it. If it's too thirsty, options: light
  sleep with periodic wake, or cutting the board's power upstream on a
  timer/RTC. (The production S3 board escapes this — see MCU.)
- Evening entry into low power; wake at least often enough to keep the
  displayed temperature honest overnight (it's a thermometer — 🔶 decide the
  night refresh interval).

### Dashboard

The web UI serves a statistics dashboard:

- Current temperature, today's high and low so far (from the TMP117 log),
  and **today's forecast** pulled from an online provider (🔶 open: which —
  NWS/weather.gov is free and keyless for US locations,
  <https://www.weather.gov/documentation/services-web-api>; OpenWeatherMap
  etc. need keys). Same data feeds the walk-up forecast mode.
- **Battery health**: live battery voltage and charge state (owner said
  "charge date" — assumed charge rate/state, 🔶 confirm), plus a **rolling
  30-day log of battery voltage cycling**, so the daily charge/discharge
  curve shows at a glance whether the charge controller is doing its job.
- Implications: a voltage divider from the battery bus into an ESP32 ADC
  (scaled for 24 V max; calibrate the divider — ESP32 ADC is sloppy), and
  ~30 days of samples persisted in flash (LittleFS; e.g. 5-min samples ≈
  8.6k points — trivial). Consider an INA226-style monitor if charge
  *current* turns out to matter for judging the controller.

### OTA updates — required

Firmware updates over WiFi — the ESP32 lives inside an outdoor sculpture;
no USB cable to reflash. Standard ESP32 dual-partition OTA (upload via the
web UI or push over the LAN), with rollback to the previous partition if the
new image fails to boot.

### Network / discovery — required

- **mDNS** so a phone finds the thermometer by name (e.g.
  `thermometer.local`) on the local LAN.
- **AP-mode fallback**: no configured WiFi or LAN unreachable → the ESP32
  runs its own access point; the phone joins it and reaches the same web UI
  (mDNS in AP mode too, plus captive-portal redirect is the usual trick).
- Same web server serves calibration and, later, the forecast-mode
  configuration; WiFi credentials get provisioned through the AP-mode page.

---

## Features

### Walk-up forecast mode — 💡 proposed 2026-08-20

A walker presses a button and the thermometer displays today's forecast high
and low, then returns to the current temperature.

**Mode dial:** while the indicator is traveling, the viewer needs to know
*what* it is moving to. A **hobby servo** sweeps a small dial between three
engraved positions — **HIGH / CURRENT / LOW** — pointing at the one the
indicator is currently heading to (or resting on).

Proposed sequence on button press: servo → HIGH, actuator drives to the
forecast high, dwell; servo → LOW, drive to the forecast low, dwell;
servo → CURRENT, return to live temperature. (Order/dwell times TBD.)

Hardware/firmware implications:

- **Button**: weatherproof momentary switch, ESP32 GPIO, debounced;
  ignore/queue presses while a cycle is already running.
- **Servo**: standard hobby servo, 50 Hz PWM from ESP32 LEDC, runs on the
  5 V rail — adds a peak-current blip to the buck budget. Outdoor-rated or
  housed; consider powering it down between moves to save idle draw and
  avoid hunting.
- **Forecast source**: needs today's high/low. ESP32 has WiFi — a weather
  API is the obvious route, but requires internet at the garden. Leading
  candidate: NWS/weather.gov API — free, no API key, US-only
  (<https://www.weather.gov/documentation/services-web-api>). 🔶 Open:
  connectivity (home WiFi reach? cellular? fall back to recorded
  today's-min/max from the TMP117 if offline), and a keyed provider
  (OpenWeatherMap etc.) for non-US customers.
- The temp→extension mapping already handles arbitrary targets; this is a
  setpoint sequencer on top, not a new mapping.
