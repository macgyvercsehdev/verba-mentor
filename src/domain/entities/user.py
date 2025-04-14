from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ProficiencyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class UserProgress:
    vocabulary_mastered: int = 0
    lessons_completed: int = 0
    practice_sessions: int = 0
    pronunciation_score: float = 0.0
    grammar_accuracy: float = 0.0
    last_active: datetime = field(default_factory=datetime.now)
    completed_topics: List[str] = field(default_factory=list)


@dataclass
class User:
    id: str
    discord_id: str
    username: str
    proficiency_level: ProficiencyLevel = ProficiencyLevel.BEGINNER
    progress: UserProgress = field(default_factory=UserProgress)
    conversation_history: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_interaction: Optional[datetime] = None

    def update_last_interaction(self):
        self.last_interaction = datetime.now()
        self.progress.last_active = datetime.now()

    def update_progress(
        self,
        vocabulary_mastered: int = 0,
        lessons_completed: int = 0,
        practice_sessions: int = 0,
        pronunciation_score: float = 0.0,
        grammar_accuracy: float = 0.0,
        completed_topic: Optional[str] = None,
    ):
        self.progress.vocabulary_mastered += vocabulary_mastered
        self.progress.lessons_completed += lessons_completed
        self.progress.practice_sessions += practice_sessions

        # Update scores with weighted average to prevent sudden jumps
        if pronunciation_score > 0:
            self.progress.pronunciation_score = (
                self.progress.pronunciation_score * 0.7 + pronunciation_score * 0.3
            )

        if grammar_accuracy > 0:
            self.progress.grammar_accuracy = (
                self.progress.grammar_accuracy * 0.7 + grammar_accuracy * 0.3
            )

        if completed_topic and completed_topic not in self.progress.completed_topics:
            self.progress.completed_topics.append(completed_topic)

    def should_level_up(self) -> bool:
        """Verifica se o usuário deve subir de nível com base no progresso"""
        if self.proficiency_level == ProficiencyLevel.BEGINNER:
            return (
                self.progress.lessons_completed >= 10
                and self.progress.pronunciation_score >= 0.7
                and self.progress.grammar_accuracy >= 0.7
            )
        elif self.proficiency_level == ProficiencyLevel.INTERMEDIATE:
            return (
                self.progress.lessons_completed >= 25
                and self.progress.pronunciation_score >= 0.8
                and self.progress.grammar_accuracy >= 0.8
            )
        return False

    def level_up(self) -> bool:
        """Tenta aumentar o nível de proficiência do usuário"""
        if not self.should_level_up():
            return False

        if self.proficiency_level == ProficiencyLevel.BEGINNER:
            self.proficiency_level = ProficiencyLevel.INTERMEDIATE
            return True
        elif self.proficiency_level == ProficiencyLevel.INTERMEDIATE:
            self.proficiency_level = ProficiencyLevel.ADVANCED
            return True
        return False

    def add_to_conversation_history(self, role: str, content: str):
        """Adiciona uma mensagem ao histórico de conversação"""
        self.conversation_history.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

        # Limita o histórico para as últimas 20 mensagens para evitar tokens excessivos
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
