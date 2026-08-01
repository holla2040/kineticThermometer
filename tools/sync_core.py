"""Keeps mobile.html's physics byte-identical to index.html's.

    python3 tools/sync_core.py            # --check: fail if they differ
    python3 tools/sync_core.py --apply    # copy index.html's core over mobile.html's

index.html and mobile.html are two hand-maintained pages sharing one solver, one DXF
writer and one set of presets. The shared half sits between

    // ==== SHARED CORE START ====
    // ==== SHARED CORE END ====

in both files. Edit the physics in index.html, run --apply, commit both. Run --check in
verification so a drift is a test failure and not a mis-cut part.
"""
import sys, os, difflib

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "index.html")
DST = os.path.join(HERE, "mobile.html")
START = "// ==== SHARED CORE START ===="
END = "// ==== SHARED CORE END ===="


def split(path):
    """-> (before, core, after). Raises if the markers are missing or out of order."""
    txt = open(path, encoding="utf-8").read()
    i, j = txt.find(START), txt.find(END)
    if i < 0 or j < 0:
        raise SystemExit(f"{os.path.basename(path)}: missing {START if i < 0 else END}")
    if j < i:
        raise SystemExit(f"{os.path.basename(path)}: END marker precedes START")
    if txt.count(START) > 1 or txt.count(END) > 1:
        raise SystemExit(f"{os.path.basename(path)}: markers must appear exactly once")
    return txt[:i + len(START)], txt[i + len(START):j], txt[j:]


def main():
    apply_ = "--apply" in sys.argv[1:]
    sb, score, sa = split(SRC)
    db, dcore, da = split(DST)

    if score == dcore:
        print("shared core in sync (%d lines)" % score.count("\n"))
        return 0

    if apply_:
        open(DST, "w", encoding="utf-8").write(db + score + da)
        print("copied index.html's shared core into mobile.html (%d lines)" % score.count("\n"))
        return 0

    diff = difflib.unified_diff(dcore.splitlines(True), score.splitlines(True),
                                "mobile.html core", "index.html core")
    sys.stdout.writelines(diff)
    print("\nSHARED CORE HAS DRIFTED. Fix index.html, then: "
          "python3 tools/sync_core.py --apply", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
