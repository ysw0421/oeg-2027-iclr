from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from oeg.io import load_jsonl
from oeg.metrics import summarize


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare two runs and export a summary CSV.")
    ap.add_argument("--a", required=True, help="JSONL path A")
    ap.add_argument("--b", required=True, help="JSONL path B")
    ap.add_argument("--name_a", default="A")
    ap.add_argument("--name_b", default="B")
    ap.add_argument("--tau", type=float, default=0.5)
    ap.add_argument("--out", default="plots/compare_shift.csv")
    args = ap.parse_args()

    rows_a = load_jsonl(args.a)
    rows_b = load_jsonl(args.b)

    sa = summarize(rows_a, tau=float(args.tau))
    sb = summarize(rows_b, tau=float(args.tau))

    sa["name"] = args.name_a
    sb["name"] = args.name_b

    df = pd.DataFrame([sa, sb])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(df)
    print("saved:", args.out)


if __name__ == "__main__":
    main()