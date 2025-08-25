"""Unit tests for AI module."""

import pytest
from morphcards.ai import AIServiceFactory


class TestAIServiceFactory:
    def test_get_available_services(self) -> None:
        services = AIServiceFactory.get_available_services()
        assert "openai" in services
        assert "gemini" in services
    
    def test_create_openai_service(self) -> None:
        service = AIServiceFactory.create_service("openai")
        assert service is not None
    
    def test_create_gemini_service(self) -> None:
        service = AIServiceFactory.create_service("gemini")
        assert service is not None
    
    def test_create_invalid_service(self) -> None:
        with pytest.raises(ValueError):
            AIServiceFactory.create_service("invalid")
