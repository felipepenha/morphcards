#!/usr/bin/env python3
"""Basic usage example for MorphCards."""

import os
from datetime import datetime
from morphcards import Card, Scheduler, VocabularyDatabase
from morphcards.ai import AIServiceFactory
from dotenv import load_dotenv # Import load_dotenv


def main() -> None:
    """Demonstrate basic MorphCards functionality."""
    print("🎯 MorphCards Basic Usage Example")
    print("=" * 50)
    
    # Initialize components
    db = VocabularyDatabase()
    scheduler = Scheduler()
    
    load_dotenv() # Load environment variables

    # Check for API key and model name
    api_key = ""
    ai_service_type = ""
    model_name = ""

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if gemini_api_key:
        api_key = gemini_api_key
        ai_service_type = "gemini"
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
    elif openai_api_key:
        api_key = openai_api_key
        ai_service_type = "openai"
        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    else:
        print("⚠️ No API key found. Set GEMINI_API_KEY or OPENAI_API_KEY environment variable.")
        print("   Using fallback mode (no AI sentence generation).")
        api_key = "dummy-key" # Provide a dummy key to avoid errors if no AI service is configured
        ai_service_type = "gemini" # Default to gemini service type
        model_name = "gemini-2.5-flash" # Default model name

    ai_service = AIServiceFactory.create_service(ai_service_type, model_name)
    
    try:
        # Create some sample cards
        print("\n📝 Creating sample cards...")
        
        cards_data = [
            ("bonjour", "Bonjour, comment allez-vous?", "French"),
            ("hello", "Hello, how are you?", "English"),
            ("hola", "¡Hola! ¿Cómo estás?", "Spanish"),
        ]
        
        for word, sentence, language in cards_data:
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
            print(f"   ✅ Added: {word} ({language})")
        
        # Show initial stats
        print("\n📊 Initial statistics:")
        stats = db.get_vocabulary_stats()
        print(f"   Total words: {stats['total_words']}")
        print(f"   Total cards: {stats['total_cards']}")
        
        # Get due cards
        print("\n🔄 Getting due cards...")
        due_cards = db.get_due_cards(datetime.now())
        print(f"   Found {len(due_cards)} cards due for review")
        
        if due_cards:
            # Review the first card
            card = due_cards[0]
            print(f"\n📖 Reviewing card: {card.word}")
            print(f"   Current sentence: {card.sentence}")
            
            # Simulate a "Good" rating (3)
            print("   Rating: Good (3)")
            
            # Process review
            updated_card, review_log = scheduler.review_card(
                card=card,
                rating=3,
                now=datetime.now(),
                ai_api_key=api_key,
                vocabulary_database=db,
                ai_service=ai_service,
            )
            
            # Update database
            db.update_card(updated_card)
            db.add_review_log(review_log)
            
            print(f"\n✅ Review completed!")
            print(f"   New sentence: {updated_card.sentence}")
            print(f"   Next review: {updated_card.due_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Stability: {updated_card.stability:.2f}")
            print(f"   Difficulty: {updated_card.difficulty:.2f}")
        
        # Show final stats
        print("\n📊 Final statistics:")
        stats = db.get_vocabulary_stats()
        print(f"   Total words: {stats['total_words']}")
        print(f"   Total cards: {stats['total_cards']}")
        print(f"   Total reviews: {stats['total_reviews']}")
        
        print("\n🎉 Example completed successfully!")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()