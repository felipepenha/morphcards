"AI service module for generating sentence variations."

import os
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Union

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
* Contains the word '{word}' in a meaningful context
* Uses vocabulary from this list, as much as possible: {vocab_text}
* When vocabulary is too short, used vocabulary based on language level inference
* Sounds natural to a native speaker
* Is appropriate for language learning
* The sentence is short, from 2 to 10 words max
{additional_instruction}
Return only the sentence, no explanations."""


def _get_openai_client(api_key: str) -> openai.OpenAI:
    return openai.OpenAI(api_key=api_key)


def _get_gemini_client(api_key: str, model_name: str) -> genai.GenerativeModel:
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


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

    def __init__(self):
        """Initializes the OpenAIService."""
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
        # Initialize client with API key
        self.client = _get_openai_client(api_key)

        # Create prompt for sentence generation
        additional_instruction = ""
        if rating == Rating.AGAIN:
            additional_instruction = "* Generate a sentence that is significantly different from previous sentences for this word.\n"
        prompt = _create_prompt(
            word, learned_vocabulary, language, rating, additional_instruction
        )  # Pass rating

        # Define a preferred order of models (most capable to least capable/cheapest)
        preferred_model_families = ["gpt-4", "gpt-3.5-turbo"]

        # Get all available models and filter for chat completion capabilities
        available_models = []
        try:
            for m in self.client.models.list():
                # Check if the model is a chat completion model
                # This is a heuristic, as OpenAI API doesn't expose a direct capability for this
                if m.id.startswith(("gpt-4", "gpt-3.5-turbo")):
                    available_models.append(m.id)
        except Exception as e:
            print(f"Error listing OpenAI models: {e}")
            # If listing models fails, fall back to hardcoded preferred models
            available_models = preferred_model_families

        # Create a prioritized list of models to try
        models_to_try = []
        for preferred_family in preferred_model_families:
            # Find the latest version of the preferred family
            matching_models = sorted([
                m for m in available_models if m.startswith(preferred_family)
            ], reverse=True) # Sort to get latest version first
            if matching_models:
                models_to_try.append(matching_models[0])
        
        # Add any other available models that support chat completion, not in preferred_models
        for model_name in available_models:
            if model_name not in models_to_try:
                models_to_try.append(model_name)

        if not models_to_try:
            print("No suitable OpenAI models found that support chat completion.")
            return f"I am learning the word '{word}' in {language}'."

        for model_name in models_to_try:
            try:
                print(f"Attempting to generate content with OpenAI model: {model_name}")
                response = self.client.chat.completions.create(
                    model=model_name,
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
                print(f"Error with OpenAI model {model_name}: {e}")
                # Continue to next fallback model
                continue

        # Fallback to a simple template if all models fail
        return f"I am learning the word '{word}' in {language}'."

    def _handle_rate_limit(self, retry_after: int) -> None:
        """Handles API rate limiting by pausing execution.

        Args:
            retry_after: The number of seconds to wait before retrying the request.
        """
        time.sleep(retry_after)


class GeminiService(AIService):
    """Google Gemini API service for generating sentence variations."""

    def __init__(self):
        """Initializes the GeminiService."""
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
        additional_instruction = ""
        if rating == Rating.AGAIN:
            additional_instruction = "* Generate a sentence that is significantly different from previous sentences for this word.\n"
        prompt = _create_prompt(
            word, learned_vocabulary, language, rating, additional_instruction
        )  # Pass rating

        # Define a preferred order of models (most capable to least capable/cheapest)
        # These are common and generally available models.
        preferred_model_families = ["models/gemini-2.5-flash-lite", "models/gemini-1.5-flash-lite", "models/gemini-1.5-pro"]

        # Get all available models and filter for text generation capabilities
        available_models = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                available_models.append(m.name)

        # Create a prioritized list of models to try
        models_to_try = []
        for preferred_family in preferred_model_families:
            # Find the latest version of the preferred family
            matching_models = sorted([
                m for m in available_models if m.startswith(preferred_family)
            ], reverse=True) # Sort to get latest version first
            if matching_models:
                models_to_try.append(matching_models[0])
        
        

        if not models_to_try:
            print("No suitable Gemini models found that support content generation.")
            return f"I am learning the word '{word}' in {language}'."

        for model_name in models_to_try:
            try:
                print(f"Attempting to generate content with Gemini model: {model_name}")
                # Initialize client with API key and current model
                self.client = _get_gemini_client(api_key, model_name)

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
                print(f"Error with Gemini model {model_name}: {e}")
                # Continue to next fallback model
                continue

        # Fallback to a simple template if all models fail
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
