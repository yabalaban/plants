import pytest


@pytest.mark.asyncio
async def test_list_plants_empty(client):
    resp = await client.get("/api/plants")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_add_plant(client, sample_photo):
    with open(sample_photo, "rb") as f:
        resp = await client.post(
            "/api/plants",
            data={"name": "My Monstera"},
            files={"photo": ("plant.jpg", f, "image/jpeg")},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Monstera"
    assert data["id"] == 1
    assert data["species"] is None


@pytest.mark.asyncio
async def test_get_plant_detail(client, sample_photo):
    with open(sample_photo, "rb") as f:
        await client.post(
            "/api/plants",
            data={"name": "My Fern"},
            files={"photo": ("fern.jpg", f, "image/jpeg")},
        )
    resp = await client.get("/api/plants/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "My Fern"
    assert data["watering_logs"] == []


@pytest.mark.asyncio
async def test_get_plant_not_found(client):
    resp = await client.get("/api/plants/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_plant(client, sample_photo):
    with open(sample_photo, "rb") as f:
        await client.post(
            "/api/plants",
            data={"name": "Doomed Plant"},
            files={"photo": ("plant.jpg", f, "image/jpeg")},
        )
    resp = await client.delete("/api/plants/1")
    assert resp.status_code == 204
    resp = await client.get("/api/plants")
    assert resp.json() == []


@pytest.mark.asyncio
async def test_water_plant(client, sample_photo):
    with open(sample_photo, "rb") as f:
        await client.post(
            "/api/plants",
            data={"name": "Thirsty Plant"},
            files={"photo": ("plant.jpg", f, "image/jpeg")},
        )
    resp = await client.post("/api/plants/1/water", json={"notes": "Looked dry"})
    assert resp.status_code == 201
    resp = await client.get("/api/plants/1")
    assert len(resp.json()["watering_logs"]) == 1
    assert resp.json()["watering_logs"][0]["notes"] == "Looked dry"
