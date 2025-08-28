"""Unit tests for database module."""

from datetime import datetime

import pytest

from morphcards.core import Card, Rating, ReviewLog
from morphcards.database import VocabularyDatabase


class TestVocabularyDatabase:
    def test_database_initialization(self) -> None:
        db = VocabularyDatabase()
        assert db is not None
        db.close()

    def test_add_and_get_card(self) -> None:
        db = VocabularyDatabase()
        try:
            card = Card(
                id="test_1",
                word="hello",
                sentence="Hello world!",
                original_sentence="Hello world!",
                due_date=datetime.now(),
                language="English",
            )
            db.add_card(card)

            retrieved_card = db.get_card("test_1")
            assert retrieved_card is not None
            assert retrieved_card.word == "hello"
        finally:
            db.close()

    def test_get_learned_vocabulary(self) -> None:
        db = VocabularyDatabase()
        try:
            card = Card(
                id="test_2",
                word="world",
                sentence="Hello world!",
                original_sentence="Hello world!",
                due_date=datetime.now(),
                language="English",
            )
            db.add_card(card)

            vocab = db.get_learned_vocabulary()
            assert "world" in vocab
        finally:
            db.close()
