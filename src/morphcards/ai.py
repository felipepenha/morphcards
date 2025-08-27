"""AI service module for generating sentence variations."""

import os
import time
from abc import ABC, abstractmethod
from typing import List, Optional

import google.generativeai as genai
import openai
import requests


class AIService(ABC):
    """Abstract base class for AI services."""

    @abstractmethod
    def generate_sentence_variation(
        self,
        word: str,
        learned_vocabulary: List[str],
        api_key: str,
        language: str = "English",
    ) -> str:
        """Generate a new sentence variation for the given word."""
        pass


class OpenAIService(AIService):
    """OpenAI API service for generating sentence variations."""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """Initialize OpenAI service."""
        self.model = model
        self.client: Optional[openai.OpenAI] = None

    def generate_sentence_variation(
        self,
        word: str,
        learned_vocabulary: List[str],
        api_key: str,
        language: str = "English",
    ) -> str:
        """Generate sentence variation using OpenAI."""
        try:
            # Initialize client with API key
            if not self.client:
                self.client = openai.OpenAI(api_key=api_key)

            # Create prompt for sentence generation
            prompt = self._create_prompt(word, learned_vocabulary, language)

            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a language learning assistant. Generate natural, grammatically correct sentences.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.7,
            )

            # Extract and clean response
            sentence = response.choices[0].message.content.strip()

            # Remove quotes if present
            if sentence.startswith('"') and sentence.endswith('"'):
                sentence = sentence[1:-1]

            return sentence

        except Exception as e:
            # Fallback to a simple template
            return f"I am learning the word '{word}' in {language}."

    def _create_prompt(
        self,
        word: str,
        learned_vocabulary: List[str],
        language: str,
    ) -> str:
        """Create prompt for sentence generation."""
        vocab_text = ", ".join(learned_vocabulary[:20])  # Limit to first 20 words

        return f"""Generate a natural, grammatically correct sentence in {language} that:
1. Contains the word '{word}' in a meaningful context
2. Uses only vocabulary from this list: {vocab_text}
3. Sounds natural to a native speaker
4. Is appropriate for language learning

Return only the sentence, no explanations."""

    def _handle_rate_limit(self, retry_after: int) -> None:
        """Handle rate limiting by waiting."""
        time.sleep(retry_after)


class GeminiService(AIService):
    """Google Gemini API service for generating sentence variations."""

    def __init__(self, model: str = "gemini-pro"):
        """Initialize Gemini service."""
        self.model = model
        self.client: Optional[genai.GenerativeModel] = None

    def generate_sentence_variation(
        self,
        word: str,
        learned_vocabulary: List[str],
        api_key: str,
        language: str = "English",
    ) -> str:
        """Generate sentence variation using Gemini."""
        try:
            # Initialize client with API key
            if not self.client:
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(self.model)

            # Create prompt for sentence generation
            prompt = self._create_prompt(word, learned_vocabulary, language)

            # Generate response
            response = self.client.generate_content(prompt)

            # Extract and clean response
            sentence = response.text.strip()

            # Remove quotes if present
            if sentence.startswith('"') and sentence.endswith('"'):
                sentence = sentence[1:-1]

            return sentence

        except Exception as e:
            # Fallback to a simple template
            return f"I am learning the word '{word}' in {language}."

    def _create_prompt(
        self,
        word: str,
        learned_vocabulary: List[str],
        language: str,
    ) -> str:
        """Create prompt for sentence generation."""
        vocab_text = ", ".join(learned_vocabulary[:20])  # Limit to first 20 words

        return f"""Generate a natural, grammatically correct sentence in {language} that:
1. Contains the word '{word}' in a meaningful context
2. Uses only vocabulary from this list: {vocab_text}
3. Sounds natural to a native speaker
4. Is appropriate for language learning

Return only the sentence, no explanations."""


class AIServiceFactory:
    """Factory for creating AI service instances."""

    @staticmethod
    def create_service(service_type: str) -> AIService:
        """Create AI service based on type."""
        if service_type.lower() == "openai":
            return OpenAIService()
        elif service_type.lower() == "gemini":
            return GeminiService()
        else:
            raise ValueError(f"Unknown AI service type: {service_type}")

    @staticmethod
    def get_available_services() -> List[str]:
        """Get list of available AI service types."""
        return ["openai", "gemini"]
