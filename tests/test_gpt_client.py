import sys
import os
import pytest
import asyncio
from typing import Dict
from core.gpt_client import GPTClient
from config.settings import settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
async def gpt_client():
    """Fixture to create a GPT client instance."""
    client = GPTClient()
    return client

@pytest.fixture
def test_market_data():
    """Fixture to create test market data."""
    return {
        "id": "test-market-id",
        "question": "Will the S&P 500 close above 5000 by end of Q1 2024?",
        "description": "This market resolves YES if the S&P 500 index closes above 5000 at any point before March 31, 2024.",
        "probability": 0.65,
        "closeTime": 1711843200000  # March 31, 2024
    }

@pytest.mark.asyncio
async def test_analyze_market(gpt_client, test_market_data):
    """Test market analysis with search capabilities."""
    result = await gpt_client.analyze_market(test_market_data)
    
    # Verify basic structure
    assert isinstance(result, dict)
    assert 'estimated_probability' in result
    assert 'confidence_level' in result
    assert 'sources' in result
    assert 'research_findings' in result
    
    # Verify probability constraints
    assert 0 <= result['estimated_probability'] <= 1
    assert 0 <= result['confidence_level'] <= 1
    
    # Verify search results
    assert len(result['sources']) >= 1
    assert len(result['research_findings']) >= 1
    
    # Verify source structure
    for source in result['sources']:
        assert isinstance(source, dict)
        assert 'url' in source
        assert 'credibility' in source
        assert 0 <= source['credibility'] <= 1

@pytest.mark.asyncio
async def test_source_validation(gpt_client):
    """Test source validation capabilities."""
    test_sources = [
        {"url": "https://www.reuters.com/test", "type": "NEWS"},
        {"url": "https://twitter.com/test", "type": "SOCIAL"}
    ]
    
    result = await gpt_client.validate_sources(test_sources)
    
    assert isinstance(result, dict)
    assert 'validated_sources' in result
    assert len(result['validated_sources']) == len(test_sources)
    
    for source in result['validated_sources']:
        assert 'credibility' in source
        assert 'recommendation' in source

@pytest.mark.asyncio
async def test_rate_limiting(gpt_client, test_market_data):
    """Test rate limiting behavior."""
    # Make multiple rapid requests
    results = await asyncio.gather(
        *[gpt_client.analyze_market(test_market_data) for _ in range(3)],
        return_exceptions=True
    )
    
    # Verify some requests were rate limited
    assert any(isinstance(r, Exception) for r in results)
    assert any('rate_limit' in str(r) for r in results if isinstance(r, Exception))

@pytest.mark.asyncio
async def test_error_handling(gpt_client):
    """Test error handling for invalid inputs."""
    invalid_market = {"id": "test"}  # Missing required fields
    
    with pytest.raises(Exception) as exc_info:
        await gpt_client.analyze_market(invalid_market)
    
    assert "Invalid market data" in str(exc_info.value)

def test_config_validation():
    """Test configuration validation."""
    assert settings.MAX_SEARCH_RESULTS > 0
    assert 0 < settings.MIN_SOURCE_CREDIBILITY <= 1
    assert settings.SEARCH_TIMEOUT > 0
    
    # Verify source type weights
    for source_type, weight in settings.SOURCE_TYPES.items():
        assert 0 <= weight <= 1

if __name__ == "__main__":
    pytest.main(["-v", "test_gpt_client.py"])