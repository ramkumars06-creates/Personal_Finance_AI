"""
Tests for LLMGateway multi-model support (NVIDIA Nemotron, Gemini, and fallback).
"""
import pytest
from unittest.mock import patch, MagicMock
from app.llm.gateway import LLMGateway


def test_llm_gateway_fallback_when_no_keys():
    """Verify gateway defaults to deterministic rule engine when keys are absent."""
    gateway = LLMGateway()
    res = gateway.categorize_merchant("Swiggy Order #1234")
    assert res["category"] == "food"
    assert res["method"] == "rule"

    advice = gateway.generate_weekly_explanation(
        total_spend=1500.0,
        top_category="food",
        top_category_spend=800.0,
        overbudget_summary="food exceeded by Rs. 200",
        recommendations_text="Reduce food delivery"
    )
    assert "explanation" in advice
    assert advice["method"] == "template_fallback"


def test_nemotron_call_parsing():
    """Verify Nemotron responses with markdown fences are correctly parsed."""
    gateway = LLMGateway()
    gateway.active_provider = "nemotron"
    gateway.nvidia_api_key = "nvapi-test-key"

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '```json\n{"category": "transport", "confidence": 0.95, "reason": "Ride hailing service"}\n```'
                }
            }
        ]
    }

    with patch("httpx.post", return_value=mock_resp):
        res = gateway.categorize_merchant("Uber Trip Bangalore")
        assert res["category"] == "transport"
        assert res["confidence"] == 0.95
        assert res["method"] == "llm_nemotron"
