import argparse, re, pandas as pd

def root_id(s: str) -> str:
    s = re.sub(r"\.bed$", "", str(s))
    return re.split(r"[-_]", s, maxsplit=1)[0]

def to_bed(s: str) -> str:
    return s if str(s).endswith(".bed") else f"{s}.bed"

def patient_id(s: str) -> str:
    s = re.sub(r"\.bed$", "", str(s))
    m = re.match(r"(\d+)", s)
    return m.group(1) if m else root_id(s)

def suffix(root: str) -> str:
    if root.endswith("PRE"): return "PRE"
    if root.endswith("CLND"): return "CLND"
    return "OTHER"

ap = argparse.ArgumentParser()
ap.add_argument("--hla",  required=True, help="TSV with columns: sample, hla")
ap.add_argument("--keep", required=True, help="Text file with sample names to keep (e.g. 53823CLND.bed, 53823PRE.bed)")
ap.add_argument("--out",  default="optitype_summary.filtered.tsv")
args = ap.parse_args()

# desired outputs (explicit sample roots like 53823CLND / 53823PRE)
with open(args.keep) as f:
    desired = [t for t in re.split(r"\s+", f.read().strip()) if t]
desired_roots = [root_id(x) for x in desired]
desired_df = pd.DataFrame({"desired_root": desired_roots})
desired_df["patient"] = desired_df["desired_root"].apply(patient_id)

# HLA table + helper columns
df = pd.read_csv(args.hla, sep="\t", dtype=str)
if "sample" not in df.columns or "hla" not in df.columns:
    raise ValueError("Input --hla must have columns: 'sample' and 'hla'")
df["root"]    = df["sample"].apply(root_id)
df["patient"] = df["sample"].apply(patient_id)
df["suf"]     = df["root"].apply(suffix)
# preference: PRE (0) < CLND (1) < OTHER (9)
pref_map = {"PRE": 0, "CLND": 1}
df["pref"] = df["suf"].map(pref_map).fillna(9).astype(int)

rows = []
for _, req in desired_df.iterrows():
    want = req["desired_root"]
    pid  = req["patient"]

    exact = df[df["root"] == want]
    if len(exact) > 0:
        use = exact.sort_values(by=["pref","root"]).iloc[0]
    else:
        cand = df[df["patient"] == pid]
        if len(cand) == 0:
            # no HLA at all for this patient -> skip
            continue
        # choose best available for this patient (prefer PRE, then CLND)
        use = cand.sort_values(by=["pref","root"]).iloc[0]

    # duplicate row but label as the requested sample root
    rows.append({"sample": to_bed(want), "hla": use["hla"]})

out = pd.DataFrame(rows).drop_duplicates()
out.to_csv(args.out, sep="\t", index=False)

print(f"requested {len(desired_roots)} samples; wrote {len(out)} rows -> {args.out}")
missing = set(desired_roots) - set(out["sample"])
if missing:
    print("WARNING: no HLA found for patients of:", ", ".join(sorted(missing)))
