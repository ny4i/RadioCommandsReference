# IC-718 CI-V Protocol

## Overview

- Protocol: Icom CI-V
- Transceiver default address: `0x5E`
- Controller default address: `0xE0`
- Terminator: `0xFD`
- OK response: `FE FE E0 5E FB FD`
- NG response: `FE FE E0 5E FA FD`

## Frame Format

### Controller to IC-718

```text
FE FE 5E E0 Cn Sc Data... FD
```

| Field | Value | Notes |
|---|---|---|
| Preamble | `FE FE` | Fixed |
| Radio address | `5E` | IC-718 default |
| Controller address | `E0` | Controller default |
| Command | `Cn` | Main command byte |
| Subcommand | `Sc` | Optional subcommand byte |
| Data | variable | Payload |
| End | `FD` | Fixed |

### IC-718 to controller

```text
FE FE E0 5E Cn Sc Data... FD
```

## Common Encodings

### Boolean

| Value | Meaning |
|---|---|
| `00` | OFF |
| `01` | ON |

### Operating mode

| Code | Mode |
|---|---|
| `00` | LSB |
| `01` | USB |
| `02` | AM |
| `03` | CW |
| `04` | RTTY |
| `07` | CW-R |
| `08` | RTTY-R |

### Frequency payload

Used by commands `00`, `03`, `05`.

```yaml
bytes: 5
encoding: packed_decimal_bcd
least_significant_digit_first: true
digits:
  - 10_hz
  - 1_hz
  - 1_khz
  - 100_hz
  - 100_khz
  - 10_khz
  - 10_mhz
  - 1_mhz
  - 1_ghz_fixed_0
  - 100_mhz_fixed_0
```

### Mode select payload

Used by command path `1A 10`.

| Code | Meaning |
|---|---|
| `00` | OFF |
| `01` | RX |
| `02` | RX & TX |

Mode mask fields shown by the manual: `LSB`, `USB`, `CW`, `RTTY`, `AM`.

## Commands

### Core frequency and mode

| Name | Cmd | Sub/Path | Direction | Data |
|---|---|---|---|---|
| Send frequency data | `00` | format on page | send/transceive | 5-byte frequency payload |
| Send mode data | `01` | format on page | send/transceive | mode code |
| Read band edge frequencies | `02` | format on page | read | lower edge + separator + higher edge |
| Read operating frequency | `03` | format on page | read | response carries frequency payload |
| Read operating mode | `04` | format on page | read | response carries mode code |
| Set operating frequency | `05` | format on page | write | 5-byte frequency payload |
| Set operating mode | `06` | format on page | write | mode code |

### VFO and memory

| Name | Cmd | Sub/Path | Direction | Data |
|---|---|---|---|---|
| Select VFO A | `07` | `00` | write | none |
| Select VFO B | `07` | `01` | write | none |
| Equalize VFO A and B | `07` | `A0` | write | none |
| Exchange VFO A and B | `07` | `B0` | write | none |
| Select memory channel | `08` | `00 01`..`00 99` | write | memory number |
| Select program scan edge P1 | `08` | `01 00` | write | none |
| Select program scan edge P2 | `08` | `01 01` | write | none |
| Memory write | `09` | none | write | unspecified |
| Memory copy to VFO | `0A` | none | write | unspecified |
| Memory clear | `0B` | none | write | unspecified |

### Scan and split

| Name | Cmd | Sub/Path | Direction | Data |
|---|---|---|---|---|
| Cancel scan | `0E` | `00` | write | none |
| Start program/memory scan | `0E` | `01` | write | none |
| Scan resume OFF | `0E` | `D0` | write | none |
| Scan resume ON | `0E` | `D3` | write | none |
| Split OFF | `0F` | `00` | write | `00` |
| Split ON | `0F` | `01` | write | `01` |

### Tuning, attenuation, and levels

| Name | Cmd | Sub | Direction | Values |
|---|---|---|---|---|
| Tuning step | `10` | `00`..`06` | send/read | `00` OFF (10 Hz or 1 Hz), `01` 100 Hz, `02` 1 kHz, `03` 5 kHz, `04` 9 kHz, `05` 10 kHz, `06` 100 kHz |
| Attenuator | `11` | `00` | send/read | `00` OFF, `01` 20 dB |
| AF gain | `14` | `01` | send/read | `00 00`..`02 55` |
| RF gain | `14` | `02` | send/read | `00 00`..`02 55` |
| Squelch level | `14` | `03` | send/read | `00 00`..`02 55` |
| NR level | `14` | `06` | send/read | `00 00`..`02 55` |
| CW pitch | `14` | `09` | send/read | `00 00`..`02 55` |
| RF power | `14` | `0A` | send/read | `00 00`..`02 55` |
| MIC gain | `14` | `0B` | send/read | `00 00`..`02 55` |
| Key speed | `14` | `0C` | send/read | `00 00`..`02 55` |
| BK-IN delay | `14` | `0F` | send/read | `00 00`..`02 55` |

### Meter and status reads

| Name | Cmd | Sub | Direction | Values |
|---|---|---|---|---|
| SQL open/close | `15` | `01` | read | `00` Close, `01` Open |
| S-meter level | `15` | `02` | read | `00 00`..`02 55` |
| Po meter level | `15` | `11` | read | `00 00`..`02 55` |
| SWR meter level | `15` | `12` | read | `00 00`..`02 55` |
| ALC meter level | `15` | `13` | read | `00 00`..`02 55` |
| Read transceiver ID | `19` | `00` | read | response data |
| RX/TX status | `1C` | `01` | send/read | `00` RX, `01` TX |

