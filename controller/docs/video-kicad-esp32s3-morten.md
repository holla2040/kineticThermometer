# Reference — ESP32-S3-WROOM board in KiCad, start to Gerbers

**Video:** "ESP32-S3 Simple TestBoard designed in KiCad" — *made by morten*
(<https://www.youtube.com/channel/UCqyPRKnXxjDJOQAXV__6yNw>)
<https://www.youtube.com/watch?v=Z5AQMZh3qXw> · uploaded 2026-08-21 · 2:29:31 ·
sponsored by PCBWay.

**Why it is in this repo:** the controller's production board is an
ESP32-S3-WROOM-1 soldered to our own PCB (see
[DESIGN.md → Production board](../DESIGN.md#production-board-esp32-s3-wroom-module-on-the-controller-pcb---decided-2026-08-20)).
This is an unbroken, real-time walkthrough of exactly that board being built in
KiCad — blank schematic → symbols → footprints → BOM → 4-layer stackup →
routing → zones → silkscreen → DRC → Gerbers → fab upload. It is the closest
thing to a worked reference for the board we have to draw.

Full machine transcript with timestamps:
[video-kicad-esp32s3-morten-transcript.md](video-kicad-esp32s3-morten-transcript.md).
Project files and the KiCad libraries he uses are on his GitHub (stated at
[0:03:23], link not given in the description); the board is orderable at
<https://www.pcbway.com/project/shareproject/ESP32_S3_SIMPLE_TestBoard_b77edcef.html>.

**The board he builds (not ours):** ESP32-S3-WROOM-1, 8 MB flash, reset button,
user button, RGB LED, power LED, 2×5 expansion header, 6-pin programming header,
Qwiic I²C connector, 5 V screw terminal → 3V3 LDO, 4× Ø3.2 mm mounting holes,
45 × 45 mm, 4 layers.

---

## Timestamp index

| Time | Section |
|------|---------|
| 0:00:00 | Intro, feature list |
| 0:01:42 | Page settings (title/rev/date) |
| 0:02:33 | Place the WROOM symbol; power + decoupling |
| 0:06:38 | EN/reset: button, RC, ESD diode |
| 0:10:45 | Strapping pins and PSRAM-reserved pins |
| 0:14:06 | Programming header for ESP-Prog (no on-board USB-UART) |
| 0:20:43 | Screw terminal, LM1117 LDO, 5 V → 3V3 |
| 0:25:06 | Power LED, RGB LED |
| 0:30:23 | User button |
| 0:31:14 | Qwiic I²C connector + pull-ups |
| 0:35:21 | Mounting holes, 2×5 expansion header |
| 0:40:52 | Tidy-up: boxes, labels, symmetry |
| 0:49:30 | GPIO assignment; USB test points |
| 0:53:42 | **Footprints assigned in the schematic** (Edit Symbol Fields) |
| 1:00:16 | KiCad crashes, work lost, redo |
| 1:08:58 | BOM: custom columns, CSV export |
| 1:10:34 | Annotate schematic; plot schematic to PDF |
| 1:13:53 | **PCB starts** — update from schematic |
| 1:14:40 | Edge.Cuts 45×45 mm, fillet 4 mm |
| 1:15:26 | Placement, 3D-viewer check |
| 1:26:23 | **4-layer stackup** |
| 1:27:57 | Routing begins; cross-probe from schematic |
| 1:50:23 | Track widths: 0.6 mm / 1 mm for power |
| 1:52:05 | **Copper zones** — GND and 3V3 planes |
| 1:56:58 | Stitching vias into unpoured areas |
| 1:57:43 | Silkscreen, designators, selection filter, align/distribute |
| 2:18:11 | Missing 3D models; copper-to-edge clearance |
| 2:24:11 | **DRC** |
| 2:25:47 | **Gerbers + drill files**, PCBWay plugin upload |

---

## Circuit patterns worth copying

**Module power/decoupling** [0:05:00] — 10 µF + 100 nF on the 3V3 rail at the
module. At layout time [1:37:44] the **100 nF goes closest to the module's VCC
pin**, the bulk cap behind it.

**EN / reset** [0:06:38–0:10:00] — pushbutton EN→GND, 10 kΩ pull-up to 3V3,
1 µF EN→GND. The RC sets the reset pulse; the cap is charged through the 10 k.
Plus an **ESD diode on the EN net**, explicitly because a finger arrives at that
button. For an outdoor sculpture with a walk-up button
([DESIGN.md → Walk-up forecast mode](../DESIGN.md#walk-up-forecast-mode---proposed-2026-08-20))
that ESD part is not optional garnish — it is the pattern for *any* user-touched
GPIO on our board.

**Strapping pins** [0:11:41–0:13:21] — GPIO0, GPIO3, GPIO45, GPIO46 are
strapping pins: "if you have enough pins, just don't play with these." He fits a
10 kΩ pull-up on GPIO3. GPIO0 + EN + RX/TX go to the programming header.

**PSRAM-reserved pins** [0:11:41] — on `-R8` (octal-PSRAM) WROOM variants
**IO35, IO36, IO37 are used internally** and must not be used; KiCad's symbol
marks them with a star. Our choice is the **N8 (no PSRAM)**, so those three are
free — but the DESIGN.md escape hatch to a `1U`/R8 part would take them away.
Anything that hard-codes IO35–37 makes that escape hatch expensive.

**Programming header instead of on-board USB-UART** [0:14:06] — a 6-pin
2.54 mm header (EN, TXD, RXD, 3V3, GND, IO0) wired for the Espressif **ESP-Prog**,
deliberately to avoid a USB-UART bridge plus the auto-reset transistor pair.
Note this is a *simplification for his testboard*, and it partly cuts against our
reason for choosing the S3 (native USB, no CP2102, no bridge quiescent draw). The
useful part for us is the **pinout and the fact that a 6-pin header is a complete
fallback** if native-USB bring-up stalls — cheap insurance to footprint.

**Qwiic / STEMMA QT I²C** [0:31:14–0:34:27, 0:49:30] — JST SH 4-pin
(SM04B-SRSS-TB), **pin 1 = GND (black), 2 = VCC (red), 3 = SDA (blue),
4 = SCL (yellow)**, with the colour legend printed as schematic text. Pull-ups
drawn as 10 k and **corrected to 2.2 kΩ** at [1:23:13] — he had to fix values and
re-export the BOM. Default S3 I²C pins used: **IO8 = SDA, IO9 = SCL**.
**Ours: the TMP117 is I²C.** A Qwiic connector is the obvious way to hang the
sensor on a cable away from the board's own heat — which the sensor section wants
anyway — and 2.2 k is the right pull-up value to start from, not 10 k.
SparkFun's spec: <https://www.sparkfun.com/qwiic>.

**Unused USB D+/D−** [0:51:01, 1:40:10] — broken out to two test points only,
and he says outright he is **not doing impedance control** on them this time. If
we use native USB for programming/OTA-recovery, that is the one thing here we
must *not* copy.

**Power in** [0:20:43–0:25:06] — 2-pin Phoenix screw terminal, 5 V in, LM1117-3.3
in SOT-223 with 10 µF in and out. Our 12 V bus and buck are a different problem;
the screw-terminal-for-field-wiring habit transfers.

**Indicators** [0:25:06–0:29:33] — power LED on 3V3 through 1 kΩ; RGB LED
**common anode** to 3V3 with three current-limiting resistors to three GPIOs.

**Expansion header** [0:36:14] — 2×5, six GPIO (IO10–IO15) + 2× 3V3 + 2× GND.

---

## KiCad workflow worth copying

- **Assign footprints in the schematic editor**, Tools → Edit Symbol Fields, not
  in the PCB editor [0:53:42]. His reason: doing it in the PCB editor lets you
  silently swap in a footprint the schematic never sanctioned. The same dialog
  takes **custom BOM columns** — he adds a `Mouser` column so distributor part
  numbers travel with the design [1:08:58] — and per-part flags for
  "exclude from BOM" / "do not populate" (used on the mounting holes).
- **Annotate before the final BOM export** [1:10:34] — Tools → Annotate, choose
  X-first or Y-first ordering, so designators read in sweep order.
- **Plot the schematic to PDF** in colour, File → Plot [1:12:16].
- **Cross-probe schematic → PCB** [1:19:25]: select a part group in the schematic,
  the same parts highlight in the PCB, then `M` moves the cluster together. This
  is how he keeps each sub-circuit's passives with their part.
- Hotkeys in play: `P` place symbol, `L` net label, `G` drag (schematic),
  `M` move, `D` drag (PCB), `Ctrl+D` duplicate, `B` refill zones.
- **Duplicate net labels rather than retyping them** [0:20:43] — guarantees the
  names match.
- **KiCad crashed at [1:00:16]** during footprint assignment and lost the
  assignments; he redoes them and saves after every batch. Save often.

## Layout / fabrication numbers

- **Outline**: rectangle on Edge.Cuts, 1 mm grid, 45 × 45 mm, then double-click
  the outline → Shape modifications → Fillet lines. **3 mm read as too small,
  4 mm chosen** [1:24:46].
- **The module's antenna end overhangs the board edge** [1:25:37] — deliberate,
  and the standard WROOM keep-out treatment.
- **Stackup** [1:26:23]: 4 layers — top signal / **In1 = GND plane** /
  **In2 = 3V3 plane** / bottom signal.
- **Zones** [1:52:05]: GND poured on top, In1 and bottom; 3V3 on In2. Clearance
  **0.2 mm**, thermal relief gap **0.2 mm**, spoke width **0.3 mm**. `B` refills.
- **Track widths** [1:50:23]: signals at default, **power runs 0.6 mm, some 1 mm**.
  (Our motor rails will need far more than this — his board draws milliamps.)
- **Stitching vias** [1:56:58]: `Ctrl+D` an existing via and drop copies into
  areas the pour did not reach, then refill.
- **Silkscreen** [1:57:43]: the **selection filter** (bottom-right) set to text
  only, so clicking picks the designator and not the footprint; then
  Align → centre and Distribute for even text.
- **Copper-to-edge clearance** [2:18:11]: Board Setup → Design Rules, adjusted to
  bring the pour nearer the edge. *(The transcript reads "1.1 millimeter" but the
  pour visibly moves closer, so the spoken value is suspect — set this from your
  fab's rules, not from this number.)*
- **DRC** [2:24:11]: the only surviving error is **hole size 0.2 mm vs a 0.3 mm
  minimum constraint**, knowingly ignored because the fab drills 0.2 mm.
- **Outputs** [2:25:47]: File → Fabrication Outputs → Gerbers (4 copper + paste +
  silk + mask) and drill files; zip and upload, or use the **PCBWay KiCad plugin**
  which uploads directly once you map top / In1 / In2 / bottom.
- 3D viewer used repeatedly as the placement sanity check; two missing 3D models
  (RGB LED, Qwiic connector) added by hand [2:20:39].

---

## What this video does NOT answer for our board

Everything that makes the controller harder than a testboard is out of scope
here, so do not treat it as a template for the whole PCB:

- No switching regulator — an LM1117 linear from 5 V, not a 12 V buck.
- **No motor drivers, no high-current copper, no thermal work.** Two DRV8245-Q1
  channels and their sense/bulk decoupling are the hard part of our layout and
  none of it appears here. His 0.6 mm "power" tracks are a signal-board number.
- No power-plane splitting or return-path management between motor and logic.
- No impedance control (explicitly skipped, even on USB).
- No outdoor/field concerns: surge, reverse-polarity, transient protection on
  the actuator and sensor cabling, conformal coating, connector sealing.
- No antenna keep-out discussion beyond letting the module overhang the edge —
  and our metal sculpture is the reason DESIGN.md keeps the `1U` external-antenna
  variant on the table.
