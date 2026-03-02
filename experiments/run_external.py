from __future__ import annotations

import argparse

from oeg.adapters.webshop import convert_trace
from oeg.runners.external_runner import run_external


def main() -> None:
    ap = argparse.ArgumentParser(description="Run external OEG evaluation (e.g., WebShop).")
    ap.add_argument("--input", required=True, help="Path to external episodes JSONL")
    ap.add_argument("--tools", default="tools/tools_webshop.yaml")
    ap.add_argument("--out", default="runs/external_eval.jsonl")
    ap.add_argument("--mitigate", action="store_true")
    args = ap.parse_args()

    run_external(
        input_jsonl=args.input,
        tools_yaml=args.tools,
        out_jsonl=args.out,
        adapter=convert_trace,
        mitigate=args.mitigate,
    )


if __name__ == "__main__":
    main()