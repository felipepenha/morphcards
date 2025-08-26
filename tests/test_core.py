"""Unit tests for core module."""

import pytest
from datetime import datetime, timedelta
from morphcards.core import Card, Rating, ReviewLog, Scheduler


class TestCard:
    def test_card_creation(self) -> None:
        card = Card(
            id="test_1",
            word="hello",
            sentence="Hello world!",
            original_sentence="Hello world!",
            due_date=datetime.now()
        )
        assert card.word == "hello"
        assert card.sentence == "Hello world!"
        assert card.review_count == 0


class TestRating:
    def test_rating_values(self) -> None:
        assert Rating.AGAIN == 1
        assert Rating.HARD == 2
        assert Rating.GOOD == 3
        assert Rating.EASY == 4


class TestScheduler:
    def test_scheduler_initialization(self) -> None:
        scheduler = Scheduler()
        assert scheduler.parameters is not None
        
    def test_scheduler_with_custom_parameters(self) -> None:
        custom_params = [1.0] * 17  # FSRS has 17 parameters
        scheduler = Scheduler(custom_params)
        assert scheduler.parameters == tuple(custom_params)
