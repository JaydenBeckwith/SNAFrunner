import argparse, os, re, sys
import pandas as pd

UID_RE = re.compile(r"^(?:chr)?(?:[1-9][0-9]?|X|Y):\d+:\d+:[+-]$")

def clean_sample_name(s):
    return s.replace(".bed", "")

def main():
    ap = argparse.ArgumentParser(description="Trim AltAnalyze_ID '=chr...' tail and prune counts.")
    ap.add_argument("--in",  dest="inp",  required=True, help="counts.original.txt")
    ap.add_argument("--out", dest="outp", required=True, help="counts.original.pruned.txt")
    ap.add_argument("--min-sum", type=float, default=10, help="Min total reads across cohort")
    ap.add_argument("--min-samples", type=int, default=1, help="Min #samples meeting --min-per-sample")
    ap.add_argument("--min-per-sample", type=float, default=2, help="Min reads in a sample to count as supported")
    ap.add_argument("--strict-uid", action="store_true",
                    help="Keep only junction IDs like chr1:123:456:+")
    args = ap.parse_args()

    if not os.path.exists(args.inp):
        sys.exit(f"[ERROR] file not found: {args.inp}")

    # Load matrix (AltAnalyze_ID in col 1)
    df = pd.read_csv(args.inp, sep="\t", header=0, index_col=0, low_memory=False)
    print(f"[INFO] loaded: {df.shape[0]:,} junctions × {df.shape[1]:,} columns")

    # 1) Trim '=chr...' tail from AltAnalyze_ID
    new_index = df.index.to_series().astype(str).str.split("=", n=1).str[0]
    # Merge duplicates created by trimming (sum counts)
    df.index = new_index
    df = df.groupby(df.index, sort=False).sum()

    # 2) Clean sample headers (remove .bed)
    df.columns = [clean_sample_name(c) for c in df.columns]

    # 3) Keep only numeric, coerce others to numeric (NA->0)
    df = df.apply(pd.to_numeric, errors="coerce").fillna(0)

    # 4) Optional: enforce canonical junction ID format
    if args.strict_uid:
        keep = df.index.to_series().astype(str).str.match(UID_RE)
        dropped = int((~keep).sum())
        if dropped:
            print(f"[INFO] strict-uid: drop {dropped:,} rows with non-standard IDs")
        df = df.loc[keep]

    # 5) Pruning
    keep_sum   = (df.sum(axis=1) >= args.min_sum)
    keep_samps = (df >= args.min_per_sample).sum(axis=1) >= args.min_samples
    keep = keep_sum & keep_samps
    dfp = df.loc[keep].astype(int)

    # 6) Write
    os.makedirs(os.path.dirname(args.outp) or ".", exist_ok=True)
    dfp.to_csv(args.outp, sep="\t", header=True, index=True)
    print(f"[OK] wrote {args.outp}  ({dfp.shape[0]:,} × {dfp.shape[1]:,})")

if __name__ == "__main__":
    main()