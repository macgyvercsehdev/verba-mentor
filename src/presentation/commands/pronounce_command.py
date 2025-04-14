import os
import tempfile
from typing import Any, Dict, List, Optional

import discord
from discord import app_commands

from src.application.use_cases.user_management import UserManagementUseCase
from src.domain.interfaces.speech_service import SpeechService
from src.presentation.commands.base_command import SlashCommand


class PronounceCommand(SlashCommand):
    """Comando para avaliar a pronúncia de um usuário"""

    def __init__(
        self, speech_service: SpeechService, user_management: UserManagementUseCase
    ):
        super().__init__(
            name="pronounce",
            description="Avalia sua pronúncia em inglês a partir de um arquivo de áudio",
        )
        self.speech_service = speech_service
        self.user_management = user_management

    def register(self, command_tree: app_commands.CommandTree) -> None:
        """Registra o comando slash na árvore de comandos"""

        @command_tree.command(name=self.name, description=self.description)
        @app_commands.describe(text="Texto que você tentou pronunciar (opcional)")
        async def pronounce_command(
            interaction: discord.Interaction, text: Optional[str] = None
        ):
            await self.execute(interaction, text=text)

    async def execute(self, interaction: discord.Interaction, **kwargs) -> None:
        """Executa o comando de avaliação de pronúncia"""

        # Verifica se o usuário está registrado
        user = await self.user_management.get_user_by_discord_id(
            str(interaction.user.id)
        )
        if not user:
            user = await self.user_management.register_user(
                discord_id=str(interaction.user.id),
                username=interaction.user.display_name,
            )

        # Obtém o texto esperado, se fornecido
        expected_text = kwargs.get("text", "")

        # Responde inicialmente
        await interaction.response.send_message(
            "📝 Para avaliar sua pronúncia, envie um arquivo de áudio como resposta a esta mensagem.\n"
            + (f"Texto esperado: **{expected_text}**\n" if expected_text else "")
            + "Você também pode anexar o arquivo de áudio diretamente ao usar este comando.",
            ephemeral=True,
        )

        # Verifica se já há um arquivo de áudio anexado
        if hasattr(interaction, "attachments") and interaction.attachments:
            attachment = interaction.attachments[0]
            if self._is_valid_audio_file(attachment.filename):
                await self._process_audio_attachment(
                    interaction, attachment, expected_text, user.id
                )

    async def _process_audio_attachment(
        self,
        interaction: discord.Interaction,
        attachment: discord.Attachment,
        expected_text: str,
        user_id: str,
    ) -> None:
        """Processa um anexo de áudio para avaliação de pronúncia"""

        # Informa que está processando
        await interaction.followup.send(
            "🔊 Processando seu áudio, por favor aguarde...", ephemeral=True
        )

        # Processa a gravação de voz
        result = await self.speech_service.process_user_voice_recording(
            discord_attachment_url=attachment.url, user_id=user_id
        )

        if not result.get("success", False):
            await interaction.followup.send(
                f"❌ Não foi possível processar seu áudio: {result.get('error', 'Erro desconhecido')}",
                ephemeral=True,
            )
            return

        transcribed_text = result.get("text", "")

        # Se não tiver texto esperado, apenas mostra a transcrição
        if not expected_text:
            await interaction.followup.send(
                f"📝 Transcrição: **{transcribed_text}**", ephemeral=False
            )
            return

        # Analisa a pronúncia comparando com o texto esperado
        pronunciation_result = await self.speech_service.analyze_pronunciation(
            audio_file_path=result.get(
                "file_path", ""
            ),  # Pode não estar disponível na implementação atual
            expected_text=expected_text,
        )

        # Formata o resultado para o usuário
        score = pronunciation_result.get("pronunciation_score", 0) * 100
        feedback = pronunciation_result.get(
            "feedback", "Não foi possível gerar feedback."
        )

        # Atualiza o progresso do usuário
        await self.user_management.update_user_progress(
            user_id=user_id,
            progress_data={"pronunciation_score": score / 100},  # Normaliza para 0-1
        )

        # Envia o resultado
        embed = discord.Embed(
            title="Avaliação de Pronúncia", color=self._get_score_color(score)
        )
        embed.add_field(name="Texto Esperado", value=expected_text, inline=False)
        embed.add_field(name="Sua Pronúncia", value=transcribed_text, inline=False)
        embed.add_field(name="Pontuação", value=f"{score:.1f}%", inline=True)
        embed.add_field(name="Feedback", value=feedback, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=False)

    def _is_valid_audio_file(self, filename: str) -> bool:
        """Verifica se o arquivo é um formato de áudio válido"""
        valid_extensions = [".mp3", ".wav", ".ogg", ".m4a"]
        ext = os.path.splitext(filename.lower())[1]
        return ext in valid_extensions

    def _get_score_color(self, score: float) -> discord.Color:
        """Retorna uma cor baseada na pontuação"""
        if score >= 90:
            return discord.Color.green()
        elif score >= 70:
            return discord.Color.gold()
        elif score >= 50:
            return discord.Color.orange()
        else:
            return discord.Color.red()
