"""Tests for multi-language support."""

from datetime import datetime, timedelta
import uuid

from morphcards.core import Card, Rating
from morphcards.database import VocabularyDatabase


def test_add_and_get_cards_multiple_languages():
    """Tests adding and retrieving cards for multiple languages."""
    db = VocabularyDatabase()
    now = datetime.now()

    # Add English card
    card_en = Card(
        id=str(uuid.uuid4()),
        word="hello",
        sentence="Hello, world!",
        original_sentence="Hello, world!",
        due_date=now,
        language="English",
    )
    db.add_card(card_en)

    # Add Japanese card
    card_jp = Card(
        id=str(uuid.uuid4()),
        word="こんにちは",
        sentence="こんにちは、世界！",
        original_sentence="こんにちは、世界！",
        due_date=now,
        language="Japanese",
    )
    db.add_card(card_jp)

    # Get due cards for English
    due_cards_en = db.get_due_cards(now + timedelta(seconds=1), language="English")
    assert len(due_cards_en) == 1
    assert due_cards_en[0].word == "hello"

    # Get due cards for Japanese
    due_cards_jp = db.get_due_cards(now + timedelta(seconds=1), language="Japanese")
    assert len(due_cards_jp) == 1
    assert due_cards_jp[0].word == "こんにちは"

    # Get all due cards
    all_due_cards = db.get_due_cards(now + timedelta(seconds=1))
    assert len(all_due_cards) == 2

    db.close()


def test_vocabulary_stats_multiple_languages():
    """Tests vocabulary statistics for multiple languages."""
    db = VocabularyDatabase()
    now = datetime.now()

    # Add English card
    card_en = Card(
        id=str(uuid.uuid4()),
        word="hello",
        sentence="Hello, world!",
        original_sentence="Hello, world!",
        due_date=now,
        language="English",
    )
    db.add_card(card_en)

    # Add Japanese card
    card_jp = Card(
        id=str(uuid.uuid4()),
        word="こんにちは",
        sentence="こんにちは、世界！",
        original_sentence="こんにちは、世界！",
        due_date=now,
        language="Japanese",
    )
    db.add_card(card_jp)

    # Stats for English
    stats_en = db.get_vocabulary_stats(language="English")
    assert stats_en["total_cards"] == 1
    assert stats_en["total_words"] == 1

    # Stats for Japanese
    stats_jp = db.get_vocabulary_stats(language="Japanese")
    assert stats_jp["total_cards"] == 1
    assert stats_jp["total_words"] == 1

    # Overall stats
    stats_all = db.get_vocabulary_stats()
    assert stats_all["total_cards"] == 2
    assert stats_all["total_words"] == 2

    db.close()


def test_get_learned_vocabulary_multiple_languages():
    """Tests get_learned_vocabulary for multiple languages."""
    db = VocabularyDatabase()
    now = datetime.now()

    # Add English card and mark as learned
    card_en = Card(
        id=str(uuid.uuid4()),
        word="hello",
        sentence="Hello, world!",
        original_sentence="Hello, world!",
        due_date=now,
        language="English",
        stability=10,
    )
    db.add_card(card_en)
    db.connection.execute("UPDATE vocabulary SET mastery_level = 1 WHERE word = 'hello'")

    # Add Japanese card and mark as learned
    card_jp = Card(
        id=str(uuid.uuid4()),
        word="こんにちは",
        sentence="こんにちは、世界！",
        original_sentence="こんにちは、世界！",
        due_date=now,
        language="Japanese",
        stability=10,
    )
    db.add_card(card_jp)
    db.connection.execute("UPDATE vocabulary SET mastery_level = 1 WHERE word = 'こんにちは'")

    # Add another English card, not learned
    card_en2 = Card(
        id=str(uuid.uuid4()),
        word="world",
        sentence="Hello, world!",
        original_sentence="Hello, world!",
        due_date=now,
        language="English",
    )
    db.add_card(card_en2)

    # Get learned vocabulary for English
    learned_en = db.get_learned_vocabulary(language="English")
    assert learned_en == ["hello"]

    # Get learned vocabulary for Japanese
    learned_jp = db.get_learned_vocabulary(language="Japanese")
    assert learned_jp == ["こんにちは"]

    db.close()
