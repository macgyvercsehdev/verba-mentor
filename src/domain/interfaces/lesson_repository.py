from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.lesson import Lesson, LessonCategory, LessonDifficulty


class LessonRepository(ABC):
    """Interface para o repositório de lições seguindo o princípio de inversão de dependência"""

    @abstractmethod
    async def get_by_id(self, lesson_id: str) -> Optional[Lesson]:
        """Recupera uma lição pelo ID"""
        pass

    @abstractmethod
    async def save(self, lesson: Lesson) -> Lesson:
        """Salva ou atualiza uma lição no repositório"""
        pass

    @abstractmethod
    async def delete(self, lesson_id: str) -> bool:
        """Remove uma lição do repositório"""
        pass

    @abstractmethod
    async def list_all(self) -> List[Lesson]:
        """Lista todas as lições"""
        pass

    @abstractmethod
    async def list_by_category(self, category: LessonCategory) -> List[Lesson]:
        """Lista lições por categoria"""
        pass

    @abstractmethod
    async def list_by_difficulty(self, difficulty: LessonDifficulty) -> List[Lesson]:
        """Lista lições por nível de dificuldade"""
        pass

    @abstractmethod
    async def get_next_lesson(self, current_lesson_id: str) -> Optional[Lesson]:
        """Recupera a próxima lição na sequência"""
        pass

    @abstractmethod
    async def get_recommended_lessons(
        self, user_id: str, limit: int = 5
    ) -> List[Lesson]:
        """Recupera lições recomendadas para um usuário específico"""
        pass
