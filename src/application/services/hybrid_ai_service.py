from typing import Any, Dict, List, Optional

from src.domain.interfaces.ai_service import AIService


class HybridAIService(AIService):
    """
    Implementação híbrida do serviço AI que usa diferentes serviços para cada funcionalidade.
    Usa Gemini para conversação e Groq para as demais funcionalidades.
    """

    def __init__(self, conversation_service: AIService, feature_service: AIService):
        """
        Inicializa o serviço híbrido com os serviços específicos.

        Args:
            conversation_service: Serviço para conversação (Gemini)
            feature_service: Serviço para outras funcionalidades (Groq)
        """
        self.conversation_service = conversation_service
        self.feature_service = feature_service

    async def generate_response(
        self, messages: List[Dict[str, str]], user_level: str, max_tokens: int = 500
    ) -> str:
        """Delega a geração de respostas conversacionais para o Gemini"""
        return await self.conversation_service.generate_response(
            messages=messages, user_level=user_level, max_tokens=max_tokens
        )

    async def generate_lesson_content(
        self, topic: str, difficulty: str, category: str
    ) -> Dict[str, Any]:
        """Delega a geração de conteúdo de lições para o Groq"""
        return await self.feature_service.generate_lesson_content(
            topic=topic, difficulty=difficulty, category=category
        )

    async def generate_exercises(
        self, lesson_content: str, num_exercises: int = 5, difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """Delega a geração de exercícios para o Groq"""
        return await self.feature_service.generate_exercises(
            lesson_content=lesson_content,
            num_exercises=num_exercises,
            difficulty=difficulty,
        )

    async def evaluate_response(
        self, expected_pattern: str, user_response: str, user_level: str
    ) -> Dict[str, Any]:
        """Delega a avaliação de respostas para o Groq"""
        return await self.feature_service.evaluate_response(
            expected_pattern=expected_pattern,
            user_response=user_response,
            user_level=user_level,
        )

    async def evaluate_pronunciation(
        self, expected_text: str, audio_transcription: str
    ) -> Dict[str, Any]:
        """Delega a avaliação de pronúncia para o Groq"""
        return await self.feature_service.evaluate_pronunciation(
            expected_text=expected_text, audio_transcription=audio_transcription
        )

    async def generate_vocabulary_list(
        self, text: str, user_level: str, max_items: int = 10
    ) -> List[Dict[str, str]]:
        """Delega a geração de lista de vocabulário para o Groq"""
        return await self.feature_service.generate_vocabulary_list(
            text=text, user_level=user_level, max_items=max_items
        )

    async def translate_text(self, text: str, target_language: str = "pt-br") -> str:
        """Delega a tradução de texto para o Groq"""
        return await self.feature_service.translate_text(
            text=text, target_language=target_language
        )