### Feature toggles

| Name | Cmd | Sub | Direction | Values |
|---|---|---|---|---|
| Preamplifier | `16` | `02` | read/send | `00` OFF, `01` ON |
| Noise blanker | `22` | none | read/send | `00` OFF, `01` ON |
| Noise reduction | `40` | none | read/send | `00` OFF, `01` ON |
| Auto notch | `41` | none | read/send | `00` OFF, `01` ON |
| Compressor | `44` | none | read/send | `00` OFF, `01` ON |
| VOX | `46` | none | read/send | `00` OFF, `01` ON |
| Break-in | `47` | none | read/send | `00` OFF, `01` SEMI, `02` FULL |

### Extended settings (`1A` group)

| Name | Cmd | Path | Direction | Values |
|---|---|---|---|---|
| VOX gain | `1A` | `01 01` | read/send | `00 00`..`02 55` |
| VOX delay | `1A` | `01 02` | read/send | `00 00`..`00 20` |
| Anti-VOX level | `1A` | `01 03` | read/send | `00 00`..`02 55` |
| Key ratio | `1A` | `01 04` | read/send | `00 28`..`00 45` |
| RTTY mark tone | `1A` | `01 05` | read/send | `00` 1275, `01` 1615, `02` 2125 |
| RTTY shift | `1A` | `01 06` | read/send | `00` 170, `01` 200, `02` 425, `03` 850 |
| Dimmer | `1A` | `01 07` | read/send | `00` OFF, `01` Lo, `02` Hi |
| Noise blanker level | `1A` | `01 08` | read/send | `00 00`..`02 55` |
| Meter function | `1A` | `01 09` | read/send | `00` Po, `01` ALC, `02` SWR |
| Mode select | `1A` | `01 10` | read/send | mode mask + `00` OFF / `01` RX / `02` RX&TX |
| RF/SQL VR | `1A` | `01 11` | read/send | `00` SQL, `01` AUTO, `02` RF&SQL |
| Beep setting | `1A` | `01 12` | read/send | `00` OFF, `01` ON |
| Beep level | `1A` | `01 13` | read/send | `00 00`..`02 55` |
| Band edge beep | `1A` | `01 14` | read/send | `00` OFF, `01` ON |
| Side tone level | `1A` | `01 15` | read/send | `00 00`..`02 55` |
| Meter peak hold | `1A` | `01 16` | read/send | `00` OFF, `01` ON |
| Scan speed | `1A` | `01 17` | read/send | `00` Lo, `01` Hi |
| AM noise blanker | `1A` | `01 18` | read/send | `00` OFF, `01` ON |
| Auto TS | `1A` | `01 19` | read/send | `00` OFF, `01` ON |
| Key type | `1A` | `01 20` | read/send | `00` n, `01` r, `02` oF, `03` ud |
| Auto tune | `1A` | `01 21` | read/send | `00` OFF, `01` ON |
| PTT tune | `1A` | `01 22` | read/send | `00` OFF, `01` ON |
| Speech language | `1A` | `01 23` | read/send | `00` English, `01` Japanese |
| Speech speed | `1A` | `01 24` | read/send | `00` Lo, `01` Hi |
| Speech S-meter level | `1A` | `01 25` | read/send | `00` OFF, `01` ON |
| CI-V transceive setting | `1A` | `01 26` | read/send | `00` OFF, `01` ON |
| CI-V 731 mode | `1A` | `01 27` | read/send | `00` OFF, `01` ON |
| Optional filter selection | `1A` | `01 28` | read/send | `00` no, `01` 52A, `02` 53A, `03` 96, `04` 222, `05` 257 |
| Filter expansion | `1A` | `01 29` | read/send | `00` OFF, `01` ON |
| Expanded filter selection (Wide) | `1A` | `01 30` | read/send | `00` no, `01` 52A, `02` 53A, `03` 96, `04` 222, `05` 257, `06` NoR, `07` THU |
| Expanded filter selection (Narrow) | `1A` | `01 31` | read/send | `00` no, `01` 52A, `02` 53A, `03` 96, `04` 222, `05` 257, `06` NoR, `07` THU |

## Format Details

### Operating frequency (`00`, `03`, `05`)

```yaml
command_set:
  - 0x00
  - 0x03
  - 0x05
payload_bytes: 5
encoding: packed_decimal_bcd
order:
  - 10_hz
  - 1_hz
  - 1_khz
  - 100_hz
  - 100_khz
  - 10_khz
  - 10_mhz
  - 1_mhz
  - 1_ghz_fixed_0
  - 100_mhz_fixed_0
```

### Operating mode (`01`, `04`, `06`)

```yaml
command_set:
  - 0x01
  - 0x04
  - 0x06
values:
  0x00: LSB
  0x01: USB
  0x02: AM
  0x03: CW
  0x04: RTTY
  0x07: CW-R
  0x08: RTTY-R
```

### Band edge frequencies (`02`)

```yaml
command: 0x02
payload:
  lower_edge: packed_decimal_bcd_5_bytes
  separator: 0x02
  higher_edge: packed_decimal_bcd_5_bytes
```

### Mode select (`1A 10`)

```yaml
command: 0x1A
path:
  - 0x01
  - 0x10
payload:
  mode_mask:
    - LSB
    - USB
    - CW
    - RTTY
    - AM
  scope:
    0x00: OFF
    0x01: RX
    0x02: RX_TX
```
