"""Run one complete audit against the built-in mock target and print the Markdown report.

    cd backend
    python scripts/demo_audit.py

No API key, no database server and no network access required.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MBA_DATABASE_URL", "sqlite+aiosqlite:///./demo_audit.db")

# There are no migrations yet (Alembic is planned work), so a database file left over from a
# build with a different schema fails with "no such column". This is a throwaway demo
# database, so the simplest correct behaviour is to start from an empty one every time.
Path("demo_audit.db").unlink(missing_ok=True)

from app.db.init import init_database
from app.db.session import SessionFactory
from app.schemas.audit import AuditCreate
from app.schemas.target import TargetCreate
from app.services import audit as audit_service
from app.services import report as report_service
from app.services import target as target_service


async def main() -> None:
    await init_database()
    async with SessionFactory() as session:
        target = await target_service.create_target(
            session,
            TargetCreate(name="Mock model", description="Offline stand-in", provider="mock", model_name="mock-model"),
        )
        audit = await audit_service.create_audit(
            session,
            AuditCreate(name="Demo fairness sweep", target_id=target.id, probe_ids=[]),
        )
        summary = await audit_service.run_audit(session, audit, target)
        report = await report_service.generate_report(session, audit, "markdown")

    print(f"probes run : {summary['probes_run']}")
    print(f"findings   : {summary['findings']}")
    print(f"max score  : {summary['highest_disparity']:.3f}")
    print()
    print(report.content)


if __name__ == "__main__":
    asyncio.run(main())
