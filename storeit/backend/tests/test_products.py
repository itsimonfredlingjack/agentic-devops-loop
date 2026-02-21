"""Product, variant, and category API tests."""

import pytest

# ────────────────────────────────────────────────
# Categories
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_category(test_client):
    r = await test_client.post("/api/categories", json={"name": "Books", "slug": "books"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Books"
    assert data["slug"] == "books"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_category_duplicate_slug(test_client):
    await test_client.post("/api/categories", json={"name": "A", "slug": "dupe"})
    r = await test_client.post("/api/categories", json={"name": "B", "slug": "dupe"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_list_categories(test_client):
    await test_client.post("/api/categories", json={"name": "Cat A", "slug": "cat-a"})
    await test_client.post("/api/categories", json={"name": "Cat B", "slug": "cat-b"})
    r = await test_client.get("/api/categories")
    assert r.status_code == 200
    names = {c["name"] for c in r.json()}
    assert "Cat A" in names
    assert "Cat B" in names


@pytest.mark.asyncio
async def test_get_category_not_found(test_client):
    r = await test_client.get("/api/categories/9999")
    assert r.status_code == 404


# ────────────────────────────────────────────────
# Products
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_product(test_client):
    r = await test_client.post(
        "/api/products",
        json={"name": "Widget", "slug": "widget"},
    )
    assert r.status_code == 201
    assert r.json()["name"] == "Widget"
    assert r.json()["is_active"] is True


@pytest.mark.asyncio
async def test_create_product_duplicate_slug(test_client):
    await test_client.post("/api/products", json={"name": "A", "slug": "dupe-prod"})
    r = await test_client.post("/api/products", json={"name": "B", "slug": "dupe-prod"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_list_products(test_client):
    await test_client.post("/api/products", json={"name": "P1", "slug": "p1"})
    await test_client.post("/api/products", json={"name": "P2", "slug": "p2"})
    r = await test_client.get("/api/products")
    assert r.status_code == 200
    assert len(r.json()) >= 2


@pytest.mark.asyncio
async def test_get_product_with_variants(test_client):
    r = await test_client.post("/api/products", json={"name": "Phone", "slug": "phone"})
    product_id = r.json()["id"]

    await test_client.post(
        f"/api/products/{product_id}/variants",
        json={"sku": "PH-BLK", "name": "Black", "price_cents": 99900},
    )
    await test_client.post(
        f"/api/products/{product_id}/variants",
        json={"sku": "PH-WHT", "name": "White", "price_cents": 99900},
    )

    r = await test_client.get(f"/api/products/{product_id}")
    assert r.status_code == 200
    data = r.json()
    assert len(data["variants"]) == 2


@pytest.mark.asyncio
async def test_get_product_not_found(test_client):
    r = await test_client.get("/api/products/9999")
    assert r.status_code == 404


# ────────────────────────────────────────────────
# Variants
# ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_variant(test_client):
    r = await test_client.post("/api/products", json={"name": "Gadget", "slug": "gadget"})
    product_id = r.json()["id"]

    r = await test_client.post(
        f"/api/products/{product_id}/variants",
        json={"sku": "GDG-001", "name": "Standard", "price_cents": 49900},
    )
    assert r.status_code == 201
    assert r.json()["sku"] == "GDG-001"
    assert r.json()["price_cents"] == 49900


@pytest.mark.asyncio
async def test_create_variant_duplicate_sku(test_client):
    r = await test_client.post("/api/products", json={"name": "Thing", "slug": "thing"})
    pid = r.json()["id"]
    await test_client.post(
        f"/api/products/{pid}/variants",
        json={"sku": "DUPE-SKU", "name": "A", "price_cents": 1000},
    )
    r = await test_client.post(
        f"/api/products/{pid}/variants",
        json={"sku": "DUPE-SKU", "name": "B", "price_cents": 2000},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_variant_product_not_found(test_client):
    r = await test_client.post(
        "/api/products/9999/variants",
        json={"sku": "X", "name": "X", "price_cents": 100},
    )
    assert r.status_code == 404
