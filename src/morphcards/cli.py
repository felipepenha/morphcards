"""Command-line interface for MorphCards."""

import argparse
import sys
from datetime import datetime
from typing import Optional
import os

from .core import Card, Rating, Scheduler, Optimizer
from .database import VocabularyDatabase
from .ai import AIServiceFactory


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MorphCards: Spaced repetition with AI-generated sentence variations (Podman-ready)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add card command
    add_parser = subparsers.add_parser("add", help="Add a new card")
    add_parser.add_argument("word", help="Word to learn")
    add_parser.add_argument("sentence", help="Sentence containing the word")
    add_parser.add_argument("--language", default="English", help="Language of the card")
    
    # Review command
    review_parser = subparsers.add_parser("review", help="Review due cards")
    review_parser.add_argument("--ai-service", choices=["openai", "gemini"], 
                              default="openai", help="AI service to use")
    review_parser.add_argument("--api-key", help="API key for AI service")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show vocabulary statistics")
    
    # Optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Optimize FSRS parameters")
    
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
            review_cards(db, args.ai_service, args.api_key)
        elif args.command == "stats":
            show_stats(db)
        elif args.command == "optimize":
            optimize_parameters(db)
        else:
            parser.print_help()
            sys.exit(1)
    finally:
        db.close()


def add_card(db: VocabularyDatabase, word: str, sentence: str, language: str) -> None:
    """Add a new card to the database."""
    from datetime import datetime, timedelta
    
    card = Card(
        id=f"{word}_{datetime.now().timestamp()}",
        word=word,
        sentence=sentence,
        original_sentence=sentence,
        stability=0.0,
        difficulty=0.0,
        due_date=datetime.now(),
        created_at=datetime.now(),
    )
    
    db.add_card(card)
    print(f"Added card for word: {word}")
    print(f"Sentence: {sentence}")


def review_cards(db: VocabularyDatabase, ai_service_type: str, api_key: Optional[str]) -> None:
    """Review due cards."""
    if not api_key:
        api_key = os.getenv(f"{ai_service_type.upper()}_API_KEY")
        if not api_key:
            print(f"Error: No API key provided for {ai_service_type}")
            print(f"Set {ai_service_type.upper()}_API_KEY environment variable or use --api-key")
            return
    
    # Get due cards
    now = datetime.now()
    due_cards = db.get_due_cards(now)
    
    if not due_cards:
        print("No cards due for review!")
        return
    
    print(f"Found {len(due_cards)} cards due for review")
    
    # Initialize scheduler and AI service
    scheduler = Scheduler()
    ai_service = AIServiceFactory.create_service(ai_service_type)
    
    for card in due_cards:
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


def show_stats(db: VocabularyDatabase) -> None:
    """Show vocabulary statistics."""
    stats = db.get_vocabulary_stats()
    
    print("=== Vocabulary Statistics ===")
    print(f"Total words learned: {stats['total_words']}")
    print(f"Total cards: {stats['total_cards']}")
    print(f"Total reviews: {stats['total_reviews']}")


def optimize_parameters(db: VocabularyDatabase) -> None:
    """Optimize FSRS parameters based on review history."""
    review_history = db.get_review_history()
    
    if len(review_history) < 10:
        print("Need at least 10 reviews to optimize parameters")
        return
    
    print("Optimizing FSRS parameters...")
    optimizer = Optimizer()
    
    try:
        optimal_params = optimizer.optimize_parameters(review_history)
        print("Optimal parameters:")
        for i, param in enumerate(optimal_params):
            print(f"  Parameter {i+1}: {param:.6f}")
        
        print("\nYou can use these parameters when initializing the Scheduler:")
        print(f"  scheduler = Scheduler(parameters={optimal_params})")
        
    except Exception as e:
        print(f"Error during optimization: {e}")


if __name__ == "__main__":
    main()
