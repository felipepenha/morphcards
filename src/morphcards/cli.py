"""Command-line interface for MorphCards."""

import argparse
import os
import sys
from datetime import datetime
from typing import Optional

from .ai import AIServiceFactory
from .core import Card, Rating, Scheduler
from .database import VocabularyDatabase


def main() -> None:
    """Main entry point for the MorphCards command-line interface.

    Parses command-line arguments and dispatches to the appropriate
    function (add, review, stats).
    """
    parser = argparse.ArgumentParser(
        description="MorphCards: Spaced repetition with AI-generated sentence variations (Podman-ready)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add card command
    add_parser = subparsers.add_parser("add", help="Add a new card")
    add_parser.add_argument("word", help="Word to learn")
    add_parser.add_argument("sentence", help="Sentence containing the word")
    add_parser.add_argument(
        "--language", default="English", help="Language of the card"
    )

    # Review command
    review_parser = subparsers.add_parser("review", help="Review due cards")
    review_parser.add_argument(
        "--language", help="Language to review"
    )
    review_parser.add_argument(
        "--ai-service",
        choices=["openai", "gemini"],
        default="openai",
        help="AI service to use",
    )
    review_parser.add_argument(
        "--model-name",
        help="Specific model name to use (e.g., gpt-3.5-turbo, gemini-2.5-flash)",
    )
    review_parser.add_argument("--api-key", help="API key for AI service")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show vocabulary statistics")
    stats_parser.add_argument(
        "--language", help="Language to show stats for"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize database
    db = VocabularyDatabase()

    try:
        if args.command == "add":
            add_card(db, args.word, args.sentence, args.language)
        elif args.command == "review":
            review_cards(
                db,
                args.ai_service,
                args.api_key,
                args.model_name,
                args.language,
            )
        elif args.command == "stats":
            show_stats(db, args.language)
        else:
            parser.print_help()
            sys.exit(1)
    finally:
        db.close()


def review_cards(
    db: VocabularyDatabase,
    ai_service_type: str,
    api_key: Optional[str],
    model_name: Optional[str],
    language: Optional[str] = None,
) -> None:
    """Initiates a review session for due cards.

    Args:
        db: The VocabularyDatabase instance.
        ai_service_type: The type of AI service to use ("openai" or "gemini").
        api_key: The API key for the AI service. Can be None if loaded from environment.
        model_name: The specific AI model to use.
        language: The language to review. If None, review all languages.
    """
    if not api_key:
        api_key = os.getenv(f"{ai_service_type.upper()}_API_KEY")
        if not api_key:
            print(f"Error: No API key provided for {ai_service_type}")
            print(
                f"Set {ai_service_type.upper()}_API_KEY environment variable or use --api-key"
            )
            return

    # Get due cards
    now = datetime.now()
    due_cards = db.get_due_cards(now, language=language)

    if not due_cards:
        print("No cards due for review!")
        return

    print(f"Found {len(due_cards)} cards due for review")

    # Group cards by language
    cards_by_language: dict[str, list[Card]] = {}
    for card in due_cards:
        if card.language not in cards_by_language:
            cards_by_language[card.language] = []
        cards_by_language[card.language].append(card)

    for lang, cards in cards_by_language.items():
        print(f"\n--- Reviewing {lang} cards --- ({len(cards)} cards)")
        # Initialize scheduler and AI service
        scheduler = Scheduler()
        ai_service = AIServiceFactory.create_service(ai_service_type, model_name)

        for card in cards:
            print(f"\n--- Reviewing: {card.word} ---")
            print(f"Current sentence: {card.sentence}")

            # Get user rating
            while True:
                try:
                    rating_input = input(
                        "Rate your recall (1=Again, 2=Hard, 3=Good, 4=Easy): "
                    ).strip()
                    rating = int(rating_input)
                    if rating in [1, 2, 3, 4]:
                        break
                    else:
                        print("Please enter a number between 1 and 4")
                except ValueError:
                    print("Please enter a valid number")

            # Process review
            updated_card, review_log = scheduler.review_card(
                card=card,
                rating=rating,
                now=now,
                ai_api_key=api_key,
                vocabulary_database=db,
                ai_service=ai_service,
            )

            # Update database
            db.update_card(updated_card)
            db.add_review_log(review_log)

            print(f"New sentence: {updated_card.sentence}")
            print(f"Next review: {updated_card.due_date}")
            print(f"Stability: {updated_card.stability:.2f}")
            print(f"Difficulty: {updated_card.difficulty:.2f}")


def show_stats(db: VocabularyDatabase, language: Optional[str] = None) -> None:
    """Displays vocabulary statistics.

    Args:
        db: The VocabularyDatabase instance.
        language: The language to show stats for. If None, show stats for all languages.
    """
    stats = db.get_vocabulary_stats(language=language)

    if language:
        print(f"=== Vocabulary Statistics for {language} ===")
    else:
        print("=== Vocabulary Statistics ===")
    print(f"Total words learned: {stats['total_words']}")
    print(f"Total cards: {stats['total_cards']}")
    print(f"Total reviews: {stats['total_reviews']}")


if __name__ == "__main__":
    main()
