"""Portable local evaluation commands; never interacts with devices."""

import argparse
import json
import sys
from pathlib import Path

from .audit import audit
from .campaign import run
from .evidence import verify_manifest


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ix-symmetrylock")
    sub = parser.add_subparsers(dest="command", required=True)
    poc = sub.add_parser("poc", help="execute the explicit-coil correction campaign")
    poc.add_argument("--config", type=Path, default=Path("configs/poc.json"))
    poc.add_argument("--output", type=Path, default=Path("results/local"))
    verify = sub.add_parser("verify", help="verify an unsigned output integrity manifest")
    verify.add_argument("bundle", type=Path)
    audit_parser = sub.add_parser("audit", help="recompute archived fields, metrics and gates")
    audit_parser.add_argument("bundle", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "poc":
            result = run(args.config, args.output)
            print(
                json.dumps(
                    {
                        "cases": [
                            {
                                "name": c["name"],
                                "screen_pass": c["local_field_screen_pass"],
                                "validation_normal_rms": c["validation_after"][
                                    "normal_rms_over_B0"
                                ],
                                "validation_geometric_strength_rms": c["validation_after"][
                                    "geometric_strength_variation_rms_over_B0"
                                ],
                            }
                            for c in result["cases"]
                        ],
                        "reactor_promoted": False,
                    },
                    indent=2,
                )
            )
        elif args.command == "audit":
            print(json.dumps(audit(args.bundle), indent=2))
        else:
            manifest = json.loads((args.bundle / "manifest.json").read_text())
            count = verify_manifest(args.bundle, manifest)
            print(
                json.dumps(
                    {
                        "integrity_verified_files": count,
                        "authentication": "UNSIGNED_FILE_INTEGRITY_ONLY",
                    }
                )
            )
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"ix-symmetrylock: {exc}", file=sys.stderr)
        return 2
    return 0
