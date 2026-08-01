"""Minimal DXF group-code reader, shared by the two verification scripts.

Its own module because verify_export.py runs its whole suite at import time — anything
that needs the reader has to get it from somewhere that does nothing when imported.
"""


def parse_dxf(txt):
    """-> list of entities in the ENTITIES section, each {'type':…, <group code>:[vals]}."""
    lines = txt.split("\r\n")
    assert lines[-1] == "", "file must end with a line terminator"
    pairs = [(int(lines[i]), lines[i+1]) for i in range(0, len(lines)-1, 2)]
    ents, cur, inent = [], None, False
    for code, val in pairs:
        if code == 2 and val == "ENTITIES":
            inent = True; continue
        if not inent: continue
        if code == 0:
            if cur: ents.append(cur)
            if val in ("ENDSEC", "EOF"): cur = None; inent = False; continue
            cur = {"type": val}
        elif cur is not None:
            cur.setdefault(code, []).append(val)
    return ents
