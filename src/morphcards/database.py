"""Database module for storing vocabulary and cards."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
from duckdb import DuckDBPyConnection

from .core import Card, ReviewLog


class VocabularyDatabase:
    """Manages the in-memory DuckDB database for storing vocabulary and cards."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or ":memory:"
        self.connection: DuckDBPyConnection = duckdb.connect(self.db_path)
        self._create_tables()

    def _create_tables(self) -> None:
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
                review_count INTEGER NOT NULL DEFAULT 0,
                language VARCHAR NOT NULL DEFAULT 'English'
            )
        """
        )

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
        self.connection.execute(
            """
            INSERT OR REPLACE INTO cards 
            (id, word, sentence, original_sentence, stability, difficulty, 
             due_date, created_at, last_reviewed, review_count, language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                card.language,
            ),
        )

        self.connection.execute(
            """
            INSERT OR IGNORE INTO vocabulary (word, first_seen)
            VALUES (?, ?)
        """,
            (card.word, card.created_at),
        )

    def update_card(self, card: Card) -> None:
        self.add_card(card)

    def update_card_sentence(self, card_id: str, new_sentence: str) -> None:
        """Updates only the sentence for a specific card.

        Args:
            card_id: The ID of the card to update.
            new_sentence: The new sentence to set for the card.
        """
        self.connection.execute(
            """
            UPDATE cards
            SET sentence = ?
            WHERE id = ?
            """,
            (new_sentence, card_id),
        )

    def get_card(self, card_id: str) -> Optional[Card]:
        result = self.connection.execute(
            """
            SELECT id, word, sentence, original_sentence, stability, difficulty,
                   due_date, created_at, last_reviewed, review_count, language
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
                language=result[10],
            )
        return None

    def get_card_by_word(self, word: str, language: str) -> Optional[Card]:
        result = self.connection.execute(
            """
            SELECT id, word, sentence, original_sentence, stability, difficulty,
                   due_date, created_at, last_reviewed, review_count, language
            FROM cards WHERE word = ? AND language = ?
        """,
            (word, language),
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
                language=result[10],
            )
        return None

    def get_due_cards(self, now: datetime, language: Optional[str] = None) -> List[Card]:
        query = """
            SELECT id, word, sentence, original_sentence, stability, difficulty,
                   due_date, created_at, last_reviewed, review_count, language
            FROM cards WHERE due_date <= ?
        """
        params = [now]

        if language:
            query += " AND language = ?"
            params.append(language)

        results = self.connection.execute(query, params).fetchall()

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
                language=result[10],
            )
            cards.append(card)

        return cards

    def add_review_log(self, review_log: ReviewLog) -> None:
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

        # Determine mastery level based on stability
        mastery_level = 1 if review_log.stability >= 10 else 0

        self.connection.execute(
            """
            UPDATE vocabulary
            SET last_reviewed = ?, review_count = review_count + 1, mastery_level = ?
            WHERE word = (SELECT word FROM cards WHERE id = ?)
        """,
            (review_log.review_time, mastery_level, review_log.card_id),
        )

    def get_review_history(self, card_id: Optional[str] = None) -> List[ReviewLog]:
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

    def get_learned_vocabulary(self, language: str) -> List[str]:
        results = self.connection.execute(
            """
            SELECT v.word
            FROM vocabulary v
            JOIN cards c ON v.word = c.word
            WHERE v.mastery_level = 1 AND c.language = ?
            ORDER BY v.first_seen
            """,
            (language,),
        ).fetchall()

        return [result[0] for result in results]

    def get_vocabulary_stats(self, language: Optional[str] = None) -> Dict[str, Any]:
        if language:
            total_words = self.connection.execute(
                """
                SELECT COUNT(DISTINCT c.word)
                FROM cards c
                WHERE c.language = ?
                """,
                (language,),
            ).fetchone()[0]

            total_cards = self.connection.execute(
                """
                SELECT COUNT(*)
                FROM cards
                WHERE language = ?
                """,
                (language,),
            ).fetchone()[0]

            total_reviews = self.connection.execute(
                """
                SELECT COUNT(rl.id)
                FROM review_logs rl
                JOIN cards c ON rl.card_id = c.id
                WHERE c.language = ?
                """,
                (language,),
            ).fetchone()[0]
        else:
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
        self.connection.close()

    def __enter__(self) -> "VocabularyDatabase":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
