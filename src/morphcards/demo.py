"""Demo interface for MorphCards using Gradio."""

import gradio as gr
from datetime import datetime
from typing import List, Optional, Tuple
import os

from .core import Card, Rating, FSRSScheduler
from .database import VocabularyDatabase
from .ai import AIServiceFactory


class MorphCardsDemo:
    """Demo interface for MorphCards."""
    
    def __init__(self) -> None:
        """Initialize the demo interface."""
        self.db = VocabularyDatabase()
        self.scheduler = FSRSScheduler()
        self.current_card: Optional[Card] = None
        self.ai_service_type = "openai"
        self.api_key = ""
    
    def add_card(self, word: str, sentence: str, language: str) -> str:
        """Add a new card."""
        if not word.strip() or not sentence.strip():
            return "Please provide both word and sentence."
        
        card = Card(
            id=f"{word}_{datetime.now().timestamp()}",
            word=word.strip(),
            sentence=sentence.strip(),
            original_sentence=sentence.strip(),
            stability=0.0,
            difficulty=0.0,
            due_date=datetime.now(),
            created_at=datetime.now(),
        )
        
        self.db.add_card(card)
        return f"Added card for word: {word}\nSentence: {sentence}"
    
    def get_due_cards(self) -> str:
        """Get list of due cards."""
        due_cards = self.db.get_due_cards(datetime.now())
        
        if not due_cards:
            return "No cards due for review!"
        
        result = f"Found {len(due_cards)} cards due for review:\n\n"
        for i, card in enumerate(due_cards, 1):
            result += f"{i}. {card.word}: {card.sentence}\n"
        
        return result
    
    def start_review(self) -> Tuple[str, str, str, str, str]:
        """Start reviewing due cards."""
        due_cards = self.db.get_due_cards(datetime.now())
        
        if not due_cards:
            return "No cards due for review!", "", "", "", ""
        
        self.current_card = due_cards[0]
        
        return (
            f"Reviewing: {self.current_card.word}",
            self.current_card.sentence,
            "Rate your recall:",
            "1 = Again (Forgot), 2 = Hard, 3 = Good, 4 = Easy",
            "Enter your rating (1-4):"
        )
    
    def submit_review(self, rating_input: str) -> str:
        """Submit a review rating."""
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
            ai_service = AIServiceFactory.create_service(self.ai_service_type)
            
            updated_card, review_log = self.scheduler.review_card(
                card=self.current_card,
                rating=rating,
                now=datetime.now(),
                ai_api_key=self.api_key,
                vocabulary_database=self.db,
                ai_service=ai_service,
            )
            
            # Update database
            self.db.update_card(updated_card)
            self.db.add_review_log(review_log)
            
            result = f"Review completed!\n\n"
            result += f"Word: {updated_card.word}\n"
            result += f"New sentence: {updated_card.sentence}\n"
            result += f"Next review: {updated_card.due_date.strftime('%Y-%m-%d %H:%M')}\n"
            result += f"Stability: {updated_card.stability:.2f}\n"
            result += f"Difficulty: {updated_card.difficulty:.2f}"
            
            self.current_card = None
            return result
            
        except Exception as e:
            return f"Error during review: {str(e)}"
    
    def set_api_key(self, api_key: str, service_type: str) -> str:
        """Set API key and service type."""
        self.api_key = api_key.strip()
        self.ai_service_type = service_type
        
        if not self.api_key:
            return "API key cleared."
        
        return f"API key set for {service_type} service."
    
    def get_stats(self) -> str:
        """Get vocabulary statistics."""
        stats = self.db.get_vocabulary_stats()
        
        result = "=== Vocabulary Statistics ===\n"
        result += f"Total words learned: {stats['total_words']}\n"
        result += f"Total cards: {stats['total_cards']}\n"
        result += f"Total reviews: {stats['total_reviews']}"
        
        return result
    
    def optimize_parameters(self) -> str:
        """Optimize FSRS parameters."""
        review_history = self.db.get_review_history()
        
        if len(review_history) < 10:
            return "Need at least 10 reviews to optimize parameters."
        
        try:
            optimizer = Optimizer()
            optimal_params = optimizer.optimize_parameters(review_history)
            
            result = "Optimal FSRS parameters:\n\n"
            for i, param in enumerate(optimal_params):
                result += f"Parameter {i+1}: {param:.6f}\n"
            
            return result
            
        except Exception as e:
            return f"Error during optimization: {str(e)}"


