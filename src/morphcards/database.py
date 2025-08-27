"""Database module for storing vocabulary and cards."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb

from .core import Card, ReviewLog


class VocabularyDatabase:
    """Manages the in-memory DuckDB database for storing vocabulary, cards, and review logs.

    This class provides methods for creating tables, adding/updating cards,
    retrieving due cards, managing review history, and fetching vocabulary statistics.
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initializes the VocabularyDatabase connection.

        Args:
            db_path: Optional path to a DuckDB file. If None, an in-memory database is used.
        """
        self.db_path = db_path or ":memory:"
        self.connection = duckdb.connect(self.db_path)
        self._create_tables()

    def _create_tables(self) -> None:
        """Creates the necessary tables (cards, review_logs, vocabulary) in the database.

        This method is called during initialization to ensure the database schema is set up.
        """
        # Cards table
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cards (
                id VARCHAR PRIMARY KEY,
                word VARCHAR NOT NULL,
                sentence VARCHAR NOT NULL,
                original_sentence VARCHAR NOT NULL,
                stability DOUBLE,
                difficulty DOUBLE,
                due_date TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL,
                last_reviewed TIMESTAMP,
                review_count INTEGER NOT NULL DEFAULT 0
            )
        """
        )

        # Review logs table
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS review_logs (
                id VARCHAR PRIMARY KEY,
                card_id VARCHAR NOT NULL,
                review_time TIMESTAMP NOT NULL,
                rating INTEGER NOT NULL,
                interval DOUBLE NOT NULL,
                stability DOUBLE NOT NULL,
                difficulty DOUBLE NOT NULL,
                FOREIGN KEY (card_id) REFERENCES cards(id)
            )
        """
        )

        # Vocabulary table
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS vocabulary (
                word VARCHAR PRIMARY KEY,
                first_seen TIMESTAMP NOT NULL,
                last_reviewed TIMESTAMP,
                review_count INTEGER NOT NULL DEFAULT 0,
                mastery_level INTEGER NOT NULL DEFAULT 0
            )
        """
        )

    def add_card(self, card: Card) -> None:
        """Adds a new card or updates an existing one in the 'cards' table.

        Also ensures the word from the card is added to the 'vocabulary' table.

        Args:
            card: The Card object to add or update.
        """
        self.connection.execute(
            """
            INSERT OR REPLACE INTO cards 
            (id, word, sentence, original_sentence, stability, difficulty, 
             due_date, created_at, last_reviewed, review_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                card.id,
                card.word,
                card.sentence,
                card.original_sentence,
                card.stability,
                card.difficulty,
                card.due_date,
                card.created_at,
                card.last_reviewed,
                card.review_count,
            ),
        )

        # Add word to vocabulary if not exists
        self.connection.execute(
            """
            INSERT OR IGNORE INTO vocabulary (word, first_seen)
            VALUES (?, ?)
        """,
            (card.word, card.created_at),
        )

    def update_card(self, card: Card) -> None:
        """Updates an existing card in the 'cards' table.

        This method internally uses `add_card` with INSERT OR REPLACE functionality.

        Args:
            card: The Card object with updated information.
        """
        self.add_card(card)  # INSERT OR REPLACE handles updates

    def get_card(self, card_id: str) -> Optional[Card]:
        """Retrieves a single card by its ID from the 'cards' table.

        Args:
            card_id: The unique identifier of the card.

        Returns:
            The Card object if found, otherwise None.
        """
        result = self.connection.execute(
            """
            SELECT id, word, sentence, original_sentence, stability, difficulty,
                   due_date, created_at, last_reviewed, review_count
            FROM cards WHERE id = ?
        """,
            (card_id,),
        ).fetchone()

        if result:
            return Card(
                id=result[0],
                word=result[1],
                sentence=result[2],
                original_sentence=result[3],
                stability=result[4],
                difficulty=result[5],
                due_date=result[6],
                created_at=result[7],
                last_reviewed=result[8],
                review_count=result[9],
            )
        return None

    def get_due_cards(self, now: datetime) -> List[Card]:
        """Retrieves all cards that are due for review based on the current time.

        Args:
            now: The current datetime to compare against card due dates.

        Returns:
            A list of Card objects that are due.
        """
        results = self.connection.execute(
            """
            SELECT id, word, sentence, original_sentence, stability, difficulty,
                   due_date, created_at, last_reviewed, review_count
            FROM cards WHERE due_date <= ?
        """,
            (now,),
        ).fetchall()

        cards = []
        for result in results:
            card = Card(
                id=result[0],
                word=result[1],
                sentence=result[2],
                original_sentence=result[3],
                stability=result[4],
                difficulty=result[5],
                due_date=result[6],
                created_at=result[7],
                last_reviewed=result[8],
                review_count=result[9],
            )
            cards.append(card)

        return cards

    def add_review_log(self, review_log: ReviewLog) -> None:
        """Adds a new review log entry to the 'review_logs' table.

        Also updates the 'vocabulary' table with the latest review time and increments
        the review count for the associated word.

        Args:
            review_log: The ReviewLog object to add.
        """
        self.connection.execute(
            """
            INSERT INTO review_logs 
            (id, card_id, review_time, rating, interval, stability, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                review_log.id,
                review_log.card_id,
                review_log.review_time,
                review_log.rating.value,
                review_log.interval,
                review_log.stability,
                review_log.difficulty,
            ),
        )

        # Update vocabulary review count
        self.connection.execute(
            """
            UPDATE vocabulary 
            SET last_reviewed = ?, review_count = review_count + 1
            WHERE word = (SELECT word FROM cards WHERE id = ?)
        """,
            (review_log.review_time, review_log.card_id),
        )

    def get_review_history(self, card_id: Optional[str] = None) -> List[ReviewLog]:
        """Retrieves the review history from the 'review_logs' table.

        Args:
            card_id: Optional. If provided, filters the review history for a specific card.

        Returns:
            A list of ReviewLog objects, sorted by review time in descending order.
        """
        if card_id:
            results = self.connection.execute(
                """
                SELECT id, card_id, review_time, rating, interval, stability, difficulty
                FROM review_logs WHERE card_id = ?
                ORDER BY review_time DESC
            """,
                (card_id,),
            ).fetchall()
        else:
            results = self.connection.execute(
                """
                SELECT id, card_id, review_time, rating, interval, stability, difficulty
                FROM review_logs ORDER BY review_time DESC
            """
            ).fetchall()

        review_logs = []
        for result in results:
            review_log = ReviewLog(
                id=result[0],
                card_id=result[1],
                review_time=result[2],
                rating=result[3],
                interval=result[4],
                stability=result[5],
                difficulty=result[6],
            )
            review_logs.append(review_log)

        return review_logs

    def get_learned_vocabulary(self) -> List[str]:
        """Retrieves a list of all unique words present in the vocabulary.

        Returns:
            A list of strings, where each string is a learned word.
        """
        results = self.connection.execute(
            """
            SELECT word FROM vocabulary ORDER BY first_seen
        """
        ).fetchall()

        return [result[0] for result in results]

    def get_vocabulary_stats(self) -> Dict[str, Any]:
        """Retrieves various statistics about the vocabulary and reviews.

        Returns:
            A dictionary containing:
            - "total_words": Total number of unique words learned.
            - "total_cards": Total number of cards in the database.
            - "total_reviews": Total number of review log entries.
        """
        total_words = self.connection.execute(
            """
            SELECT COUNT(*) FROM vocabulary
        """
        ).fetchone()[0]

        total_cards = self.connection.execute(
            """
            SELECT COUNT(*) FROM cards
        """
        ).fetchone()[0]

        total_reviews = self.connection.execute(
            """
            SELECT COUNT(*) FROM review_logs
        """
        ).fetchone()[0]

        return {
            "total_words": total_words,
            "total_cards": total_cards,
            "total_reviews": total_reviews,
        }

    def close(self) -> None:
        """Closes the database connection.
        """
        self.connection.close()

    def __enter__(self) -> "VocabularyDatabase":
        """Enables the use of VocabularyDatabase as a context manager.

        Returns:
            The VocabularyDatabase instance itself.
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Handles the exit of the context manager, ensuring the database connection is closed.

        Args:
            exc_type: The type of the exception that caused the context to be exited.
            exc_val: The exception instance.
            exc_tb: A traceback object encapsulating the call stack at the point where the exception originally occurred.
        """
        self.close()
