import argparse, re, pandas as pd

def root_id(s: str) -> str:
    """Normalize sample names:
       - remove trailing '.bed'
       - take part before the first '-' or '_' (e.g. 16518PRE-16518-2_g_normal -> 16518PRE)
    """
    s = re.sub(r"\.bed$", "", str(s))
    s = re.split(r"[-_]", s, maxsplit=1)[0]
    return s

ap = argparse.ArgumentParser()
ap.add_argument("--hla",  required=True, help="TSV with columns: sample, hla")
ap.add_argument("--keep", required=True, help="Text file of sample names to keep (with or without .bed)")
ap.add_argument("--out",  default="optitype_summary.filtered.tsv")
args = ap.parse_args()

# load keep list; accept whitespace/newline separated
with open(args.keep) as f:
    keep_raw = [t for t in re.split(r"\s+", f.read().strip()) if t]
keep = {root_id(k) for k in keep_raw}

df = pd.read_csv(args.hla, sep="\t", dtype=str)
df["root"] = df["sample"].apply(root_id)

out = df[df["root"].isin(keep)][["sample", "hla"]]
out.to_csv(args.out, sep="\t", index=False)

print(f"kept {len(out)} / {len(df)} rows -> {args.out}")
print("examples:", sorted(list({*list(out['sample'].head(3))})))