def create_demo_interface() -> gr.Interface:
    """Create the Gradio demo interface."""
    demo = MorphCardsDemo()
    
    with gr.Blocks(title="MorphCards Demo", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🎯 MorphCards Demo")
        gr.Markdown("Spaced repetition with AI-generated sentence variations for language learning")
        
        with gr.Tab("Add Cards"):
            gr.Markdown("### Add New Learning Cards")
            with gr.Row():
                word_input = gr.Textbox(label="Word to learn", placeholder="Enter the word")
                sentence_input = gr.Textbox(label="Sentence", placeholder="Enter a sentence containing the word")
                language_input = gr.Textbox(label="Language", value="English", placeholder="Language of the card")
            
            add_btn = gr.Button("Add Card", variant="primary")
            add_output = gr.Textbox(label="Result", interactive=False)
            
            add_btn.click(
                demo.add_card,
                inputs=[word_input, sentence_input, language_input],
                outputs=add_output
            )
        
        with gr.Tab("Review Cards"):
            gr.Markdown("### Review Due Cards")
            
            with gr.Row():
                api_key_input = gr.Textbox(
                    label="API Key", 
                    placeholder="Enter your OpenAI or Gemini API key",
                    type="password"
                )
                service_select = gr.Dropdown(
                    choices=["openai", "gemini"],
                    value="openai",
                    label="AI Service"
                )
                set_key_btn = gr.Button("Set API Key")
            
            key_output = gr.Textbox(label="API Key Status", interactive=False)
            
            with gr.Row():
                get_due_btn = gr.Button("Show Due Cards")
                start_review_btn = gr.Button("Start Review", variant="primary")
            
            due_output = gr.Textbox(label="Due Cards", interactive=False)
            
            with gr.Row():
                review_word = gr.Textbox(label="Word", interactive=False)
                review_sentence = gr.Textbox(label="Sentence", interactive=False)
            
            gr.Markdown("### Rate Your Recall")
            rating_instruction = gr.Textbox(label="Instructions", interactive=False)
            rating_input = gr.Textbox(label="Your Rating", placeholder="Enter 1, 2, 3, or 4")
            submit_btn = gr.Button("Submit Rating", variant="primary")
            
            review_output = gr.Textbox(label="Review Result", interactive=False)
            
            # Connect components
            set_key_btn.click(
                demo.set_api_key,
                inputs=[api_key_input, service_select],
                outputs=key_output
            )
            
            get_due_btn.click(
                demo.get_due_cards,
                outputs=due_output
            )
            
            start_review_btn.click(
                demo.start_review,
                outputs=[review_word, review_sentence, rating_instruction, due_output, rating_input]
            )
            
            submit_btn.click(
                demo.submit_review,
                inputs=[rating_input],
                outputs=[review_output]
            )
        
        with gr.Tab("Statistics"):
            gr.Markdown("### Vocabulary Statistics")
            stats_btn = gr.Button("Get Statistics", variant="primary")
            stats_output = gr.Textbox(label="Statistics", interactive=False)
            
            stats_btn.click(
                demo.get_stats,
                outputs=stats_output
            )
        
        with gr.Tab("Optimization"):
            gr.Markdown("### FSRS Parameter Optimization")
            gr.Markdown("Optimize parameters based on your review history")
            optimize_btn = gr.Button("Optimize Parameters", variant="primary")
            optimize_output = gr.Textbox(label="Optimization Result", interactive=False)
            
            optimize_btn.click(
                demo.optimize_parameters,
                outputs=optimize_output
            )
    
    return interface


def main() -> None:
    """Run the demo interface."""
    interface = create_demo_interface()
    interface.launch(share=False, server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
