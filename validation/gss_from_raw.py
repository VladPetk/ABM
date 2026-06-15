"""Independent GSS cross-check of the cultural common-mode trend (battery F0).

ANES says the partisan center of mass was culturally TRADITIONAL in the 1990s/2000s
and liberalized in the 2010s; the model misses that hump. Here we confirm the same
secular trend from a *different* dataset (GSS) and different items, built from raw.

We construct a society-wide cultural-traditionalism z-index from canonical GSS moral
items, weighted (wtssall), by year, and compare its SHAPE to the ANES cultural
center-of-mass and to the model. Outputs validation/anchors_gss.json.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DTA = ROOT / "data/gss_raw/gss7224_r3.dta"
HERE = Path(__file__).resolve().parent

# item -> +1 if higher raw code = more TRADITIONAL, -1 if higher raw = more progressive
ITEMS = {
    "homosex":  -1,   # 1 always wrong (trad) .. 4 not wrong at all (prog)
    "premarsx": -1,   # 1 always wrong .. 4 not wrong at all
    "abany":    +1,   # 1 yes/allowed (prog) .. 2 no (trad)
    "fefam":    -1,   # 1 agree woman-tend-home (trad) .. 4 disagree (prog)
    "grass":    +1,   # 1 legal (prog) .. 2 not legal (trad)
}
ECON = {"helppoor": +1, "eqwlth": +1}  # higher = more "people should help selves" / less redistribute (right)


def zorient(series, sign):
    v = pd.to_numeric(series, errors="coerce")
    z = (v - v.mean()) / v.std()
    return z * sign


def main():
    cols = ["year", "partyid", "wtssall"] + list(ITEMS) + list(ECON)
    df = pd.read_stata(DTA, columns=cols, convert_categoricals=False)
    df["w"] = pd.to_numeric(df["wtssall"], errors="coerce").fillna(0.0)

    # cultural traditionalism index: equal-weight mean of oriented z-scores
    zc = pd.DataFrame({k: zorient(df[k], s) for k, s in ITEMS.items()})
    df["trad"] = zc.mean(axis=1, skipna=True)          # +ve = more traditional
    df["n_items"] = zc.notna().sum(axis=1)
    ze = pd.DataFrame({k: zorient(df[k], s) for k, s in ECON.items()})
    df["econ_right"] = ze.mean(axis=1, skipna=True)

    # 3-pt party from partyid (0-1 D incl lean, 3 I, 5-6 R; 7=other dropped)
    pid = pd.to_numeric(df["partyid"], errors="coerce")
    df["party3"] = np.where(pid <= 2, "D", np.where(pid == 3, "I",
                     np.where(pid.between(4, 6), "R", None)))

    def wmean(g, col):
        m = g[col].notna() & (g.w > 0)
        if m.sum() < 30:
            return None
        return float(np.average(g.loc[m, col], weights=g.loc[m, "w"]))

    pub, part = {}, {}
    for yr, g in df[df.n_items >= 2].groupby("year"):
        v = wmean(g, "trad")
        if v is not None:
            pub[int(yr)] = round(v, 4)
        gd = g[g.party3.isin(["D", "R"])]
        vp = wmean(gd, "trad")
        if vp is not None:
            part[int(yr)] = round(vp, 4)

    result = {
        "source": "GSS 1972-2024 Cumulative (Release 3), WTSSALL weighted, from raw",
        "items_cultural": ITEMS,
        "note": "z-index, +ve = more culturally traditional (society-wide common mode)",
        "public_traditionalism": pub,
        "partisan_traditionalism": part,
    }
    (HERE / "anchors_gss.json").write_text(json.dumps(result, indent=2))
    print(f"wrote {HERE/'anchors_gss.json'}")

    print("\n=== GSS society-wide cultural traditionalism (z, +ve=traditional) ===")
    ys = sorted(pub)
    peak = max(pub, key=lambda y: pub[y])
    for y in ys:
        if y % 4 == 0 or y in (peak,):
            bar = "#" * int(max(0, (pub[y] + 0.5) * 30))
            print(f"  {y}: {pub[y]:+.3f} {bar}")
    print(f"\n  PEAK traditionalism year: {peak} ({pub[peak]:+.3f})")
    early = np.mean([pub[y] for y in ys if 1990 <= y <= 2000])
    late = np.mean([pub[y] for y in ys if y >= 2018])
    print(f"  1990-2000 mean: {early:+.3f}   2018+ mean: {late:+.3f}   shift: {late-early:+.3f}")
    print("\n  => If 1990s are clearly more traditional than the 2010s, GSS independently")
    print("     confirms ANES F0: a society-wide cultural liberalization the model omits.")


if __name__ == "__main__":
    main()
