import json
import pytest
from unittest.mock import AsyncMock, patch
from app.services.claude import identify_plant, adjust_schedules

MOCK_IDENTIFICATION = {
    "species": "Monstera deliciosa",
    "confidence": "high",
    "care_summary": "Tropical plant that likes indirect light and moderate watering.",
    "light_preference": "bright indirect",
    "base_watering_interval_days": 7,
    "overwatering_signs": "Yellow leaves, mushy stems",
    "underwatering_signs": "Brown crispy leaf edges, drooping"
}

@pytest.mark.asyncio
async def test_identify_plant_parses_json():
    mock_result = json.dumps(MOCK_IDENTIFICATION)
    with patch("app.services.claude._run_claude_cli", return_value=mock_result):
        result = await identify_plant("/tmp/photo.jpg")
    assert result["species"] == "Monstera deliciosa"
    assert result["base_watering_interval_days"] == 7

@pytest.mark.asyncio
async def test_identify_plant_handles_markdown_fenced_json():
    mock_result = f"```json\n{json.dumps(MOCK_IDENTIFICATION)}\n```"
    with patch("app.services.claude._run_claude_cli", return_value=mock_result):
        result = await identify_plant("/tmp/photo.jpg")
    assert result["species"] == "Monstera deliciosa"

@pytest.mark.asyncio
async def test_identify_plant_returns_none_on_failure():
    with patch("app.services.claude._run_claude_cli", side_effect=RuntimeError("CLI failed")):
        result = await identify_plant("/tmp/photo.jpg")
    assert result is None

@pytest.mark.asyncio
async def test_adjust_schedules_returns_adjustments():
    mock_response = json.dumps([
        {"plant_id": 1, "interval_days": 5, "reason": "Hot weather this week"}
    ])
    with patch("app.services.claude._run_claude_cli", return_value=mock_response):
        result = await adjust_schedules(
            plants=[{"id": 1, "species": "Monstera", "interval_days": 7}],
            weather=[{"date": "2026-03-15", "temp_high": 32, "humidity": 40}],
        )
    assert len(result) == 1
    assert result[0]["interval_days"] == 5
