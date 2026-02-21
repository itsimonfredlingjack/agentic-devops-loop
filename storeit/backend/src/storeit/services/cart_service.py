"""Cart service -- session-based shopping cart."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from storeit.models.cart import Cart, CartItem
from storeit.models.product import ProductVariant
from storeit.schemas.cart import CartItemAdd, CartRead


async def get_or_create_cart(session: AsyncSession, session_id: str) -> Cart:
    """Get existing cart or create a new one."""
    result = await session.execute(
        select(Cart).where(Cart.session_id == session_id).options(selectinload(Cart.items))
    )
    cart = result.scalar_one_or_none()
    if cart is None:
        cart = Cart(session_id=session_id)
        session.add(cart)
        await session.flush()
        # Re-fetch with eager load to avoid lazy-load in async context
        result = await session.execute(
            select(Cart).where(Cart.id == cart.id).options(selectinload(Cart.items))
        )
        cart = result.scalar_one()
    return cart


async def get_cart(session: AsyncSession, session_id: str) -> CartRead | None:
    """Get a cart by session ID. Returns None if not found."""
    result = await session.execute(
        select(Cart).where(Cart.session_id == session_id).options(selectinload(Cart.items))
    )
    cart = result.scalar_one_or_none()
    if cart is None:
        return None
    return CartRead.model_validate(cart)


async def add_item(session: AsyncSession, session_id: str, payload: CartItemAdd) -> CartRead:
    """Add an item to cart. Merges quantity if variant already in cart.

    Raises ValueError if variant not found.
    """
    variant = await session.get(ProductVariant, payload.variant_id)
    if variant is None:
        raise ValueError(f"Variant {payload.variant_id} not found")

    cart = await get_or_create_cart(session, session_id)

    # Check if variant already in cart
    existing_item = None
    for item in cart.items:
        if item.variant_id == payload.variant_id:
            existing_item = item
            break

    if existing_item is not None:
        existing_item.quantity += payload.quantity
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            variant_id=payload.variant_id,
            quantity=payload.quantity,
        )
        session.add(cart_item)

    await session.flush()

    # Refresh cart with items to pick up new/updated items
    await session.refresh(cart, ["items"])
    return CartRead.model_validate(cart)


async def update_item(
    session: AsyncSession, session_id: str, item_id: int, quantity: int
) -> CartRead:
    """Update a cart item's quantity. Raises ValueError if not found."""
    result = await session.execute(
        select(Cart).where(Cart.session_id == session_id).options(selectinload(Cart.items))
    )
    cart = result.scalar_one_or_none()
    if cart is None:
        raise ValueError("Cart not found")

    target = None
    for item in cart.items:
        if item.id == item_id:
            target = item
            break

    if target is None:
        raise ValueError(f"Cart item {item_id} not found")

    target.quantity = quantity
    await session.flush()
    await session.refresh(cart, ["items"])
    return CartRead.model_validate(cart)


async def remove_item(session: AsyncSession, session_id: str, item_id: int) -> CartRead:
    """Remove an item from cart. Raises ValueError if not found."""
    result = await session.execute(
        select(Cart).where(Cart.session_id == session_id).options(selectinload(Cart.items))
    )
    cart = result.scalar_one_or_none()
    if cart is None:
        raise ValueError("Cart not found")

    target = None
    for item in cart.items:
        if item.id == item_id:
            target = item
            break

    if target is None:
        raise ValueError(f"Cart item {item_id} not found")

    await session.delete(target)
    await session.flush()
    await session.refresh(cart, ["items"])
    return CartRead.model_validate(cart)
