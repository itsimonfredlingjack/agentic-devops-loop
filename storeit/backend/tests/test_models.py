"""Direct service-layer unit tests."""

import pytest
from sqlalchemy import select

from storeit.models.base import Base
from storeit.models.product import Product, ProductVariant


@pytest.mark.asyncio
async def test_all_tables_created(test_engine):
    """All expected tables exist in the in-memory DB."""
    async with test_engine.begin() as conn:
        table_names = await conn.run_sync(lambda sync_conn: set(Base.metadata.tables.keys()))
    expected = {
        "categories",
        "products",
        "product_variants",
        "inventory",
        "inventory_reservations",
        "carts",
        "cart_items",
        "orders",
        "order_items",
    }
    assert expected.issubset(table_names)


@pytest.mark.asyncio
async def test_product_variant_relationship(test_session, sample_product):
    """Product has variants relationship loaded correctly."""
    result = await test_session.execute(
        select(ProductVariant).where(ProductVariant.product_id == sample_product.id)
    )
    variants = result.scalars().all()
    assert len(variants) == 1
    assert variants[0].sku == "WM-001-BLK"


@pytest.mark.asyncio
async def test_category_product_relationship(test_session, sample_category, sample_product):
    """Category->Products relationship works."""
    result = await test_session.execute(
        select(Product).where(Product.category_id == sample_category.id)
    )
    products = result.scalars().all()
    assert len(products) == 1
    assert products[0].name == "Wireless Mouse"


@pytest.mark.asyncio
async def test_create_product_service(test_session):
    """product_service.create_product creates a product."""
    from storeit.schemas.product import ProductCreate
    from storeit.services.product_service import create_product

    result = await create_product(
        test_session,
        ProductCreate(name="Test Item", slug="test-item"),
    )
    assert result.name == "Test Item"
    assert result.slug == "test-item"
    assert result.is_active is True


@pytest.mark.asyncio
async def test_create_category_service(test_session):
    """product_service.create_category creates a category."""
    from storeit.schemas.product import CategoryCreate
    from storeit.services.product_service import create_category

    result = await create_category(
        test_session,
        CategoryCreate(name="Toys", slug="toys"),
    )
    assert result.name == "Toys"
    assert result.slug == "toys"


@pytest.mark.asyncio
async def test_duplicate_product_slug_service(test_session):
    """create_product raises ValueError on duplicate slug."""
    from storeit.schemas.product import ProductCreate
    from storeit.services.product_service import create_product

    await create_product(
        test_session,
        ProductCreate(name="A", slug="unique-slug"),
    )
    with pytest.raises(ValueError, match="already exists"):
        await create_product(
            test_session,
            ProductCreate(name="B", slug="unique-slug"),
        )


@pytest.mark.asyncio
async def test_order_state_machine_service(test_session, sample_variant):
    """Order state machine enforces valid transitions."""
    from storeit.models.order import Order, OrderItem, OrderStatus
    from storeit.services.order_service import transition_order

    order = Order(
        customer_email="sm@test.com",
        customer_name="State Machine",
        status=OrderStatus.pending,
        total_cents=10000,
    )
    test_session.add(order)
    await test_session.flush()

    # Add a dummy order item
    item = OrderItem(
        order_id=order.id,
        variant_id=sample_variant.id,
        product_name="Test",
        sku="TST",
        quantity=1,
        unit_price_cents=10000,
        line_total_cents=10000,
    )
    test_session.add(item)
    await test_session.flush()

    # Valid: pending -> paid
    result = await transition_order(test_session, order.id, "paid")
    assert result.status == "paid"

    # Invalid: paid -> delivered (must go through processing, shipped)
    with pytest.raises(ValueError, match="Cannot transition"):
        await transition_order(test_session, order.id, "delivered")
