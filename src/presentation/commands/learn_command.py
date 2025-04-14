import asyncio
from typing import Any, Dict, Optional

import discord
from discord import app_commands

from src.application.use_cases.conversation_handler import ConversationHandlerUseCase
from src.application.use_cases.user_management import UserManagementUseCase
from src.presentation.commands.base_command import SlashCommand


class LearnCommand(SlashCommand):
    """Comando para iniciar uma sessão de aprendizado sobre um tópico específico"""

    def __init__(
        self,
        conversation_handler: ConversationHandlerUseCase,
        user_management: UserManagementUseCase,
    ):
        super().__init__(
            name="learn",
            description="Inicia uma sessão de aprendizado sobre um tópico específico",
        )
        self.conversation_handler = conversation_handler
        self.user_management = user_management

    def register(self, command_tree: app_commands.CommandTree) -> None:
        """Registra o comando slash na árvore de comandos"""

        @command_tree.command(name=self.name, description=self.description)
        @app_commands.describe(topic="Tópico que você deseja aprender")
        async def learn_command(interaction: discord.Interaction, topic: str):
            await self.execute(interaction, topic=topic)

    async def execute(self, interaction: discord.Interaction, **kwargs) -> None:
        """Executa o comando de aprendizado"""

        # Obtém o tópico da interação
        topic = kwargs.get("topic", "inglês geral")

        # Obtém o usuário ou registra um novo
        user = await self.user_management.get_user_by_discord_id(
            str(interaction.user.id)
        )
        if not user:
            user = await self.user_management.register_user(
                discord_id=str(interaction.user.id),
                username=interaction.user.display_name,
            )

        # Responde a interação inicialmente
        await interaction.response.send_message(
            f"🧠 Iniciando uma sessão com seu tutor sobre **{topic}**. Por favor, aguarde...",
            ephemeral=False,
        )

        try:
            # Inicia a sessão de aprendizado
            welcome_message = await self.conversation_handler.start_practice_session(
                user_id=user.id, topic=topic
            )

            # Envia o resultado
            await interaction.followup.send(
                f"**Tópico:** {topic}\n\n{welcome_message}\n\n*Para continuar a conversa, basta responder a esta mensagem ou mencionar @VerbaMentor*"
            )

            print(
                f"Sessão de aprendizado iniciada com sucesso para o usuário {user.id} sobre {topic}"
            )

        except Exception as e:
            print(f"ERRO ao executar comando learn: {e}")
            await interaction.followup.send(
                f"❌ Desculpe, ocorreu um erro ao iniciar a sessão sobre {topic}. Por favor, tente novamente."
            )
