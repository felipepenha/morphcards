"""Core classes for MorphCards spaced repetition system."""

from datetime import datetime
from typing import List, Optional, Union, Tuple, TYPE_CHECKING
from enum import IntEnum

from fsrs import Scheduler
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .database import VocabularyDatabase
    from .ai import AIService


class Rating(IntEnum):
    """User rating for card recall."""
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4


class Card(BaseModel):
    """Represents a flashcard with word and sentence."""
    id: str = Field(..., description="Unique identifier for the card")
    word: str = Field(..., description="The word to learn")
    sentence: str = Field(..., description="Current sentence containing the word")
    original_sentence: str = Field(..., description="Original sentence when card was created")
    stability: float = Field(default=0.0, description="FSRS stability parameter")
    difficulty: float = Field(default=0.0, description="FSRS difficulty parameter")
    due_date: datetime = Field(..., description="Next review date")
    created_at: datetime = Field(default_factory=datetime.now, description="Card creation timestamp")
    last_reviewed: Optional[datetime] = Field(default=None, description="Last review timestamp")
    review_count: int = Field(default=0, description="Number of times reviewed")
    
    class Config:
        arbitrary_types_allowed = True


class ReviewLog(BaseModel):
    """Record of a completed review."""
    card_id: str = Field(..., description="ID of the reviewed card")
    review_time: datetime = Field(..., description="When the review was completed")
    rating: Rating = Field(..., description="User's rating of recall")
    interval: float = Field(..., description="Time interval until next review")
    stability: float = Field(..., description="Card stability after review")
    difficulty: float = Field(..., description="Card difficulty after review")
    
    class Config:
        arbitrary_types_allowed = True


class FSRSScheduler:
    """FSRS-based scheduler for spaced repetition."""
    
    def __init__(self, parameters: Optional[List[float]] = None):
        """Initialize scheduler with optional custom parameters."""
        if parameters is None:
            # Default parameters for FSRS v4.0.0
            default_fsrs_parameters = (
                0.4072, 1.1829, 3.1262, 15.4722, 7.2102, 0.5316, 1.0651, 0.0234, 1.616, 0.1544,
                1.0824, 1.9813, 0.0953, 0.2975, 2.2042, 0.2407, 2.9466, 0.5034, 0.6567,
            )
            self._fsrs = Scheduler(parameters=default_fsrs_parameters)
        else:
            self._fsrs = Scheduler(parameters=parameters)
    
    def review_card(
        self,
        card: Card,
        rating: Union[Rating, int],
        now: datetime,
        ai_api_key: str,
        vocabulary_database: 'VocabularyDatabase',
        ai_service: 'AIService',
    ) -> Tuple[Card, ReviewLog]:
        """
        Process a card review and return updated card and review log.
        
        Args:
            card: Current card state
            rating: User's rating of recall
            now: Current timestamp
            ai_api_key: API key for AI service
            vocabulary_database: Database containing learned vocabulary
            ai_service: AI service for generating new sentences
            
        Returns:
            Tuple of (updated_card, review_log)
        """
        # Convert rating to int if it's an enum
        rating_int = rating.value if isinstance(rating, Rating) else rating
        
        # Get FSRS scheduling
        scheduling_cards = self._fsrs.repeat(card, now)
        scheduled_card = scheduling_cards[rating_int - 1].card
        
        # Generate new sentence using AI
        new_sentence = self._generate_new_sentence(
            card.word,
            card.original_sentence,
            vocabulary_database,
            ai_service,
            ai_api_key,
        )
        
        # Update card with new sentence and FSRS parameters
        updated_card = Card(
            id=card.id,
            word=card.word,
            sentence=new_sentence,
            original_sentence=card.original_sentence,
            stability=scheduled_card.stability,
            difficulty=scheduled_card.difficulty,
            due_date=scheduled_card.due,
            created_at=card.created_at,
            last_reviewed=now,
            review_count=card.review_count + 1,
        )
        
        # Create review log
        review_log = ReviewLog(
            card_id=card.id,
            review_time=now,
            rating=Rating(rating_int),
            interval=scheduled_card.interval,
            stability=scheduled_card.stability,
            difficulty=scheduled_card.difficulty,
        )
        
        return updated_card, review_log
    
    def _generate_new_sentence(
        self,
        word: str,
        original_sentence: str,
        vocabulary_database: 'VocabularyDatabase',
        ai_service: 'AIService',
        api_key: str,
    ) -> str:
        """Generate a new sentence using AI or fallback to original."""
        try:
            # Get learned vocabulary
            learned_words = vocabulary_database.get_learned_vocabulary()
            
            # If vocabulary is too short, fallback to original sentence
            if len(learned_words) < 5:  # Minimum threshold
                return original_sentence
            
            # Generate new sentence using AI
            new_sentence = ai_service.generate_sentence_variation(
                word=word,
                learned_vocabulary=learned_words,
                api_key=api_key,
            )
            
            return new_sentence
            
        except Exception:
            # Fallback to original sentence on any error
            return original_sentence
