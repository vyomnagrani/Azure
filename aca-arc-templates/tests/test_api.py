import pytest


@pytest.mark.asyncio
async def test_health_endpoints(client):
    live = await client.get("/health/live")
    ready = await client.get("/health/ready")

    assert live.status_code == 200
    assert live.json() == {"status": "ok"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_seed_inventory_is_deterministic(client):
    response = await client.get("/api/inventory")

    assert response.status_code == 200
    assert [item["sku"] for item in response.json()] == [
        "EDGE-CAM-01",
        "EDGE-GW-02",
        "EDGE-SCAN-03",
        "EDGE-TAG-04",
    ]
    assert [item["quantity"] for item in response.json()] == [12, 2, 0, 4]


@pytest.mark.asyncio
async def test_successful_adjustment_changes_summary(client):
    before = (await client.get("/api/inventory/summary")).json()
    response = await client.post(
        "/api/inventory/EDGE-TAG-04/adjust",
        json={"quantity_delta": 3},
    )
    after = (await client.get("/api/inventory/summary")).json()

    assert response.status_code == 200
    assert response.json()["quantity"] == 7
    assert response.json()["status"] == "in_stock"
    assert after["total_units"] == before["total_units"] + 3
    assert after["inventory_value_cents"] == (
        before["inventory_value_cents"] + 3 * 4900
    )
    assert after["low_stock_items"] == before["low_stock_items"] - 1


@pytest.mark.asyncio
@pytest.mark.parametrize("quantity_delta", [0, 1001, -1001, "not-a-number"])
async def test_invalid_adjustment_is_rejected(client, quantity_delta):
    response = await client.post(
        "/api/inventory/EDGE-CAM-01/adjust",
        json={"quantity_delta": quantity_delta},
    )

    assert response.status_code == 422
    item = (await client.get("/api/inventory/EDGE-CAM-01")).json()
    assert item["quantity"] == 12


@pytest.mark.asyncio
async def test_unknown_item_returns_not_found(client):
    get_response = await client.get("/api/inventory/DOES-NOT-EXIST")
    adjust_response = await client.post(
        "/api/inventory/DOES-NOT-EXIST/adjust",
        json={"quantity_delta": 1},
    )

    assert get_response.status_code == 404
    assert adjust_response.status_code == 404


@pytest.mark.asyncio
async def test_insufficient_stock_returns_conflict_without_mutation(client):
    response = await client.post(
        "/api/inventory/EDGE-GW-02/adjust",
        json={"quantity_delta": -3},
    )

    assert response.status_code == 409
    item = (await client.get("/api/inventory/EDGE-GW-02")).json()
    assert item["quantity"] == 2


@pytest.mark.asyncio
async def test_each_client_starts_with_seed_state(client):
    response = await client.get("/api/inventory/EDGE-TAG-04")
    assert response.json()["quantity"] == 4


@pytest.mark.asyncio
async def test_dashboard_is_served(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Contoso Edge Store" in response.text
    assert "/api/inventory/summary" in response.text
    assert "Educational milestone" in response.text

