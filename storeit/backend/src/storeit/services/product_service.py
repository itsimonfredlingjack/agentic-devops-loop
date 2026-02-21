"""Product service -- CRUD for categories, products, and variants."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from storeit.models.product import Category, Product, ProductVariant
from storeit.schemas.product import (
    CategoryCreate,
    CategoryRead,
    ProductCreate,
    ProductRead,
    ProductWithVariants,
    VariantCreate,
    VariantRead,
)

# ────────────────────────────────────────────────
# Categories
# ────────────────────────────────────────────────


async def create_category(session: AsyncSession, payload: CategoryCreate) -> CategoryRead:
    """Create a category. Raises ValueError if slug is duplicate."""
    existing = await session.execute(select(Category).where(Category.slug == payload.slug))
    if existing.scalar_one_or_none() is not None:
        raise ValueError(f"Category slug '{payload.slug}' already exists")

    cat = Category(name=payload.name, slug=payload.slug, description=payload.description)
    session.add(cat)
    await session.flush()
    return CategoryRead.model_validate(cat)


async def list_categories(session: AsyncSession) -> list[CategoryRead]:
    """List all categories."""
    result = await session.execute(select(Category).order_by(Category.name))
    return [CategoryRead.model_validate(c) for c in result.scalars().all()]


async def get_category(session: AsyncSession, category_id: int) -> CategoryRead | None:
    """Get a category by ID."""
    cat = await session.get(Category, category_id)
    if cat is None:
        return None
    return CategoryRead.model_validate(cat)


# ────────────────────────────────────────────────
# Products
# ────────────────────────────────────────────────


async def create_product(session: AsyncSession, payload: ProductCreate) -> ProductRead:
    """Create a product. Raises ValueError if slug is duplicate."""
    existing = await session.execute(select(Product).where(Product.slug == payload.slug))
    if existing.scalar_one_or_none() is not None:
        raise ValueError(f"Product slug '{payload.slug}' already exists")

    product = Product(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        category_id=payload.category_id,
    )
    session.add(product)
    await session.flush()
    return ProductRead.model_validate(product)


async def list_products(session: AsyncSession) -> list[ProductRead]:
    """List all active products."""
    result = await session.execute(
        select(Product).where(Product.is_active.is_(True)).order_by(Product.name)
    )
    return [ProductRead.model_validate(p) for p in result.scalars().all()]


async def get_product(session: AsyncSession, product_id: int) -> ProductWithVariants | None:
    """Get a product by ID with its variants."""
    result = await session.execute(
        select(Product).where(Product.id == product_id).options(selectinload(Product.variants))
    )
    product = result.scalar_one_or_none()
    if product is None:
        return None
    return ProductWithVariants.model_validate(product)


# ────────────────────────────────────────────────
# Variants
# ────────────────────────────────────────────────


async def create_variant(
    session: AsyncSession, product_id: int, payload: VariantCreate
) -> VariantRead:
    """Create a variant for a product. Raises ValueError if product not found or SKU duplicate."""
    product = await session.get(Product, product_id)
    if product is None:
        raise ValueError(f"Product {product_id} not found")

    existing = await session.execute(
        select(ProductVariant).where(ProductVariant.sku == payload.sku)
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError(f"SKU '{payload.sku}' already exists")

    variant = ProductVariant(
        product_id=product_id,
        sku=payload.sku,
        name=payload.name,
        price_cents=payload.price_cents,
        weight_grams=payload.weight_grams,
    )
    session.add(variant)
    await session.flush()
    return VariantRead.model_validate(variant)
