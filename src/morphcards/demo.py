"Demo interface for MorphCards using Gradio."

import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import gradio as gr
from dotenv import load_dotenv

from .ai import AIServiceFactory
from .core import Card, FSRSScheduler, Rating
from .database import VocabularyDatabase


class MorphCardsDemo:
    """Interactive demo interface for the MorphCards application.

    This class provides methods to interact with the core functionalities
    of MorphCards, such as adding cards, reviewing them, setting API keys,
    retrieving statistics, and optimizing FSRS parameters. It serves as
    the backend for the Gradio-based web interface.
    """

    def __init__(self) -> None:
        """Initializes the MorphCardsDemo instance.

        Sets up the database, FSRS scheduler, and attempts to load API keys
        from environment variables for AI service integration.
        """
        self.db = VocabularyDatabase()
        self.scheduler = FSRSScheduler()
        self.current_card: Optional[Card] = None
        self.current_time: datetime = datetime.now(timezone.utc)  # Added current_time
        self.mastered_words_override: Optional[List[str]] = (
            None  # Added mastered_words_override
        )

        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY") # Added for OpenAI model name

        if gemini_api_key:
            self.api_key = gemini_api_key
            self.ai_service_type = "gemini"
            self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash") # Get model name
        elif openai_api_key: # Handle OpenAI if Gemini not available
            self.api_key = openai_api_key
            self.ai_service_type = "openai"
            self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo") # Get model name
        else:
            self.api_key = ""
            self.ai_service_type = "gemini" # Default to gemini
            self.model_name = "gemini-2.5-flash" # Default model name

    def add_card(self, word: str, sentence: str, language: str) -> str:
        """Adds a new flashcard to the vocabulary database.

        If a card for the word already exists, it updates the sentence.
        Otherwise, it creates a new card.

        Args:
            word: The word to be learned.
            sentence: A sentence containing the word.
            language: The language of the word and sentence (e.g., "English").

        Returns:
            A string message indicating success or failure.
        """
        if not word.strip() or not sentence.strip():
            return "Please provide both word and sentence."

        existing_card = self.db.get_card_by_word(word.strip())

        if existing_card:
            existing_card.sentence = sentence.strip()
            self.db.update_card(existing_card)
            return f"Updated card for word: {word}\nSentence: {sentence}"
        else:
            card = Card(
                id=f"{word}_{self.current_time.timestamp()}",  # Use current_time
                word=word.strip(),
                sentence=sentence.strip(),
                original_sentence=sentence.strip(),
                stability=None,
                difficulty=None,
                due_date=self.current_time,  # Use current_time
                created_at=self.current_time,  # Use current_time
                language=language,  # Pass the language here
            )
            self.db.add_card(card)
            return f"Added card for word: {word}\nSentence: {sentence}"

    def get_due_cards(self) -> str:
        """Retrieves a list of cards that are due for review.

        Returns:
            A formatted string listing the due cards, or a message indicating
            that no cards are due.
        """
        due_cards = self.db.get_due_cards(self.current_time)  # Use current_time

        if not due_cards:
            return "No cards due for review!"

        result = f"Found {len(due_cards)} cards due for review:\n\n"
        for i, card in enumerate(due_cards, 1):
            result += f"{i}. {card.word}: {card.sentence}\n"

        return result

    def start_review(self) -> Tuple[str, str, str, str, str]:
        """Initiates a review session by fetching the next due card.

        Returns:
            A tuple containing:
            - A string indicating the word being reviewed.
            - The sentence associated with the card.
            - Instructions for rating.
            - A string describing the rating scale.
            - A prompt for user input.
            If no cards are due, returns a tuple of empty strings and a message.
        """
        due_cards = self.db.get_due_cards(self.current_time)  # Use current_time

        if not due_cards:
            return "No cards due for review!", "", "", "", ""

        self.current_card = due_cards[0]

        return (
            f"Reviewing: {self.current_card.word}",
            self.current_card.sentence,
            "Rate your recall:",
            "1 = Again (Forgot), 2 = Hard, 3 = Good, 4 = Easy",
            "Enter your rating (1-4):",
        )

    def submit_review(self, rating_input: str) -> str:
        """Submits the user's review rating for the current card.

        Args:
            rating_input: The user's rating as a string (1-4).

        Returns:
            A string message summarizing the review outcome, including the new
            sentence, next review date, and updated FSRS parameters.
            Returns an.error message if no card is selected or the rating is invalid.
        """
        if not self.current_card:
            return "No card to review. Please start a review first."

        try:
            rating = int(rating_input)
            if rating not in [1, 2, 3, 4]:
                return "Please enter a rating between 1 and 4."
        except ValueError:
            return "Please enter a valid number."

        if not self.api_key:
            return "Please set your API key first."

        try:
            # Process review
            ai_service = AIServiceFactory.create_service(self.ai_service_type, self.model_name)

            updated_card, review_log = self.scheduler.review_card(
                card=self.current_card,
                rating=rating,
                now=self.current_time,  # Use current_time
                ai_api_key=self.api_key,
                vocabulary_database=self.db,
                ai_service=ai_service,
                language=self.current_card.language,  # Pass the language here
                mastered_words_override=self.mastered_words_override,  # Pass the override here
            )

            # Update database
            self.db.update_card(updated_card)
            self.db.add_review_log(review_log)

            result = "Review completed!\n\n"
            result += f"Word: {updated_card.word}\n"
            result += f"New sentence: {updated_card.sentence}\n"
            result += (
                f"Next review: {updated_card.due_date.strftime('%Y-%m-%d %H:%M')}\n"
            )
            result += f"Stability: {updated_card.stability:.2f}\n"
            result += f"Difficulty: {updated_card.difficulty:.2f}"

            self.current_card = None
            return result

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error during review: {e}")  # Added print statement
            return f"Error during review: {str(e)}"

    def skip_to_next_day(self) -> str:
        """Skips the current card's due date to the next day.

        This is primarily for testing and demonstration purposes to quickly advance
        the review schedule of a card.

        Returns:
            A string message indicating the new due date of the skipped card,
            or an error message if no card is currently selected.
        """
        # Remove the check for self.current_card
        # if not self.current_card:
        #     return "No card selected to skip."

        # Advance the due date by one day
        self.current_time += timedelta(days=1)  # Advance current_time
        self.current_card = None  # Clear current card after skipping

        return (
            f"Timeline advanced to next day. Current time: {self.current_time.strftime('%Y-%m-%d %H:%M')}",
            self.current_time.strftime("%Y-%m-%d %H:%M"),
        )

    def set_api_key(self, api_key: str, service_type: str) -> str:
        """Sets the API key and AI service type for sentence generation.

        Args:
            api_key: The API key string.
            service_type: The type of AI service ("openai" or "gemini").

        Returns:
            A string message confirming the API key status.
        """
        self.api_key = api_key.strip()
        self.ai_service_type = service_type

        if not self.api_key:
            return "API key cleared."

        return f"API key set for {service_type} service."

    def set_mastered_words_override(self, words_str: str) -> str:
        """Manually sets a list of mastered words for AI sentence generation override.

        Args:
            words_str: A comma-separated string of words.

        Returns:
            A string message confirming the set words.
        """
        if words_str.strip():
            self.mastered_words_override = [
                word.strip() for word in words_str.split(",") if word.strip()
            ]
            return f"Mastered words set: {', '.join(self.mastered_words_override)}"
        else:
            self.mastered_words_override = None
            return "Mastered words override cleared."

    def get_stats(self) -> str:
        """Retrieves and formats vocabulary statistics from the database.

        Returns:
            A string containing formatted statistics about learned words,
            total cards, and total reviews.
        """
        stats = self.db.get_vocabulary_stats()

        result = "=== Vocabulary Statistics ===\n"
        result += f"Total words learned: {stats['total_words']}\n"
        result += f"Total cards: {stats['total_cards']}\n"
        result += f"Total reviews: {stats['total_reviews']}"

        return result

    def optimize_parameters(self) -> str:
        """Optimizes the FSRS parameters based on the user's review history.

        Returns:
            A string message displaying the optimal FSRS parameters,
            or an error message if insufficient review history is available.
        """
        review_history = self.db.get_review_history()

        if len(review_history) < 10:
            return "Need at least 10 reviews to optimize parameters."

        try:
            # Assuming Optimizer class and its method are defined elsewhere or imported
            # from .core import Optimizer # This import might be missing, add if needed
            from fsrs_optimizer import \
                Optimizer  # Assuming this is the correct import

            optimizer = Optimizer()
            optimal_params = optimizer.optimize_parameters(review_history)

            result = "Optimal FSRS parameters:\n\n"
            for i, param in enumerate(optimal_params):
                result += f"Parameter {i+1}: {param:.6f}\n"

            return result

        except Exception as e:
            return f"Error during optimization: {str(e)}"


