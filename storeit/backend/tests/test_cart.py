"""Cart API tests."""

import pytest


@pytest.mark.asyncio
async def test_get_cart_not_found(test_client):
    r = await test_client.get("/api/cart/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_add_item_to_cart(test_client, sample_variant):
    """POST /api/cart/{session_id}/items adds item and creates cart."""
    r = await test_client.post(
        "/api/cart/my-session/items",
        json={"variant_id": sample_variant.id, "quantity": 2},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["session_id"] == "my-session"
    assert len(data["items"]) == 1
    assert data["items"][0]["variant_id"] == sample_variant.id
    assert data["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_add_item_merges_quantity(test_client, sample_variant):
    """Adding same variant twice merges quantities."""
    await test_client.post(
        "/api/cart/merge-session/items",
        json={"variant_id": sample_variant.id, "quantity": 3},
    )
    r = await test_client.post(
        "/api/cart/merge-session/items",
        json={"variant_id": sample_variant.id, "quantity": 2},
    )
    assert r.status_code == 201
    assert r.json()["items"][0]["quantity"] == 5


@pytest.mark.asyncio
async def test_add_item_variant_not_found(test_client):
    r = await test_client.post(
        "/api/cart/bad-session/items",
        json={"variant_id": 9999, "quantity": 1},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_cart(test_client, sample_variant):
    """GET /api/cart/{session_id} returns cart with items."""
    await test_client.post(
        "/api/cart/get-session/items",
        json={"variant_id": sample_variant.id, "quantity": 1},
    )
    r = await test_client.get("/api/cart/get-session")
    assert r.status_code == 200
    assert len(r.json()["items"]) == 1


@pytest.mark.asyncio
async def test_update_cart_item(test_client, sample_variant):
    """PATCH /api/cart/{session_id}/items/{id} updates quantity."""
    r = await test_client.post(
        "/api/cart/update-session/items",
        json={"variant_id": sample_variant.id, "quantity": 1},
    )
    item_id = r.json()["items"][0]["id"]

    r = await test_client.patch(
        f"/api/cart/update-session/items/{item_id}",
        json={"quantity": 10},
    )
    assert r.status_code == 200
    assert r.json()["items"][0]["quantity"] == 10


@pytest.mark.asyncio
async def test_remove_cart_item(test_client, sample_variant):
    """DELETE /api/cart/{session_id}/items/{id} removes item."""
    r = await test_client.post(
        "/api/cart/remove-session/items",
        json={"variant_id": sample_variant.id, "quantity": 1},
    )
    item_id = r.json()["items"][0]["id"]

    r = await test_client.delete(f"/api/cart/remove-session/items/{item_id}")
    assert r.status_code == 200
    assert len(r.json()["items"]) == 0
