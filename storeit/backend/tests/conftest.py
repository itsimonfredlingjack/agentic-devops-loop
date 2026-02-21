"""Shared pytest fixtures for StoreIt backend tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from storeit.models.base import Base
from storeit.models.cart import Cart, CartItem  # noqa: F401 (ensure tables registered)
from storeit.models.inventory import InventoryRecord, InventoryReservation  # noqa: F401
from storeit.models.order import Order, OrderItem  # noqa: F401
from storeit.models.product import Category, Product, ProductVariant  # noqa: F401

# ────────────────────────────────────────────────
# In-memory SQLite engine + session
# ────────────────────────────────────────────────


@pytest.fixture
async def test_engine():
    """Create an in-memory SQLite async engine with all tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Yield an AsyncSession against the in-memory DB."""
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


# ────────────────────────────────────────────────
# HTTP client with dependency override
# ────────────────────────────────────────────────


@pytest.fixture
async def test_client(test_session):
    """AsyncClient wired to the FastAPI app with the in-memory DB injected."""
    from storeit.main import app
    from storeit.routers.cart import get_db_dep as cart_dep
    from storeit.routers.categories import get_db_dep as categories_dep
    from storeit.routers.inventory import get_db_dep as inventory_dep
    from storeit.routers.orders import get_db_dep as orders_dep
    from storeit.routers.products import get_db_dep as products_dep

    async def override_db():
        yield test_session

    app.dependency_overrides[products_dep] = override_db
    app.dependency_overrides[categories_dep] = override_db
    app.dependency_overrides[inventory_dep] = override_db
    app.dependency_overrides[cart_dep] = override_db
    app.dependency_overrides[orders_dep] = override_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ────────────────────────────────────────────────
# Domain object fixtures
# ────────────────────────────────────────────────


@pytest.fixture
async def sample_category(test_session):
    """Insert a sample category."""
    cat = Category(name="Electronics", slug="electronics", description="Electronic goods")
    test_session.add(cat)
    await test_session.flush()
    return cat


@pytest.fixture
async def sample_product(test_session, sample_category):
    """Insert a sample product with one variant and inventory."""
    product = Product(
        name="Wireless Mouse",
        slug="wireless-mouse",
        category_id=sample_category.id,
    )
    test_session.add(product)
    await test_session.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku="WM-001-BLK",
        name="Black",
        price_cents=29900,
    )
    test_session.add(variant)
    await test_session.flush()

    inv = InventoryRecord(variant_id=variant.id, quantity_on_hand=50, quantity_reserved=0)
    test_session.add(inv)
    await test_session.flush()

    return product


@pytest.fixture
async def sample_variant(test_session, sample_product):
    """Return the first variant of sample_product."""
    from sqlalchemy import select

    result = await test_session.execute(
        select(ProductVariant).where(ProductVariant.product_id == sample_product.id)
    )
    return result.scalar_one()


@pytest.fixture
async def sample_cart(test_session):
    """Create an empty cart."""
    cart_obj = Cart(session_id="test-session-123")
    test_session.add(cart_obj)
    await test_session.flush()
    return cart_obj
