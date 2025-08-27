"""Core classes for MorphCards spaced repetition system."""

from datetime import datetime, timezone
from typing import List, Optional, Union, Tuple, TYPE_CHECKING
from enum import IntEnum
import uuid # Added import for uuid

from fsrs import Scheduler, Card as FSRS_Card, Rating as FSRS_Rating, State # Import State directly
from pydantic import BaseModel, Field, ConfigDict

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
    stability: Optional[float] = Field(default=None, description="FSRS stability parameter")
    difficulty: Optional[float] = Field(default=None, description="FSRS difficulty parameter")
    due_date: datetime = Field(..., description="Next review date")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Card creation timestamp")
    last_reviewed: Optional[datetime] = Field(default=None, description="Last review timestamp")
    review_count: int = Field(default=0, description="Number of times reviewed")
    state: State = Field(default=State.Learning, description="FSRS state")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ReviewLog(BaseModel):
    """Record of a completed review."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the review log") # Added id field
    card_id: str = Field(..., description="ID of the reviewed card")
    review_time: datetime = Field(..., description="When the review was completed")
    rating: Rating = Field(..., description="User's rating of recall")
    interval: float = Field(..., description="Time interval until next review")
    stability: float = Field(..., description="Card stability after review")
    difficulty: float = Field(..., description="Card difficulty after review")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


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
        
        # Convert morphcards.core.Card to fsrs.Card
        fsrs_card = FSRS_Card(
            card_id=hash(card.id),
            state=card.state,
            step=card.review_count,
            stability=card.stability,
            difficulty=card.difficulty,
            due=card.due_date.replace(tzinfo=timezone.utc),
            last_review=card.last_reviewed.replace(tzinfo=timezone.utc) if card.last_reviewed else None
        )

        # Get FSRS scheduling
        updated_fsrs_card, fsrs_review_log = self._fsrs.review_card(fsrs_card, FSRS_Rating(rating_int), now.replace(tzinfo=timezone.utc), None) # State is already set in fsrs_card
        
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
            stability=updated_fsrs_card.stability,
            difficulty=updated_fsrs_card.difficulty,
            due_date=updated_fsrs_card.due,
            created_at=card.created_at,
            last_reviewed=now,
            review_count=card.review_count + 1,
            state=updated_fsrs_card.state,
        )
        
        # Create review log
        review_log = ReviewLog(
            id=str(uuid.uuid4()), # Generate a unique ID for the review log
            card_id=card.id,
            review_time=now,
            rating=Rating(rating_int),
            interval=(updated_fsrs_card.due - updated_fsrs_card.last_review).days if updated_fsrs_card.last_review else 0,
            stability=updated_fsrs_card.stability,
            difficulty=updated_fsrs_card.difficulty,
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