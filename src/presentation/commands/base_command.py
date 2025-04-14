from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

import discord
from discord import app_commands


class BaseCommand(ABC):
    """Classe base abstrata para todos os comandos do bot seguindo o princípio de aberto/fechado"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, interaction: discord.Interaction, **kwargs) -> None:
        """Executa o comando com base na interação recebida"""
        pass

    def register(self, command_tree: app_commands.CommandTree) -> None:
        """Registra o comando na árvore de comandos do Discord"""
        pass


class SlashCommand(BaseCommand):
    """Implementação para comandos do tipo slash"""

    def __init__(
        self,
        name: str,
        description: str,
        options: Optional[List[discord.app_commands.commands.Command]] = None,
    ):
        super().__init__(name, description)
        self.options = options or []

    def register(self, command_tree: app_commands.CommandTree) -> None:
        """Registra o comando slash na árvore de comandos"""

        # Define uma função wrapper para o método execute
        async def command_callback(interaction: discord.Interaction, **kwargs):
            await self.execute(interaction, **kwargs)

        # Cria o comando com opções
        command = app_commands.Command(
            name=self.name, description=self.description, callback=command_callback
        )

        # Adiciona as opções ao comando - versão atualizada
        for option in self.options:
            command._params.update(option._params)

        # Registra o comando na árvore
        command_tree.add_command(command)


class MessageContextCommand(BaseCommand):
    """Implementação para comandos de contexto de mensagem"""

    def register(self, command_tree: app_commands.CommandTree) -> None:
        """Registra o comando de contexto de mensagem na árvore de comandos"""

        @command_tree.context_menu(name=self.name)
        async def context_menu_command(
            interaction: discord.Interaction, message: discord.Message
        ):
            await self.execute(interaction, message=message)


class ModalCommand(BaseCommand):
    """Implementação para comandos que abrem um modal"""

    def __init__(self, name: str, description: str, modal_class):
        super().__init__(name, description)
        self.modal_class = modal_class

    async def execute(self, interaction: discord.Interaction, **kwargs) -> None:
        """Abre o modal quando o comando é executado"""
        modal = self.modal_class()
        await interaction.response.send_modal(modal)
