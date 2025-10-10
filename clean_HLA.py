#!/usr/bin/env python3
import argparse, re, sys
from pathlib import Path
import csv

ALLELE_RE = re.compile(r'(?:HLA-)?[ABC]\*\d{2}:\d{2}')

def newest_result(optitype_dir: Path):
    """Return the newest *_result or *_result.tsv under OptiType/, or None."""
    if not optitype_dir.exists():
        return None
    cands = list(optitype_dir.rglob("*_result.tsv")) + list(optitype_dir.rglob("*_result"))
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)

def parse_optitype_result(tsv_path: Path):
    """
    Extract the 6 HLA alleles from an OptiType *_result(.tsv).
    Returns (A1,A2,B1,B2,C1,C2) or None if not found.
    """
    alleles = []
    with open(tsv_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            alleles.extend(ALLELE_RE.findall(line))
            if len(alleles) >= 6:
                break
    if len(alleles) < 6:
        # Fallback: try to parse as tabbed columns with headers A1..C2
        with open(tsv_path, 'r', encoding='utf-8', errors='ignore') as f:
            rows = [r.strip().split('\t') for r in f if r.strip()]
        if len(rows) >= 2:
            header = [h.strip() for h in rows[0]]
            data   = rows[1]
            want = ['A1','A2','B1','B2','C1','C2']
            vals = []
            for k in want:
                if k in header:
                    vals.append(data[header.index(k)])
            if len(vals) == 6:
                alleles = vals

    if len(alleles) < 6:
        return None

    # keep first 6 and add HLA- prefix if missing
    alleles = alleles[:6]
    alleles = [a if a.startswith('HLA-') else f'HLA-{a}' for a in alleles]
    return tuple(alleles)

def main():
    ap = argparse.ArgumentParser(description="Collect OptiType results into a sample × HLA table.")
    ap.add_argument("-r","--root", required=True,
                    help="Directory containing per-sample folders (each has OptiType/<run>/..._result.tsv).")
    ap.add_argument("-o","--out", default="optitype_summary.tsv", help="Output TSV filename.")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"Not a directory: {root}")

    rows = []
    for sample_dir in sorted([p for p in root.iterdir() if p.is_dir()]):
        opti = sample_dir / "OptiType"
        res  = newest_result(opti)
        if res is None:
            print(f"[WARN] No OptiType result found under {opti}", file=sys.stderr)
            continue

        alleles = parse_optitype_result(res)
        if alleles is None:
            print(f"[WARN] Could not parse 6 alleles from {res}", file=sys.stderr)
            continue

        A1,A2,B1,B2,C1,C2 = alleles
        hla_str = ",".join([A1,A2,B1,B2,C1,C2])
        rows.append({
            "sample": sample_dir.name,
            "A1": A1, "A2": A2, "B1": B1, "B2": B2, "C1": C1, "C2": C2,
            "hla": hla_str
        })

    if not rows:
        sys.exit("No parsable OptiType results found.")

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["sample","A1","A2","B1","B2","C1","C2","hla"], delimiter="\t")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"[OK] wrote {args.out} with {len(rows)} samples")

if __name__ == "__main__":
    main()