def create_demo_interface() -> gr.Interface:
    """Creates and configures the Gradio web interface for MorphCards.

    Returns:
        A Gradio Interface object ready to be launched.
    """
    demo = MorphCardsDemo()

    with gr.Blocks(title="MorphCards Demo", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🎯 MorphCards Demo")
        gr.Markdown(
            "Spaced repetition with AI-generated sentence variations for language learning"
        )

        with gr.Tab("Add Cards"):
            gr.Markdown("### Add New Learning Cards")
            with gr.Row():
                word_input = gr.Textbox(
                    label="Word to learn", placeholder="Enter the word"
                )
                sentence_input = gr.Textbox(
                    label="Sentence", placeholder="Enter a sentence containing the word"
                )
                language_input = gr.Textbox(
                    label="Language",
                    value="English",
                    placeholder="Language of the card",
                )

            add_btn = gr.Button("Add Card", variant="primary")
            add_output = gr.Textbox(label="Result", interactive=False)

            add_btn.click(
                demo.add_card,
                inputs=[word_input, sentence_input, language_input],
                outputs=add_output,
            )

        with gr.Tab("Review Cards"):
            gr.Markdown("### Review Due Cards")

            with gr.Row():
                api_key_input = gr.Textbox(
                    label="API Key",
                    placeholder="Enter your Gemini API key",
                    type="password",
                )
                service_select = gr.Dropdown(
                    choices=["gemini"], value="gemini", label="AI Service"
                )
                set_key_btn = gr.Button("Set API Key")

            with gr.Row():
                mastered_words_input = gr.Textbox(
                    label="Manually Set Mastered Words (comma-separated)",
                    placeholder="e.g., dog, cat, house",
                    lines=2,
                )
                set_mastered_btn = gr.Button("Set Mastered Words")

            key_output = gr.Textbox(label="API Key Status", interactive=False)

            with gr.Row():
                current_date_display = gr.Textbox(
                    label="Current Date",
                    interactive=False,
                    value=demo.current_time.strftime("%Y-%m-%d %H:%M"),
                )
                get_due_btn = gr.Button("Show Due Cards")
                start_review_btn = gr.Button("Start Review", variant="primary")

            due_output = gr.Textbox(label="Due Cards", interactive=False)

            with gr.Row():
                review_word = gr.Textbox(label="Word", interactive=False)
                review_sentence = gr.Textbox(label="Sentence", interactive=False)

            gr.Markdown("### Rate Your Recall")
            rating_instruction = gr.Textbox(label="Instructions", interactive=False)
            rating_input = gr.Textbox(
                label="Your Rating", placeholder="Enter 1, 2, 3, or 4"
            )
            submit_btn = gr.Button("Submit Rating", variant="primary")
            skip_btn = gr.Button(
                "Move Forward By 1 Day", variant="secondary" 
            )  # Renamed button

            review_output = gr.Textbox(label="Review Result", interactive=False)

            # Connect components
            set_key_btn.click(
                demo.set_api_key,
                inputs=[api_key_input, service_select],
                outputs=key_output,
            )

            set_mastered_btn.click(
                demo.set_mastered_words_override,
                inputs=[mastered_words_input],
                outputs=key_output,  # Re-using key_output for simplicity, or create a new one
            )

            get_due_btn.click(demo.get_due_cards, outputs=due_output)

            start_review_btn.click(
                demo.start_review,
                outputs=[
                    review_word,
                    review_sentence,
                    rating_instruction,
                    due_output,
                    rating_input,
                ],
            )

            submit_btn.click(
                demo.submit_review, inputs=[rating_input], outputs=[review_output]
            )

            skip_btn.click(
                demo.skip_to_next_day, outputs=[review_output, current_date_display] 
            )  # Update current_date_display

        with gr.Tab("Statistics"):
            gr.Markdown("### Vocabulary Statistics")
            stats_btn = gr.Button("Get Statistics", variant="primary")
            stats_output = gr.Textbox(label="Statistics", interactive=False)

            stats_btn.click(demo.get_stats, outputs=stats_output)

        with gr.Tab("Optimization"):
            gr.Markdown("### FSRS Parameter Optimization")
            gr.Markdown("Optimize parameters based on your review history")
            optimize_btn = gr.Button("Optimize Parameters", variant="primary")
            optimize_output = gr.Textbox(label="Optimization Result", interactive=False)

            optimize_btn.click(demo.optimize_parameters, outputs=optimize_output)

    return interface


def main() -> gr.Interface:
    """Runs the MorphCards demo interface.

    This function initializes the Gradio interface and launches it,
    making the demo accessible via a web browser.
    """
    interface = create_demo_interface()
    interface.launch(share=False, server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()