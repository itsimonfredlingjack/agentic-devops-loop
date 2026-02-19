"""Seed the database with demo data.

Creates a demo tenant "Klipp & Trim" with services and slots for the
next 7 days.  Safe to run multiple times — uses INSERT OR IGNORE for
the tenant and checks for existing slots.

Usage:
    cd bookit/backend
    source venv/bin/activate
    python -m scripts.seed
"""

import asyncio
from datetime import datetime, timedelta

import aiosqlite

from src.bookit.config import settings
from src.bookit.database import init_db

TENANT_NAME = "Klipp & Trim"
TENANT_SLUG = "klipp-trim"

SERVICES = [
    {"name": "Herrklippning", "duration_min": 30, "capacity": 1},
    {"name": "Damklippning", "duration_min": 60, "capacity": 1},
    {"name": "Färgning", "duration_min": 90, "capacity": 2},
    {"name": "Skäggtrimning", "duration_min": 20, "capacity": 1},
]

# Generate slots 08:00-17:00 for the next 7 days
DAYS_AHEAD = 7
START_HOUR = 8
END_HOUR = 17


async def seed() -> None:
    """Populate the database with demo data."""
    await init_db()

    async with aiosqlite.connect(settings.database_url) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")

        # Create tenant
        await db.execute(
            "INSERT OR IGNORE INTO tenants (name, slug) VALUES (?, ?)",
            (TENANT_NAME, TENANT_SLUG),
        )
        row = await db.execute("SELECT id FROM tenants WHERE slug = ?", (TENANT_SLUG,))
        tenant = await row.fetchone()
        assert tenant is not None
        tenant_id = tenant["id"]
        print(f"Tenant: {TENANT_NAME} (id={tenant_id})")

        # Create services
        service_ids: dict[str, int] = {}
        for svc in SERVICES:
            await db.execute(
                """INSERT OR IGNORE INTO services (tenant_id, name, duration_min, capacity)
                   SELECT ?, ?, ?, ?
                   WHERE NOT EXISTS (
                       SELECT 1 FROM services WHERE tenant_id = ? AND name = ?
                   )""",
                (
                    tenant_id,
                    svc["name"],
                    svc["duration_min"],
                    svc["capacity"],
                    tenant_id,
                    svc["name"],
                ),
            )
            row = await db.execute(
                "SELECT id FROM services WHERE tenant_id = ? AND name = ?",
                (tenant_id, svc["name"]),
            )
            result = await row.fetchone()
            assert result is not None
            service_ids[svc["name"]] = result["id"]
            print(f"  Service: {svc['name']} (id={result['id']})")

        # Generate slots for each service for the next 7 days
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        slot_count = 0

        for svc in SERVICES:
            svc_id = service_ids[svc["name"]]
            duration = svc["duration_min"]

            for day_offset in range(DAYS_AHEAD):
                day = today + timedelta(days=day_offset)
                # Skip weekends
                if day.weekday() >= 5:
                    continue

                hour = START_HOUR
                minute = 0
                while True:
                    start = day.replace(hour=hour, minute=minute)
                    end = start + timedelta(minutes=duration)
                    if end.hour > END_HOUR or (end.hour == END_HOUR and end.minute > 0):
                        break

                    start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
                    end_str = end.strftime("%Y-%m-%dT%H:%M:%S")

                    # Check if slot already exists
                    existing = await db.execute(
                        "SELECT id FROM slots WHERE service_id = ? AND start_time = ?",
                        (svc_id, start_str),
                    )
                    if await existing.fetchone() is None:
                        await db.execute(
                            """INSERT INTO slots (service_id, start_time, end_time, capacity)
                               VALUES (?, ?, ?, ?)""",
                            (svc_id, start_str, end_str, svc["capacity"]),
                        )
                        slot_count += 1

                    # Advance to next slot
                    total_min = hour * 60 + minute + duration
                    hour = total_min // 60
                    minute = total_min % 60

        await db.commit()
        print(f"  Created {slot_count} new slots across {DAYS_AHEAD} days")

    # Also create the "demo" tenant for the frontend default
    async with aiosqlite.connect(settings.database_url) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT OR IGNORE INTO tenants (name, slug) VALUES (?, ?)",
            ("Demo Salong", "demo"),
        )
        row = await db.execute("SELECT id FROM tenants WHERE slug = ?", ("demo",))
        demo = await row.fetchone()
        assert demo is not None
        demo_id = demo["id"]

        # Add same services to demo tenant
        for svc in SERVICES:
            await db.execute(
                """INSERT OR IGNORE INTO services (tenant_id, name, duration_min, capacity)
                   SELECT ?, ?, ?, ?
                   WHERE NOT EXISTS (
                       SELECT 1 FROM services WHERE tenant_id = ? AND name = ?
                   )""",
                (demo_id, svc["name"], svc["duration_min"], svc["capacity"], demo_id, svc["name"]),
            )

        # Generate slots for demo tenant too
        demo_slot_count = 0
        for svc in SERVICES:
            row = await db.execute(
                "SELECT id FROM services WHERE tenant_id = ? AND name = ?",
                (demo_id, svc["name"]),
            )
            result = await row.fetchone()
            assert result is not None
            svc_id = result["id"]
            duration = svc["duration_min"]

            for day_offset in range(DAYS_AHEAD):
                day = today + timedelta(days=day_offset)
                if day.weekday() >= 5:
                    continue

                hour = START_HOUR
                minute = 0
                while True:
                    start = day.replace(hour=hour, minute=minute)
                    end = start + timedelta(minutes=duration)
                    if end.hour > END_HOUR or (end.hour == END_HOUR and end.minute > 0):
                        break

                    start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
                    end_str = end.strftime("%Y-%m-%dT%H:%M:%S")

                    existing = await db.execute(
                        "SELECT id FROM slots WHERE service_id = ? AND start_time = ?",
                        (svc_id, start_str),
                    )
                    if await existing.fetchone() is None:
                        await db.execute(
                            """INSERT INTO slots (service_id, start_time, end_time, capacity)
                               VALUES (?, ?, ?, ?)""",
                            (svc_id, start_str, end_str, svc["capacity"]),
                        )
                        demo_slot_count += 1

                    total_min = hour * 60 + minute + duration
                    hour = total_min // 60
                    minute = total_min % 60

        await db.commit()
        print(f"  Demo tenant: Demo Salong (id={demo_id})")
        print(f"  Created {demo_slot_count} new demo slots")

    print("\nSeed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
