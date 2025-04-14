from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.user import User


class UserRepository(ABC):
    """Interface para o repositório de usuários seguindo o princípio de inversão de dependência"""

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Recupera um usuário pelo ID"""
        pass

    @abstractmethod
    async def get_by_discord_id(self, discord_id: str) -> Optional[User]:
        """Recupera um usuário pelo ID do Discord"""
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """Salva ou atualiza um usuário no repositório"""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Remove um usuário do repositório"""
        pass

    @abstractmethod
    async def list_all(self) -> List[User]:
        """Lista todos os usuários"""
        pass

    @abstractmethod
    async def list_by_proficiency(self, proficiency_level: str) -> List[User]:
        """Lista usuários por nível de proficiência"""
        pass

    @abstractmethod
    async def get_user_statistics(self) -> dict:
        """Retorna estatísticas agregadas sobre os usuários"""
        pass
