"""MorphCards: Spaced Spatial Repetition with AI-generated sentence variations for language learning."""

__version__ = "0.1.0"
__author__ = "Felipe Campos Penha"
__email__ = "felipe.penha@alumni.usp.br"

from .core import Card, ReviewLog, Scheduler
from .database import VocabularyDatabase
from .ai import AIService, OpenAIService, GeminiService

__all__ = [
    "Card",
    "ReviewLog", 
    "Scheduler",
    "VocabularyDatabase",
    "AIService",
    "OpenAIService",
    "GeminiService",
]
