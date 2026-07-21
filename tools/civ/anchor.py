"""Locate the CI-V section and derive the transceiver address.

The frame-format text string (``FE FE <addr> E0 Cn ... FD``) is the one
signature present in every Icom command manual regardless of era or layout,
so it — not the command-table header — is the primary locator.
"""
from dataclasses import dataclass, field

from .schema import FRAME_CTRL_TO_RADIO, FRAME_RADIO_TO_CTRL, KNOWN_ADDRESSES


@dataclass
class AnchorResult:
    found: bool
    pages: list = field(default_factory=list)       # page indices with a frame hit
    address: str = None                              # consensus address byte
    address_consistent: bool = False                 # both frame directions agree
    address_known: bool = None                       # matches KNOWN_ADDRESSES (or None)
    notes: list = field(default_factory=list)


def _model_key(pdf_name):
    for key in KNOWN_ADDRESSES:
        if key.replace("-", "").lower() in pdf_name.replace("-", "").lower():
            return key
    return None


def locate(pages_text, pdf_name=""):
    """Given a list of per-page text strings, find the CI-V frame anchor.

    Returns an AnchorResult. Address is trusted only when both frame
    directions yield the SAME byte on some page (internal consistency) — this
    is what rejects the IC-9100-style mis-grab of a stray example byte.
    """
    hit_pages, ctrl_addr, radio_addr = [], set(), set()
    consistent = False
    for i, text in enumerate(pages_text):
        t = (text or "").replace("\xa0", " ")
        m1 = FRAME_CTRL_TO_RADIO.search(t)
        m2 = FRAME_RADIO_TO_CTRL.search(t)
        if not (m1 or m2):
            continue
        hit_pages.append(i)
        if m1:
            ctrl_addr.add(m1.group(1).upper())
        if m2:
            radio_addr.add(m2.group(1).upper())
        if m1 and m2 and m1.group(1).upper() == m2.group(1).upper():
            consistent = True

    if not hit_pages:
        return AnchorResult(found=False, notes=["no frame-format signature found"])

    res = AnchorResult(found=True, pages=hit_pages, address_consistent=consistent)

    # Prefer an address confirmed by both directions; fall back to ctrl->radio.
    both = ctrl_addr & radio_addr
    if both:
        res.address = sorted(both)[0]
    elif ctrl_addr:
        res.address = sorted(ctrl_addr)[0]
        res.notes.append("address from controller->radio frame only (unconfirmed)")

    key = _model_key(pdf_name)
    if key and res.address:
        res.address_known = (res.address == KNOWN_ADDRESSES[key])
        if not res.address_known:
            res.notes.append(
                f"address {res.address} != documented {KNOWN_ADDRESSES[key]} for {key}"
            )
    return res
