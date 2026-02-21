"""Race condition tests using asyncio.gather + Barrier against real PostgreSQL.

These tests validate that SELECT FOR UPDATE prevents overselling.
They require a running PostgreSQL instance and are skipped in CI.

Run with:
    pytest tests/test_race_conditions.py -xvs
"""

import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from storeit.config import settings
from storeit.models.base import Base
from storeit.models.inventory import InventoryRecord
from storeit.models.product import Product, ProductVariant
from storeit.services.inventory_service import reserve_stock

# Skip entire module if PostgreSQL is not reachable
pytestmark = pytest.mark.postgres

PG_URL = settings.database_url


@pytest.fixture
async def pg_engine():
    """Real PostgreSQL engine — creates all tables, drops after test."""
    engine = create_async_engine(PG_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def pg_session_factory(pg_engine):
    """Session factory bound to the real PostgreSQL engine."""
    return async_sessionmaker(pg_engine, expire_on_commit=False)


@pytest.fixture
async def seeded_variant_1_stock(pg_session_factory) -> int:
    """Seed a product variant with exactly 1 unit in stock. Returns variant_id."""
    async with pg_session_factory() as session:
        product = Product(name="Last Widget", slug="last-widget")
        session.add(product)
        await session.flush()

        variant = ProductVariant(
            product_id=product.id,
            sku="LW-001",
            name="Default",
            price_cents=10000,
        )
        session.add(variant)
        await session.flush()

        inv = InventoryRecord(
            variant_id=variant.id,
            quantity_on_hand=1,
            quantity_reserved=0,
        )
        session.add(inv)
        await session.commit()
        return variant.id


@pytest.fixture
async def seeded_variant_5_stock(pg_session_factory) -> int:
    """Seed a product variant with 5 units in stock. Returns variant_id."""
    async with pg_session_factory() as session:
        product = Product(name="Limited Edition", slug="limited-edition")
        session.add(product)
        await session.flush()

        variant = ProductVariant(
            product_id=product.id,
            sku="LE-001",
            name="Default",
            price_cents=50000,
        )
        session.add(variant)
        await session.flush()

        inv = InventoryRecord(
            variant_id=variant.id,
            quantity_on_hand=5,
            quantity_reserved=0,
        )
        session.add(inv)
        await session.commit()
        return variant.id


# ────────────────────────────────────────────────
# Core race condition tests
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_two_buyers_one_stock(pg_session_factory, seeded_variant_1_stock):
    """Two concurrent reserve_stock calls for the last unit.

    Only one should succeed; the other must raise ValueError.
    PostgreSQL SELECT FOR UPDATE serializes the two transactions.
    """
    variant_id = seeded_variant_1_stock
    barrier = asyncio.Barrier(2)
    results: list[str] = []

    async def attempt_reserve(cart_id: str):
        async with pg_session_factory() as session:
            await barrier.wait()
            try:
                await reserve_stock(session, variant_id, 1, cart_id)
                await session.commit()
                results.append("success")
            except ValueError:
                results.append("failure")

    await asyncio.gather(
        attempt_reserve("cart-A"),
        attempt_reserve("cart-B"),
    )

    assert results.count("success") == 1
    assert results.count("failure") == 1

    # Verify DB state: on_hand=1, reserved=1
    async with pg_session_factory() as session:
        inv = await session.execute(
            select(InventoryRecord).where(InventoryRecord.variant_id == variant_id)
        )
        record = inv.scalar_one()
        assert record.quantity_on_hand == 1
        assert record.quantity_reserved == 1


@pytest.mark.asyncio
async def test_ten_buyers_one_stock(pg_session_factory, seeded_variant_1_stock):
    """10 concurrent buyers fight for the last item.

    Exactly 1 succeeds, 9 fail. This is THE defining test for
    inventory concurrency correctness.
    """
    variant_id = seeded_variant_1_stock
    barrier = asyncio.Barrier(10)
    results: list[str] = []

    async def attempt(cart_id: str):
        async with pg_session_factory() as session:
            await barrier.wait()
            try:
                await reserve_stock(session, variant_id, 1, cart_id)
                await session.commit()
                results.append("success")
            except ValueError:
                results.append("failure")

    await asyncio.gather(*(attempt(f"cart-{i}") for i in range(10)))

    assert results.count("success") == 1
    assert results.count("failure") == 9


@pytest.mark.asyncio
async def test_ten_buyers_five_stock(pg_session_factory, seeded_variant_5_stock):
    """10 concurrent buyers, 5 units available.

    Exactly 5 succeed, 5 fail.
    """
    variant_id = seeded_variant_5_stock
    barrier = asyncio.Barrier(10)
    results: list[str] = []

    async def attempt(cart_id: str):
        async with pg_session_factory() as session:
            await barrier.wait()
            try:
                await reserve_stock(session, variant_id, 1, cart_id)
                await session.commit()
                results.append("success")
            except ValueError:
                results.append("failure")

    await asyncio.gather(*(attempt(f"cart-{i}") for i in range(10)))

    assert results.count("success") == 5
    assert results.count("failure") == 5

    # Verify: on_hand=5, reserved=5, available=0
    async with pg_session_factory() as session:
        inv = await session.execute(
            select(InventoryRecord).where(InventoryRecord.variant_id == variant_id)
        )
        record = inv.scalar_one()
        assert record.quantity_on_hand == 5
        assert record.quantity_reserved == 5


@pytest.mark.asyncio
async def test_stock_never_goes_negative(pg_session_factory, seeded_variant_1_stock):
    """Even under heavy contention, stock can never go below zero."""
    variant_id = seeded_variant_1_stock
    barrier = asyncio.Barrier(20)
    successes = 0

    async def attempt(cart_id: str):
        nonlocal successes
        async with pg_session_factory() as session:
            await barrier.wait()
            try:
                await reserve_stock(session, variant_id, 1, cart_id)
                await session.commit()
                successes += 1
            except ValueError:
                pass

    await asyncio.gather(*(attempt(f"cart-{i}") for i in range(20)))

    assert successes == 1

    # The invariant: stock never negative
    async with pg_session_factory() as session:
        inv = await session.execute(
            select(InventoryRecord).where(InventoryRecord.variant_id == variant_id)
        )
        record = inv.scalar_one()
        available = record.quantity_on_hand - record.quantity_reserved
        assert available >= 0
