"""Core classes for MorphCards spaced repetition system."""

import uuid
from datetime import datetime, timezone
from enum import IntEnum
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

from fsrs import Card as FSRS_Card
from fsrs import Rating as FSRS_Rating
from fsrs import Scheduler, State
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .ai import AIService
    from .database import VocabularyDatabase


class Rating(IntEnum):
    """Represents the user's recall rating for a flashcard.

    Attributes:
        AGAIN: The user forgot the card (rating 1).
        HARD: The user had difficulty recalling the card (rating 2).
        GOOD: The user recalled the card well (rating 3).
        EASY: The user recalled the card easily (rating 4).
    """

    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4


class Card(BaseModel):
    """Represents a flashcard in the spaced repetition system.

    Attributes:
        id: Unique identifier for the card.
        word: The word or phrase to be learned.
        sentence: The current sentence associated with the word.
        original_sentence: The original sentence used when the card was created.
        stability: FSRS stability parameter, indicating how well the card is learned.
        difficulty: FSRS difficulty parameter, indicating the inherent difficulty of the card.
        due_date: The next scheduled review date for the card.
        created_at: Timestamp when the card was created.
        last_reviewed: Timestamp of the last review.
        review_count: The number of times the card has been reviewed.
        state: The current FSRS state of the card (New, Learning, Review, Relearning).
    """

    id: str = Field(..., description="Unique identifier for the card")
    word: str = Field(..., description="The word to learn")
    sentence: str = Field(..., description="Current sentence containing the word")
    original_sentence: str = Field(
        ..., description="Original sentence when card was created"
    )
    stability: Optional[float] = Field(
        default=None, description="FSRS stability parameter"
    )
    difficulty: Optional[float] = Field(
        default=None, description="FSRS difficulty parameter"
    )
    due_date: datetime = Field(..., description="Next review date")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Card creation timestamp",
    )
    last_reviewed: Optional[datetime] = Field(
        default=None, description="Last review timestamp"
    )
    review_count: int = Field(default=0, description="Number of times reviewed")
    state: State = Field(default=State.Learning, description="FSRS state")
    language: str = Field(
        ..., description="Language of the card"
    )  # Added language field

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ReviewLog(BaseModel):
    """Records details of a single review session for a flashcard.

    Attributes:
        id: Unique identifier for the review log entry.
        card_id: The ID of the card that was reviewed.
        review_time: The timestamp when the review was completed.
        rating: The user's rating of their recall (1-4).
        interval: The calculated interval until the next review.
        stability: The card's stability parameter after this review.
        difficulty: The card's difficulty parameter after this review.
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the review log",
    )
    card_id: str = Field(..., description="ID of the reviewed card")
    review_time: datetime = Field(..., description="When the review was completed")
    rating: Rating = Field(..., description="User's rating of recall")
    interval: float = Field(..., description="Time interval until next review")
    stability: float = Field(..., description="Card stability after review")
    difficulty: float = Field(..., description="Card difficulty after review")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class FSRSScheduler:
    """Manages the spaced repetition scheduling using the FSRS algorithm.

    This class handles the logic for updating card parameters (stability, difficulty,
    and due date) based on user ratings and generates new sentences for review.
    """

    def __init__(self, parameters: Optional[List[float]] = None):
        """Initializes the FSRSScheduler.

        Args:
            parameters: Optional list of custom FSRS parameters. If None,
                        default parameters for FSRS v4.0.0 are used.
        """
        self._fsrs: Scheduler

        if parameters is None:
            # Default parameters for FSRS v4.0.0
            default_fsrs_parameters = (
                0.4072,
                1.1829,
                3.1262,
                15.4722,
                7.2102,
                0.5316,
                1.0651,
                0.0234,
                1.616,
                0.1544,
                1.0824,
                1.9813,
                0.0953,
                0.2975,
                2.2042,
                0.2407,
                2.9466,
                0.5034,
                0.6567,
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
        vocabulary_database: "VocabularyDatabase",
        ai_service: "AIService",
        language: str,
        mastered_words_override: Optional[List[str]] = None,
    ) -> Tuple[Card, ReviewLog]:
        """Processes a card review, updates its FSRS parameters, and generates a new sentence.

        Args:
            card: The current state of the card being reviewed.
            rating: The user's recall rating (1-4).
            now: The current timestamp of the review.
            ai_api_key: API key for the AI service.
            vocabulary_database: The database instance to retrieve learned vocabulary.
            ai_service: The AI service instance for sentence generation.
            language: The language of the card.
            mastered_words_override: Optional list of words to use for AI sentence generation.

        Returns:
            A tuple containing the updated Card object and a ReviewLog entry
            for the current review.
        """
        rating_int = rating.value if isinstance(rating, Rating) else rating

        fsrs_card = FSRS_Card(
            card_id=hash(card.id),
            state=card.state,
            step=card.review_count,
            stability=card.stability,
            difficulty=card.difficulty,
            due=card.due_date.replace(tzinfo=timezone.utc),
            last_review=(
                card.last_reviewed.replace(tzinfo=timezone.utc)
                if card.last_reviewed
                else None
            ),
        )

        updated_fsrs_card, fsrs_review_log = self._fsrs.review_card(
            fsrs_card, FSRS_Rating(rating_int), now.replace(tzinfo=timezone.utc), None
        )

        new_sentence = self._generate_new_sentence(
            card.word,
            card.original_sentence,
            vocabulary_database,
            ai_service,
            ai_api_key,
            Rating(rating_int),
            language,
            mastered_words_override,
        )

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
            language=card.language,
        )

        review_log = ReviewLog(
            id=str(uuid.uuid4()),
            card_id=card.id,
            review_time=now,
            rating=Rating(rating_int),
            interval=(
                (updated_fsrs_card.due - updated_fsrs_card.last_review).days
                if updated_fsrs_card.last_review
                else 0
            ),
            stability=updated_fsrs_card.stability,
            difficulty=updated_fsrs_card.difficulty,
        )

        return updated_card, review_log

    def _generate_new_sentence(
        self,
        word: str,
        original_sentence: str,
        vocabulary_database: "VocabularyDatabase",
        ai_service: "AIService",
        api_key: str,
        rating: Rating,
        language: str,
        mastered_words_override: Optional[List[str]] = None,
    ) -> str:
        """Generates a new sentence variation using an AI service.

        If the learned vocabulary is insufficient or an error occurs during AI generation,
        the original sentence is returned as a fallback.

        Args:
            word: The word for which to generate a new sentence.
            original_sentence: The original sentence associated with the word.
            vocabulary_database: The database instance to retrieve learned vocabulary.
            ai_service: The AI service instance to use for generation.
            api_key: The API key for the AI service.
            rating: The user's rating for the card.
            language: The language of the card.
            mastered_words_override: Optional list of words to use for AI sentence generation.

        Returns:
            A new AI-generated sentence, or the original sentence if generation fails.
        """
        try:
            if mastered_words_override is not None:
                learned_words = mastered_words_override
            else:
                learned_words = vocabulary_database.get_learned_vocabulary()

            if len(learned_words) < 5:
                return original_sentence

            new_sentence = ai_service.generate_sentence_variation(
                word=word,
                learned_vocabulary=learned_words,
                api_key=api_key,
                language=language,
                rating=rating,
            )

            return new_sentence

        except Exception as e:
            print(
                f"DEBUG: Error generating new sentence: {e}. Falling back to original sentence."
            )
            return original_sentence
