"AI service module for generating sentence variations."

import os
import time
from abc import ABC, abstractmethod
from typing import List, Optional

import google.generativeai as genai
import openai
import requests

from morphcards.core import Rating  # Import Rating


def _create_prompt(
    word: str,
    learned_vocabulary: List[str],
    language: str,
    rating: Optional[Rating] = None,  # Added rating parameter
    additional_instruction: str = "",
) -> str:
    """Creates the prompt string for the AI API based on the given parameters.

    Args:
        word: The word to include in the sentence.
        learned_vocabulary: A list of learned words to constrain sentence generation.
        language: The target language for the sentence.
        rating: The user's rating for the card (optional).
        additional_instruction: Additional instruction to be added to the prompt.

    Returns:
        The formatted prompt string.
    """
    vocab_text = ", ".join(learned_vocabulary[:20])  # Limit to first 20 words

    return f"""Generate a natural, grammatically correct sentence in {language} that:
1. Contains the word '{word}' in a meaningful context
2. Uses vocabulary from this list, as much as possible: {vocab_text}
3. When vocabulary is too short, used vocabulary based on language level inference
3. Sounds natural to a native speaker
4. Is appropriate for language learning
5. The sentence is short, from 2 to 10 words max
{additional_instruction}
Return only the sentence, no explanations."""


class AIService(ABC):
    """Abstract base class for AI services."""

    @abstractmethod
    def generate_sentence_variation(
        self,
        word: str,
        learned_vocabulary: List[str],
        api_key: str,
        language: str = "English",
        rating: Optional[Rating] = None,  # Added rating parameter
    ) -> str:
        """Generates a new sentence variation for the given word.

        Args:
            word: The word for which to generate a sentence.
            learned_vocabulary: A list of words considered learned by the user.
            api_key: The API key for the AI service.
            language: The language of the sentence (default: "English").
            rating: The user's rating for the card (optional).

        Returns:
            A new sentence containing the word, adhering to the learned vocabulary.
        """
        pass


class OpenAIService(AIService):
    """OpenAI API service for generating sentence variations."""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """Initializes the OpenAIService.

        Args:
            model: The OpenAI model to use for sentence generation (default: "gpt-3.5-turbo").
        """
        self.model = model
        self.client: Optional[openai.OpenAI] = None

    def generate_sentence_variation(
        self,
        word: str,
        learned_vocabulary: List[str],
        api_key: str,
        language: str = "English",
        rating: Optional[Rating] = None,  # Added rating parameter
    ) -> str:
        """Generates a new sentence variation using the OpenAI API.

        Args:
            word: The word for which to generate a sentence.
            learned_vocabulary: A list of words considered learned by the user.
            api_key: The OpenAI API key.
            language: The language of the sentence (default: "English").
            rating: The user's rating for the card (optional).

        Returns:
            A new sentence containing the word, adhering to the learned vocabulary.
            Returns a fallback sentence if an error occurs during API call.
        """
        try:
            # Initialize client with API key
            if not self.client:
                self.client = openai.OpenAI(api_key=api_key)

            # Create prompt for sentence generation
            prompt = _create_prompt(
                word, learned_vocabulary, language, rating
            )  # Pass rating

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
                temperature=0.9,
            )

            # Extract and clean response
            sentence = response.choices[0].message.content.strip()

            # Remove quotes if present
            if sentence.startswith('"') and sentence.endswith('"'):
                sentence = sentence[1:-1]

            return sentence

        except Exception as e:
            # Fallback to a simple template
            return f"I am learning the word '{word}' in {language}'."

    def _handle_rate_limit(self, retry_after: int) -> None:
        """Handles API rate limiting by pausing execution.

        Args:
            retry_after: The number of seconds to wait before retrying the request.
        """
        time.sleep(retry_after)


class GeminiService(AIService):
    """Google Gemini API service for generating sentence variations."""

    def __init__(self, model: str = "gemini-pro"):
        """Initializes the GeminiService.

        Args:
            model: The Gemini model to use for sentence generation (default: "gemini-pro").
        """
        self.model = model
        self.client: Optional[genai.GenerativeModel] = None

    def generate_sentence_variation(
        self,
        word: str,
        learned_vocabulary: List[str],
        api_key: str,
        language: str = "English",
        rating: Optional[Rating] = None,  # Added rating parameter
    ) -> str:
        """Generates a new sentence variation using the Google Gemini API.

        Args:
            word: The word for which to generate a sentence.
            learned_vocabulary: A list of words considered learned by the user.
            api_key: The Google Gemini API key.
            language: The language of the sentence (default: "English").
            rating: The user's rating for the card (optional).

        Returns:
            A new sentence containing the word, adhering to the learned vocabulary.
            Returns a fallback sentence if an error occurs during API call.
        """
        try:
            # Initialize client with API key
            if not self.client:
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(self.model)

            # Create prompt for sentence generation
            prompt = _create_prompt(
                word, learned_vocabulary, language, rating
            )  # Pass rating

            # Generate response
            response = self.client.generate_content(
                prompt, generation_config={"temperature": 0.9}
            )

            # Extract and clean response
            sentence = response.text.strip()

            # Remove quotes if present
            if sentence.startswith('"') and sentence.endswith('"'):
                sentence = sentence[1:-1]

            return sentence

        except Exception as e:
            # Fallback to a simple template
            return f"I am learning the word '{word}' in {language}'."


class AIServiceFactory:
    """Factory for creating AI service instances."""

    @staticmethod
    def create_service(service_type: str) -> AIService:
        """Creates an instance of an AI service based on the specified type.

        Args:
            service_type: The type of AI service to create ("openai" or "gemini").

        Returns:
            An instance of a concrete AIService implementation.

        Raises:
            ValueError: If an unknown AI service type is provided.
        """
        if service_type.lower() == "openai":
            return OpenAIService()
        elif service_type.lower() == "gemini":
            return GeminiService()
        else:
            raise ValueError(f"Unknown AI service type: {service_type}")

    @staticmethod
    def get_available_services() -> List[str]:
        """Returns a list of supported AI service types.

        Returns:
            A list of strings, e.g., ["openai", "gemini"].
        """
        return ["openai", "gemini"]
