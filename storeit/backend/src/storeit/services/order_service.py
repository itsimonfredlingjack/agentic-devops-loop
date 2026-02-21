"""Order service -- cart-to-order conversion and state machine."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from storeit.models.cart import Cart
from storeit.models.order import ORDER_TRANSITIONS, Order, OrderItem, OrderStatus
from storeit.models.product import ProductVariant
from storeit.schemas.order import OrderCreate, OrderRead
from storeit.services import inventory_service


async def create_order(session: AsyncSession, payload: OrderCreate) -> OrderRead:
    """Convert a cart into an order with inventory reservation.

    For each cart item:
    1. Lock inventory (SELECT FOR UPDATE via reserve_stock)
    2. Create order + order_items with snapshotted price data
    3. Clear cart items

    Raises ValueError on empty cart or insufficient stock.
    """
    result = await session.execute(
        select(Cart)
        .where(Cart.session_id == payload.cart_session_id)
        .options(selectinload(Cart.items))
    )
    cart = result.scalar_one_or_none()
    if cart is None or not cart.items:
        raise ValueError("Cart is empty or not found")

    order = Order(
        customer_email=payload.customer_email,
        customer_name=payload.customer_name,
        status=OrderStatus.pending,
    )
    session.add(order)
    await session.flush()

    # Use order ID as reservation key so fulfill_checkout can find them
    reservation_key = f"order-{order.id}"

    total_cents = 0
    for cart_item in cart.items:
        # Reserve stock (SELECT FOR UPDATE under the hood)
        await inventory_service.reserve_stock(
            session, cart_item.variant_id, cart_item.quantity, reservation_key
        )

        variant = await session.get(ProductVariant, cart_item.variant_id)
        if variant is None:
            raise ValueError(f"Variant {cart_item.variant_id} not found")
        line_total = variant.price_cents * cart_item.quantity

        order_item = OrderItem(
            order_id=order.id,
            variant_id=cart_item.variant_id,
            product_name=variant.name,
            sku=variant.sku,
            quantity=cart_item.quantity,
            unit_price_cents=variant.price_cents,
            line_total_cents=line_total,
        )
        session.add(order_item)
        total_cents += line_total

    order.total_cents = total_cents

    # Clear cart
    for item in cart.items:
        await session.delete(item)

    await session.flush()

    return await get_order(session, order.id)


async def get_order(session: AsyncSession, order_id: int) -> OrderRead | None:
    """Get an order by ID with items."""
    result = await session.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        return None
    return OrderRead.model_validate(order)


async def list_orders(session: AsyncSession, customer_email: str | None = None) -> list[OrderRead]:
    """List orders, optionally filtered by email."""
    stmt = select(Order).options(selectinload(Order.items)).order_by(Order.id.desc())
    if customer_email:
        stmt = stmt.where(Order.customer_email == customer_email)
    result = await session.execute(stmt)
    return [OrderRead.model_validate(o) for o in result.scalars().all()]


async def transition_order(session: AsyncSession, order_id: int, new_status_str: str) -> OrderRead:
    """Advance order to a new status, enforcing the state machine.

    On cancellation of a pending order, releases inventory reservations.
    Raises ValueError if order not found or transition not allowed.
    """
    result = await session.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise ValueError(f"Order {order_id} not found")

    try:
        new_status = OrderStatus(new_status_str)
    except ValueError:
        raise ValueError(f"Invalid status: {new_status_str}") from None

    current = OrderStatus(order.status)
    allowed = ORDER_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition order {order_id} from {current} to {new_status}. "
            f"Allowed: {sorted(s.value for s in allowed)}"
        )

    # On cancellation of a pending order, cancel actual reservations
    if new_status == OrderStatus.cancelled and current == OrderStatus.pending:
        from storeit.models.inventory import InventoryReservation

        reservation_key = f"order-{order.id}"
        res_result = await session.execute(
            select(InventoryReservation).where(
                InventoryReservation.cart_id == reservation_key,
                InventoryReservation.status == "active",
            )
        )
        for reservation in res_result.scalars().all():
            await inventory_service.cancel_reservation(session, reservation.id)

    order.status = new_status.value
    await session.flush()
    return OrderRead.model_validate(order)
