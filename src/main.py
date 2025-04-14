import asyncio
import logging
import os
from typing import Any, Dict, List

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from src.application.services.hybrid_ai_service import HybridAIService
from src.application.use_cases.conversation_handler import ConversationHandlerUseCase
from src.application.use_cases.user_management import UserManagementUseCase
from src.domain.interfaces.ai_service import AIService
from src.domain.interfaces.lesson_repository import LessonRepository
from src.domain.interfaces.speech_service import SpeechService
from src.domain.interfaces.user_repository import UserRepository
from src.infrastructure.external.gemini_service import GeminiService
from src.infrastructure.external.groq_service import GroqService
from src.infrastructure.external.speech_service_impl import SpeechServiceImpl
from src.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from src.presentation.commands.base_command import BaseCommand
from src.presentation.commands.learn_command import LearnCommand
from src.presentation.commands.pronounce_command import PronounceCommand
from src.presentation.events.message_handler import MessageHandler

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger("bot")


class EnglishTutorBot:
    """Classe principal do bot educacional de inglês"""

    def __init__(self):
        # Configurações iniciais
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")
        if not self.token:
            raise ValueError("Token do Discord não encontrado no .env")

        # Configuração do cliente do Discord
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.client = discord.Client(intents=intents)
        self.tree = app_commands.CommandTree(self.client)

        # Serviços e repositórios
        self.ai_service = self._setup_ai_service()
        self.speech_service = self._setup_speech_service()
        self.user_repository = self._setup_user_repository()

        # Casos de uso
        self.user_management = UserManagementUseCase(self.user_repository)
        self.conversation_handler = ConversationHandlerUseCase(
            ai_service=self.ai_service, user_repository=self.user_repository
        )

        # Tratador de mensagens - exposto publicamente para acesso
        self.message_handler = MessageHandler(
            conversation_handler=self.conversation_handler,
            user_management=self.user_management,
        )

        # Expor os handlers para os comandos diretamente no cliente
        self.client.message_handler = self.message_handler
        self.client.bot_instance = self

        # Lista de comandos
        self.commands: List[BaseCommand] = []

        # Configuração inicial
        self._setup_event_handlers()
        self._register_commands()

    def _setup_ai_service(self) -> AIService:
        """Configura e retorna o serviço de AI híbrido"""
        # Configurar serviço de conversação Gemini
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("API Key do Google Gemini não encontrada no .env")

        # Configurar serviço Groq para outras funcionalidades
        groq_api_key = os.getenv("OPENAI_API_KEY")
        if not groq_api_key:
            raise ValueError("API Key da Groq não encontrada no .env")

        # Criar os serviços individuais
        conversation_service = GeminiService(api_key=gemini_api_key)
        feature_service = GroqService(api_key=groq_api_key)

        # Retornar serviço híbrido
        logger.info(
            "Configurando serviço híbrido: Gemini para conversação, Groq para outras funcionalidades"
        )
        return HybridAIService(
            conversation_service=conversation_service, feature_service=feature_service
        )

    def _setup_speech_service(self) -> SpeechService:
        """Configura e retorna o serviço de fala"""
        api_key = os.getenv(
            "OPENAI_API_KEY"
        )  # Mantém o nome da variável por compatibilidade
        return SpeechServiceImpl(openai_api_key=api_key)

    def _setup_user_repository(self) -> UserRepository:
        """Configura e retorna o repositório de usuários"""
        database_url = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")
        return SQLAlchemyUserRepository(database_url=database_url)

    def _setup_event_handlers(self) -> None:
        """Configura os manipuladores de eventos do bot"""

        @self.client.event
        async def on_ready():
            logger.info(f"Bot conectado como {self.client.user}")

            # Sincroniza os comandos com o Discord
            await self.tree.sync()
            logger.info("Comandos sincronizados")

            # Status personalizado
            activity = discord.Activity(
                type=discord.ActivityType.listening, name="!help | Aprendendo inglês"
            )
            await self.client.change_presence(activity=activity)

            # Configuração do manipulador de mensagens
            await self.message_handler.setup(self.client)
            logger.info("Manipulador de mensagens configurado")

    def _register_commands(self) -> None:
        """Registra os comandos do bot"""
        # Cria e registra comandos
        self.commands = [
            LearnCommand(
                conversation_handler=self.conversation_handler,
                user_management=self.user_management,
            ),
            PronounceCommand(
                speech_service=self.speech_service, user_management=self.user_management
            ),
            # Adicione mais comandos aqui
        ]

        # Registra cada comando na árvore de comandos
        for command in self.commands:
            command.register(self.tree)

    def run(self) -> None:
        """Inicia o bot"""
        logger.info("Iniciando o bot com serviços híbridos: Gemini + Groq")
        self.client.run(self.token)


if __name__ == "__main__":
    try:
        bot = EnglishTutorBot()
        bot.run()
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}", exc_info=True)
