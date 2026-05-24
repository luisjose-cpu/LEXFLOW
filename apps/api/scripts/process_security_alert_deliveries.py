from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.database import SessionLocal
from app.services.security_alerts import security_alert_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process pending LEXFLOW security alert deliveries.")
    parser.add_argument("--scope", choices=["tenant", "owner"], default=None, help="Optional delivery scope to process.")
    parser.add_argument("--tenant-id", default=None, help="Optional tenant id when processing tenant deliveries.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum deliveries to process in this run.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.tenant_id and args.scope != "tenant":
        raise RuntimeError("--tenant-id can only be used with --scope tenant")
    if args.limit < 1 or args.limit > 500:
        raise RuntimeError("--limit must be between 1 and 500")

    with SessionLocal() as db:
        result = security_alert_service.process_pending_deliveries(
            db,
            scope=args.scope,
            tenant_id=args.tenant_id,
            limit=args.limit,
        )
        db.commit()

    print(f"Security alert deliveries processed: {result['processed']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Security alert delivery processing failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
