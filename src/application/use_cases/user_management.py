import uuid
from typing import Any, Dict, List, Optional

from src.domain.entities.user import ProficiencyLevel, User, UserProgress
from src.domain.interfaces.user_repository import UserRepository


class UserManagementUseCase:
    """Caso de uso para gerenciamento de usuários seguindo o princípio de responsabilidade única"""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register_user(self, discord_id: str, username: str) -> User:
        """Registra um novo usuário no sistema"""
        existing_user = await self.user_repository.get_by_discord_id(discord_id)

        if existing_user:
            return existing_user

        new_user = User(
            id=str(uuid.uuid4()),
            discord_id=discord_id,
            username=username,
            proficiency_level=ProficiencyLevel.BEGINNER,
            progress=UserProgress(),
        )

        return await self.user_repository.save(new_user)

    async def update_user_level(self, user_id: str, new_level: str) -> Optional[User]:
        """Atualiza o nível de proficiência de um usuário"""
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return None

        try:
            user.proficiency_level = ProficiencyLevel(new_level)
            return await self.user_repository.save(user)
        except ValueError:
            # Nível de proficiência inválido
            return None

    async def update_user_progress(
        self, user_id: str, progress_data: Dict[str, Any]
    ) -> Optional[User]:
        """Atualiza o progresso de um usuário"""
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return None

        user.update_progress(
            vocabulary_mastered=progress_data.get("vocabulary_mastered", 0),
            lessons_completed=progress_data.get("lessons_completed", 0),
            practice_sessions=progress_data.get("practice_sessions", 0),
            pronunciation_score=progress_data.get("pronunciation_score", 0.0),
            grammar_accuracy=progress_data.get("grammar_accuracy", 0.0),
            completed_topic=progress_data.get("completed_topic"),
        )

        # Verificar se o usuário pode subir de nível
        if user.should_level_up():
            user.level_up()

        return await self.user_repository.save(user)

    async def get_user_by_discord_id(self, discord_id: str) -> Optional[User]:
        """Recupera um usuário pelo ID do Discord"""
        return await self.user_repository.get_by_discord_id(discord_id)

    async def get_user_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Recupera o progresso de um usuário"""
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return None

        return {
            "username": user.username,
            "proficiency_level": user.proficiency_level.value,
            "vocabulary_mastered": user.progress.vocabulary_mastered,
            "lessons_completed": user.progress.lessons_completed,
            "practice_sessions": user.progress.practice_sessions,
            "pronunciation_score": round(user.progress.pronunciation_score * 100, 1),
            "grammar_accuracy": round(user.progress.grammar_accuracy * 100, 1),
            "completed_topics": user.progress.completed_topics,
            "last_active": (
                user.progress.last_active.isoformat()
                if user.progress.last_active
                else None
            ),
        }

    async def add_to_conversation_history(
        self, user_id: str, role: str, content: str
    ) -> bool:
        """Adiciona uma mensagem ao histórico de conversação do usuário"""
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return False

        user.add_to_conversation_history(role, content)
        user.update_last_interaction()

        await self.user_repository.save(user)
        return True

    async def get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Recupera o histórico de conversação de um usuário"""
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return []

        return user.conversation_history
