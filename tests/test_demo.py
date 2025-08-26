"""Unit tests for the demo module."""

import pytest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime, timedelta

from morphcards.demo import MorphCardsDemo
from morphcards.core import Card, Rating


class TestMorphCardsDemo:
    """Test suite for the MorphCardsDemo class."""

    @pytest.fixture
    def demo(self):
        """Fixture to create a MorphCardsDemo instance with a mocked database."""
        with patch('morphcards.demo.VocabularyDatabase') as MockDB:
            db_instance = MockDB.return_value
            demo_instance = MorphCardsDemo()
            demo_instance.db = db_instance
            return demo_instance

    def test_add_card_successfully(self, demo: MorphCardsDemo):
        """Test that a card is added successfully with valid inputs."""
        word = "test"
        sentence = "This is a test."
        result = demo.add_card(word, sentence, "English")

        assert "Added card for word: test" in result
        demo.db.add_card.assert_called_once()
        added_card = demo.db.add_card.call_args[0][0]
        assert added_card.word == word
        assert added_card.sentence == sentence

    def test_add_card_with_empty_inputs(self, demo: MorphCardsDemo):
        """Test that adding a card with empty inputs returns an. error message."""
        result = demo.add_card("", "", "English")
        assert "Please provide both word and sentence." in result
        demo.db.add_card.assert_not_called()

    def test_get_due_cards_when_none_are_due(self, demo: MorphCardsDemo):
        """Test getting due cards when no cards are due for review."""
        demo.db.get_due_cards.return_value = []
        result = demo.get_due_cards()
        assert "No cards due for review!" in result

    def test_get_due_cards_when_cards_are_due(self, demo: MorphCardsDemo):
        """Test getting due cards when there are cards due for review."""
        due_card = Card(id="1", word="due", sentence="This card is due.", original_sentence="This card is due.", due_date=datetime.now())
        demo.db.get_due_cards.return_value = [due_card]
        result = demo.get_due_cards()
        assert "Found 1 cards due for review" in result
        assert "due: This card is due." in result

    def test_start_review_with_no_due_cards(self, demo: MorphCardsDemo):
        """Test starting a review when no cards are due."""
        demo.db.get_due_cards.return_value = []
        result = demo.start_review()
        assert result[0] == "No cards due for review!"

    def test_start_review_with_due_cards(self, demo: MorphCardsDemo):
        """Test starting a review when there are due cards."""
        due_card = Card(id="1", word="review", sentence="Review this card.", original_sentence="Review this card.", due_date=datetime.now())
        demo.db.get_due_cards.return_value = [due_card]
        result = demo.start_review()
        assert "Reviewing: review" in result[0]
        assert demo.current_card == due_card

    def test_submit_review_without_starting_one(self, demo: MorphCardsDemo):
        """Test submitting a review without a card being selected."""
        result = demo.submit_review("3")
        assert "No card to review." in result

    def test_submit_review_with_invalid_rating(self, demo: MorphCardsDemo):
        """Test submitting a review with an invalid rating."""
        demo.current_card = Card(id="1", word="test", sentence="Test sentence.", original_sentence="Test sentence.", due_date=datetime.now())
        result = demo.submit_review("5")
        assert "Please enter a rating between 1 and 4." in result
        result = demo.submit_review("abc")
        assert "Please enter a valid number." in result

    def test_submit_review_without_api_key(self, demo: MorphCardsDemo):
        """Test submitting a review without setting an API key."""
        demo.current_card = Card(id="1", word="test", sentence="Test sentence.", original_sentence="Test sentence.", due_date=datetime.now())
        result = demo.submit_review("3")
        assert "Please set your API key first." in result

    @patch('morphcards.demo.AIServiceFactory')
    def test_submit_review_successfully(self, MockAIServiceFactory, demo: MorphCardsDemo):
        """Test a successful review submission."""
        # Setup
        demo.api_key = "fake_api_key"
        demo.ai_service_type = "openai"
        
        mock_ai_service = MagicMock()
        MockAIServiceFactory.create_service.return_value = mock_ai_service

        original_card = Card(
            id="1",
            word="test",
            sentence="This is a test.",
            original_sentence="This is a test.",
            due_date=datetime.now()
        )
        demo.current_card = original_card

        updated_card = Card(
            id="1",
            word="test",
            sentence="A new sentence.",
            original_sentence="This is a test.",
            due_date=datetime.now() + timedelta(days=1),
            stability=1.0,
            difficulty=0.5
        )
        review_log = MagicMock()

        with patch.object(demo.scheduler, 'review_card', return_value=(updated_card, review_log)) as mock_review_card:
            # Execute
            result = demo.submit_review("3")

            # Assert
            assert "Review completed!" in result
            assert "New sentence: A new sentence." in result
            mock_review_card.assert_called_once_with(
                card=original_card,
                rating=3,
                now=ANY, # Changed from pytest.ANY to ANY
                ai_api_key="fake_api_key",
                vocabulary_database=demo.db,
                ai_service=mock_ai_service
            )
            demo.db.update_card.assert_called_once_with(updated_card)
            demo.db.add_review_log.assert_called_once_with(review_log)
            assert demo.current_card is None

    def test_set_api_key(self, demo: MorphCardsDemo):
        """Test setting the API key and service type."""
        result = demo.set_api_key("my_key", "gemini")
        assert "API key set for gemini service." in result
        assert demo.api_key == "my_key"
        assert demo.ai_service_type == "gemini"

    def test_get_stats(self, demo: MorphCardsDemo):
        """Test getting vocabulary statistics."""
        stats_data = {'total_words': 10, 'total_cards': 15, 'total_reviews': 50}
        demo.db.get_vocabulary_stats.return_value = stats_data
        result = demo.get_stats()
        assert "Total words learned: 10" in result
        assert "Total cards: 15" in result
        assert "Total reviews: 50" in result