from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AIService(ABC):
    """Interface para serviços de AI seguindo o princípio de inversão de dependência"""

    @abstractmethod
    async def generate_response(
        self, messages: List[Dict[str, str]], user_level: str, max_tokens: int = 500
    ) -> str:
        """Gera uma resposta com base no histórico de mensagens e nível do usuário"""
        pass

    @abstractmethod
    async def generate_lesson_content(
        self, topic: str, difficulty: str, category: str
    ) -> Dict[str, Any]:
        """Gera conteúdo para uma lição com base no tópico, dificuldade e categoria"""
        pass

    @abstractmethod
    async def generate_exercises(
        self, lesson_content: str, num_exercises: int = 5, difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """Gera exercícios baseados no conteúdo da lição"""
        pass

    @abstractmethod
    async def evaluate_response(
        self, expected_pattern: str, user_response: str, user_level: str
    ) -> Dict[str, Any]:
        """Avalia a resposta do usuário em relação a um padrão esperado"""
        pass

    @abstractmethod
    async def evaluate_pronunciation(
        self, expected_text: str, audio_transcription: str
    ) -> Dict[str, Any]:
        """Avalia a pronúncia do usuário comparando o texto esperado com a transcrição do áudio"""
        pass

    @abstractmethod
    async def generate_vocabulary_list(
        self, text: str, user_level: str, max_items: int = 10
    ) -> List[Dict[str, str]]:
        """Gera uma lista de vocabulário a partir de um texto, adequada ao nível do usuário"""
        pass

    @abstractmethod
    async def translate_text(self, text: str, target_language: str = "pt-br") -> str:
        """Traduz um texto para o idioma de destino"""
        pass
