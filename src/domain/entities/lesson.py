from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class LessonDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class LessonCategory(Enum):
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    PRONUNCIATION = "pronunciation"
    CONVERSATION = "conversation"
    READING = "reading"
    WRITING = "writing"
    LISTENING = "listening"


@dataclass
class Exercise:
    id: str
    question: str
    options: List[str] = field(default_factory=list)
    correct_answer: str = ""
    explanation: str = ""
    is_open_ended: bool = False


@dataclass
class Lesson:
    id: str
    title: str
    description: str
    content: str
    category: LessonCategory
    difficulty: LessonDifficulty
    exercises: List[Exercise] = field(default_factory=list)
    vocabulary: List[Dict[str, str]] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    estimated_time_minutes: int = 15
    next_lesson_id: Optional[str] = None

    def add_exercise(self, exercise: Exercise):
        self.exercises.append(exercise)

    def add_vocabulary(self, word: str, definition: str, example: str = ""):
        self.vocabulary.append(
            {"word": word, "definition": definition, "example": example}
        )

    def add_example(self, example: str):
        self.examples.append(example)

    def is_grammar_focused(self) -> bool:
        return self.category == LessonCategory.GRAMMAR

    def is_vocabulary_focused(self) -> bool:
        return self.category == LessonCategory.VOCABULARY

    def is_pronunciation_focused(self) -> bool:
        return self.category == LessonCategory.PRONUNCIATION

    def get_content_by_section(self) -> Dict[str, str]:
        """Retorna o conteúdo da lição dividido em seções"""
        sections = {
            "introduction": "",
            "main_content": "",
            "examples": "",
            "practice": "",
            "conclusion": "",
        }

        # Em uma implementação completa, aqui parsearíamos o conteúdo em seções
        # Por simplicidade, apenas dividimos o conteúdo em partes iguais
        parts = self.content.split("\n\n")
        if len(parts) >= 1:
            sections["introduction"] = parts[0]
        if len(parts) >= 2:
            sections["main_content"] = parts[1]
        if len(parts) >= 3:
            sections["examples"] = parts[2]
        if len(parts) >= 4:
            sections["practice"] = parts[3]
        if len(parts) >= 5:
            sections["conclusion"] = parts[4]

        return sections
