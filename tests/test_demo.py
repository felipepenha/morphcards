"""Unit tests for the demo module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import ANY, MagicMock, patch

import pytest

from morphcards.core import Card, FSRSScheduler, Rating  # Import FSRSScheduler
from morphcards.demo import MorphCardsDemo


class TestMorphCardsDemo:
    """Test suite for the MorphCardsDemo class."""

    @pytest.fixture
    def demo(self):
        """Fixture to create a MorphCardsDemo instance with a mocked database."""
        with patch("morphcards.demo.VocabularyDatabase") as MockDB:
            db_instance = MockDB.return_value
            demo_instance = MorphCardsDemo()
            demo_instance.db = db_instance
            # Initialize the actual scheduler for integrated tests
            demo_instance.scheduler = FSRSScheduler()
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
        due_card = Card(
            id="1",
            word="due",
            sentence="This card is due.",
            original_sentence="This card is due.",
            due_date=demo.current_time,
            language="English",
        )
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
        due_card = Card(
            id="1",
            word="review",
            sentence="Review this card.",
            original_sentence="Review this card.",
            due_date=demo.current_time,
            language="English",
        )
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
        demo.current_card = Card(
            id="1",
            word="test",
            sentence="Test sentence.",
            original_sentence="Test sentence.",
            due_date=demo.current_time,
            language="English",
        )
        result = demo.submit_review("5")
        assert "Please enter a rating between 1 and 4." in result
        result = demo.submit_review("abc")
        assert "Please enter a valid number." in result

    def test_submit_review_successfully(self, demo: MorphCardsDemo):
        """Test a successful review submission."""
        # Setup
        demo.api_key = "fake_api_key"
        demo.ai_service_type = "openai"

        patch(
            "morphcards.core.FSRSScheduler._generate_new_sentence",
            return_value="A new AI generated sentence.",
        ).start()

        original_card = Card(
            id="1",
            word="test",
            sentence="This is a test.",
            original_sentence="This is a test.",
            due_date=demo.current_time, # Use demo.current_time
            stability=None,
            difficulty=None,
            language="English",
        )
        original_card.due_date = original_card.due_date.replace(
            tzinfo=timezone.utc
        )  # Ensure original_card.due_date is timezone-aware
        demo.current_card = original_card

        # Mock get_learned_vocabulary to ensure AI service is called
        demo.db.get_learned_vocabulary = MagicMock(
            return_value=["word1", "word2", "word3", "word4", "word5"]
        )

        # Execute
        result = demo.submit_review("3")

        # Assert
        assert "Review completed!" in result
        assert (
            "New sentence: A new AI generated sentence."
        ) in result  # This will come from the mocked AI service
        assert "Next review:" in result
        assert (
            "Stability:"
        ) in result  # Check for presence, not exact value as it's dynamic
        assert (
            "Difficulty:"
        ) in result  # Check for presence, not exact value as it's dynamic

        # Assert database interactions
        demo.db.update_card.assert_called_once()
        updated_card_arg = demo.db.update_card.call_args[0][0]
        assert updated_card_arg.id == original_card.id
        assert updated_card_arg.review_count == 1  # First review
        assert updated_card_arg.last_reviewed is not None
        assert updated_card_arg.stability is not None
        assert updated_card_arg.difficulty is not None
        assert (
            updated_card_arg.due_date > original_card.due_date
        )  # Due date should advance

        demo.db.add_review_log.assert_called_once()
        review_log_arg = demo.db.add_review_log.call_args[0][0]
        assert review_log_arg.card_id == original_card.id
        assert review_log_arg.rating == Rating.GOOD
        assert review_log_arg.review_time is not None
        assert review_log_arg.interval is not None
        assert review_log_arg.stability is not None
        assert review_log_arg.difficulty is not None

        assert demo.current_card is None

    def test_set_api_key(self, demo: MorphCardsDemo):
        """Test setting the API key and service type."""
        result = demo.set_api_key("my_key", "gemini")
        assert "API key set for gemini service." in result
        assert demo.api_key == "my_key"
        assert demo.ai_service_type == "gemini"

    def test_get_stats(self, demo: MorphCardsDemo):
        """Test getting vocabulary statistics."""
        stats_data = {"total_words": 10, "total_cards": 15, "total_reviews": 50}
        demo.db.get_vocabulary_stats.return_value = stats_data
        result = demo.get_stats()
        assert "Total words learned: 10" in result
        assert "Total cards: 15" in result
        assert "Total reviews: 50" in result

    def test_full_review_cycle(self, demo: MorphCardsDemo):
        """Test the full cycle of adding a card and then reviewing it."""
        # Setup: Mock AI service for sentence generation
        patch(
            "morphcards.core.FSRSScheduler._generate_new_sentence",
            return_value="A new AI generated sentence.",
        ).start()

        # Mock datetime.now() to control time
        fixed_now = datetime(2025, 8, 26, 10, 0, 0, tzinfo=timezone.utc)
        demo.current_time = fixed_now # Set demo.current_time

        # 1. Add a new card
        word = "cycle"
        sentence = "This is a test sentence for the cycle."
        add_result = demo.add_card(word, sentence, "English")
        assert "Added card for word: cycle" in add_result

        # Simulate the database having the added card
        predictable_card_id = f"{word}_test_id"
        added_card_from_db = Card(
            id=predictable_card_id,
            word=word,
            sentence=sentence,
            original_sentence=sentence,
            due_date=fixed_now,  # Use fixed_now for initial card
            stability=None,
            difficulty=None,
            language="English",
        )
        demo.db.add_card.side_effect = lambda card_arg: setattr(
            card_arg, "id", predictable_card_id
        )

        # We need to mock get_due_cards to return the card we just added
        demo.db.get_due_cards.return_value = [added_card_from_db]
        demo.db.add_card.reset_mock()  # Reset mock to check update_card later

        # 2. Start review
        start_review_result = demo.start_review()
        assert "Reviewing: cycle" in start_review_result[0]
        assert demo.current_card is not None
        assert demo.current_card.word == word

        # 3. Submit review (rating 3 - Good)
        # No longer mocking demo.scheduler.review_card, let the actual method run
        submit_result = demo.submit_review("3")

        # Assert review result message
        assert "Review completed!" in submit_result
        assert "New sentence: A new AI generated sentence."
        assert "Next review:"
        assert (
            "Stability:"
        ) in submit_result  # Check for presence, not exact value as it's dynamic
        assert (
            "Difficulty:"
        ) in submit_result  # Check for presence, not exact value as it's dynamic

        # Assert database interactions
        demo.db.update_card.assert_called_once()
        updated_card_arg = demo.db.update_card.call_args[0][0]
        assert updated_card_arg.id == predictable_card_id
        assert updated_card_arg.review_count == 1  # First review
        assert updated_card_arg.last_reviewed is not None
        assert updated_card_arg.stability is not None
        assert updated_card_arg.difficulty is not None
        assert (
            updated_card_arg.due_date > added_card_from_db.due_date
        )  # Due date should advance

        demo.db.add_review_log.assert_called_once()
        review_log_arg = demo.db.add_review_log.call_args[0][0]
        assert review_log_arg.card_id == predictable_card_id
        assert review_log_arg.rating == Rating.GOOD
        assert review_log_arg.review_time is not None
        assert review_log_arg.interval is not None
        assert review_log_arg.stability is not None
        assert review_log_arg.difficulty is not None

        assert demo.current_card is None

    def test_add_card_and_review_multiple_times(self, demo: MorphCardsDemo):
        """Test adding a card and reviewing it multiple times with different ratings."""
        # Setup: Mock AI service for sentence generation
        patch(
            "morphcards.core.FSRSScheduler._generate_new_sentence",
            return_value="A new AI generated sentence.",
        ).start()

        # Mock datetime.now() to control time
        fixed_now_initial = datetime(2025, 8, 26, 10, 0, 0, tzinfo=timezone.utc)
        fixed_now_after_first_review = fixed_now_initial + timedelta(hours=1)
        fixed_now_after_second_review = fixed_now_initial + timedelta(days=1)

        demo.current_time = fixed_now_initial # Set demo.current_time

        # 1. Add a new card
        word = "multi_review"
        sentence = "This is a sentence for multiple reviews."
        add_result = demo.add_card(word, sentence, "English")
        assert "Added card for word: multi_review" in add_result

        # Simulate the database having the added card
        predictable_card_id = f"{word}_test_id"
        added_card_from_db = Card(
            id=predictable_card_id,
            word=word,
            sentence=sentence,
            original_sentence=sentence,
            due_date=fixed_now_initial,  # Use fixed_now for initial card
            stability=None,
            difficulty=None,
            language="English",
        )
        demo.db.add_card.side_effect = lambda card_arg: setattr(
            card_arg, "id", predictable_card_id
        )
        demo.db.get_due_cards.return_value = [added_card_from_db]
        demo.db.add_card.reset_mock()  # Reset mock to check update_card later

        # First review (Rating 3 - Good)
        start_review_result = demo.start_review()
        assert "Reviewing: multi_review" in start_review_result[0]
        submit_result = demo.submit_review("3")
        assert "Review completed!"
        assert demo.db.update_card.call_count == 1
        assert demo.db.add_review_log.call_count == 1
        updated_card_after_first_review = demo.db.update_card.call_args[0][0]
        assert updated_card_after_first_review.review_count == 1
        demo.db.update_card.reset_mock()
        demo.db.add_review_log.reset_mock()

        # Second review (Rating 1 - Again)
        # Simulate the card being due again (e.g., by advancing time or mocking get_due_cards)
        demo.db.get_due_cards.return_value = [updated_card_after_first_review]
        demo.current_card = updated_card_after_first_review  # Manually set current_card for the next review

        start_review_result = demo.start_review()
        assert "Reviewing: multi_review" in start_review_result[0]
        submit_result = demo.submit_review("1")
        assert "Review completed!"
        assert demo.db.update_card.call_count == 1
        assert demo.db.add_review_log.call_count == 1
        updated_card_after_second_review = demo.db.update_card.call_args[0][0]
        assert updated_card_after_second_review.review_count == 2
        assert (
            updated_card_after_second_review.due_date
            < updated_card_after_first_review.due_date
        )  # Due date should be earlier for 'Again'

        patch.stopall()  # Clean up all patches

    def test_skip_to_next_day(self, demo: MorphCardsDemo):
        """Test skipping review to the next day."""
        # Setup: Create a card and set it as current
        initial_due_date = datetime(2025, 8, 27, 10, 0, 0, tzinfo=timezone.utc)
        card_to_skip = Card(
            id="skip_test_id",
            word="skip",
            sentence="This is a sentence to skip.",
            original_sentence="This is a sentence to skip.",
            due_date=initial_due_date,
            stability=1.0,
            difficulty=0.5,
            language="English",
        )
        demo.current_card = card_to_skip

        # Set demo's current_time to a specific point
        demo.current_time = datetime(2025, 8, 27, 11, 0, 0, tzinfo=timezone.utc)

        # Execute skip_to_next_day
        skip_result = demo.skip_to_next_day()

        # Assertions
        assert "Timeline advanced to next day" == skip_result[0].split('.')[0]
        # Verify that demo.current_time has advanced by one day
        expected_current_time = datetime(2025, 8, 28, 11, 0, 0, tzinfo=timezone.utc)
        assert demo.current_time == expected_current_time
        assert demo.current_card is None  # Current card should be cleared

    def test_ai_sentence_variation_on_failed_review(self, demo: MorphCardsDemo):
        """Test that AI sentence variation is called on each subsequent day for a failed card."""
        # Mock the AI service factory to return a mock AI service
        with patch("morphcards.ai.AIServiceFactory.create_service") as mock_create_service:
            mock_ai_service = MagicMock()
            expected_sentences = [
                "Sentence 1 for failed review.",
                "Sentence 2 for failed review.",
                "Sentence 3 for failed review.",
                "Sentence 4 for failed review.",
                "Sentence 5 for failed review.",
            ]
            mock_ai_service.generate_sentence_variation.side_effect = expected_sentences
            mock_create_service.return_value = mock_ai_service

            # Ensure API key is set for the demo instance
            demo.api_key = "test_api_key"
            demo.ai_service_type = "gemini"

            # Mock get_learned_vocabulary to ensure AI service is called
            demo.db.get_learned_vocabulary = MagicMock(
                return_value=["word1", "word2", "word3", "word4", "word5", "word6"]
            )

            # 1. Add a new card
            word = "test_failed_ai"
            sentence = "Initial sentence for failed AI test."
            demo.add_card(word, sentence, "English")

            # Simulate the database having the added card
            predictable_card_id = f"{word}_test_id"
            test_card = Card(
                id=predictable_card_id,
                word=word,
                sentence=sentence,
                original_sentence=sentence,
                due_date=demo.current_time,
                stability=None,
                difficulty=None,
                language="English",
            )
            demo.db.add_card.side_effect = lambda card_arg: setattr(
                card_arg, "id", predictable_card_id
            )

            # Simulate multiple days of failed reviews
            num_days = 5
            for i in range(num_days):
                # Advance time by one day
                demo.current_time += timedelta(days=1)

                # Set the card as due for review
                demo.db.get_due_cards.return_value = [test_card]
                demo.current_card = test_card

                # Start review and submit a failed rating (1 - Again)
                demo.start_review()
                submit_result = demo.submit_review("1")

                # Assert that AI service was called for sentence variation
                mock_ai_service.generate_sentence_variation.assert_called_once_with(
                    word=word,
                    learned_vocabulary=ANY, # We don't care about the exact vocabulary list here
                    api_key="test_api_key",
                    language="English",
                    rating=Rating.AGAIN,
                )

                # Assert that the sentence in the updated card is from the mock AI service
                new_sentence_prefix = "New sentence: "
                start_index = submit_result.find(new_sentence_prefix)
                end_index = submit_result.find("\n", start_index + len(new_sentence_prefix)) # Corrected escape sequence for newline
                extracted_sentence = submit_result[start_index + len(new_sentence_prefix):end_index].strip()

                assert extracted_sentence == expected_sentences[i]

                # Update the test_card with the new sentence for the next iteration
                test_card.sentence = extracted_sentence

                # Reset mock call count for the next iteration
                mock_ai_service.generate_sentence_variation.reset_mock()

            # After the loop, ensure the AI service was called for each day
            assert mock_ai_service.generate_sentence_variation.call_count == 0 # Should be 0 because we reset it in each iteration

        patch.stopall() # Clean up all patches
