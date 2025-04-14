from typing import Any, Dict, List, Optional

import discord

from src.application.use_cases.conversation_handler import ConversationHandlerUseCase
from src.application.use_cases.user_management import UserManagementUseCase


class MessageHandler:
    """Classe responsável por tratar mensagens recebidas pelo bot"""

    def __init__(
        self,
        conversation_handler: ConversationHandlerUseCase,
        user_management: UserManagementUseCase,
    ):
        self.conversation_handler = conversation_handler
        self.user_management = user_management

        # Armazenamento em memória de conversas ativas (simulando um repositório)
        # Em uma implementação real, isso estaria em um banco de dados
        self.active_conversations: Dict[int, Dict[str, Any]] = {}

        # Prefixo para comandos de texto (alternativa aos slash commands)
        self.text_prefix = "!"

        print("MessageHandler inicializado")

    async def setup(self, client: discord.Client) -> None:
        """Configura os listeners de eventos"""
        print("Configurando event listeners no MessageHandler")

        @client.event
        async def on_message(message: discord.Message) -> None:
            # Ignora mensagens do próprio bot
            if message.author.bot:
                return

            print(
                f"Mensagem recebida: {message.content[:30]}... de {message.author.display_name}"
            )

            # Processa comandos baseados em texto (para compatibilidade)
            if message.content.startswith(self.text_prefix):
                print(f"Processando comando de texto: {message.content}")
                await self._handle_text_command(message)
                return

            # Verifica se é uma resposta para o bot (resposta direta ou menção)
            is_for_bot = False

            # Verifica se é uma resposta direta a uma mensagem do bot
            if message.reference and message.reference.message_id:
                try:
                    # Tenta buscar a mensagem referenciada
                    ref_msg = await message.channel.fetch_message(
                        message.reference.message_id
                    )
                    if ref_msg.author.id == client.user.id:
                        is_for_bot = True
                        print(f"É uma resposta direta ao bot")
                except Exception as e:
                    print(f"Erro ao buscar mensagem referenciada: {e}")

            # Verifica se o bot foi mencionado
            if client.user.mentioned_in(message):
                is_for_bot = True
                print(f"O bot foi mencionado")

            # Processa a mensagem se for para o bot
            if is_for_bot:
                await self._handle_bot_message(message, client)
                return

            print("Mensagem ignorada (não é comando nem direcionada ao bot)")

        print("Event listeners configurados")

    async def _handle_bot_message(self, message: discord.Message, client) -> None:
        """Trata mensagens direcionadas ao bot"""
        try:
            # Obtém ou registra o usuário
            user = await self.user_management.get_user_by_discord_id(
                str(message.author.id)
            )
            if not user:
                user = await self.user_management.register_user(
                    discord_id=str(message.author.id),
                    username=message.author.display_name,
                )

            # Remove menções ao bot da mensagem
            content = message.content
            for mention in message.mentions:
                if mention.id == client.user.id:
                    content = content.replace(f"<@{mention.id}>", "").strip()
                    content = content.replace(f"<@!{mention.id}>", "").strip()

            # Processa a mensagem
            print(f"Processando mensagem para usuário {user.id}: {content[:30]}...")
            response = await self.conversation_handler.process_message(
                user_id=user.id, message_content=content
            )

            # Envia a resposta
            await message.channel.send(
                f"{response}\n\n*Para continuar a conversa, responda a esta mensagem ou mencione @VerbaMentor*",
                reference=message,
            )

        except Exception as e:
            print(f"ERRO ao processar mensagem: {e}")
            await message.channel.send(
                "Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
                reference=message,
            )

    async def _handle_text_command(self, message: discord.Message) -> None:
        """Trata comandos baseados em texto"""
        content = message.content[len(self.text_prefix) :].strip()

        # Divide em comando e argumentos
        parts = content.split(maxsplit=1)
        command = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        # Obtém ou registra o usuário
        user = await self.user_management.get_user_by_discord_id(str(message.author.id))
        if not user:
            user = await self.user_management.register_user(
                discord_id=str(message.author.id), username=message.author.display_name
            )

        # Lógica para diferentes comandos
        if command == "help":
            await self._send_help_message(message.channel)
        elif command == "learn":
            await self._handle_learn_command(message, args, user.id)
        elif command == "progress":
            await self._handle_progress_command(message, user.id)
        elif (
            command == "debug" and str(message.author.id) == "301044875383447562"
        ):  # Substituir pelo ID do admin
            await self._handle_debug_command(message)
        # Adicione mais comandos conforme necessário

    async def _handle_conversation_message(self, message: discord.Message) -> None:
        """Trata mensagens que são parte de uma conversa ativa"""
        # Obtém os dados da conversa
        conversation_data = self.active_conversations.get(message.reference.message_id)

        if not conversation_data:
            print(
                f"ERRO: Conversa não encontrada para mensagem {message.reference.message_id}"
            )
            await message.channel.send(
                "Desculpe, não consegui recuperar o contexto desta conversa. Por favor, inicie uma nova com `/learn [tópico]`.",
                reference=message,
            )
            return

        user_id = conversation_data.get("user_id")
        print(f"Processando mensagem para usuário {user_id}")

        # Processa a mensagem com o manipulador de conversação
        try:
            response = await self.conversation_handler.process_message(
                user_id=user_id, message_content=message.content
            )

            # Responde ao usuário
            sent_message = await message.channel.send(
                content=f"{response}\n\n*Responda a esta mensagem para continuar a conversa*",
                reference=message,
            )

            # Armazena a nova mensagem como parte da conversa ativa
            conversation_data["message_id"] = sent_message.id
            self.active_conversations[sent_message.id] = conversation_data

            # Mantém o registro da mensagem original também
            self.active_conversations[message.reference.message_id] = conversation_data

            print(f"Resposta enviada, ID: {sent_message.id}")
            print(
                f"Conversas ativas atualizadas: {list(self.active_conversations.keys())}"
            )

        except Exception as e:
            print(f"ERRO ao processar mensagem: {e}")
            await message.channel.send(
                "Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente ou inicie uma nova conversa.",
                reference=message,
            )

    async def _is_part_of_conversation(self, message: discord.Message) -> bool:
        """Verifica se a mensagem é parte de uma conversa ativa"""
        # Verifica se é uma resposta a outra mensagem
        if not message.reference or not message.reference.message_id:
            print(f"Mensagem {message.id} não é uma resposta a nenhuma mensagem")
            return False

        # Obtém o ID da mensagem referenciada
        ref_id = message.reference.message_id
        print(f"Mensagem {message.id} é uma resposta à mensagem {ref_id}")
        print(f"Conversas ativas: {list(self.active_conversations.keys())}")

        # Verifica se a mensagem referenciada é parte de uma conversa ativa
        is_part = ref_id in self.active_conversations

        if not is_part:
            print(f"A mensagem {ref_id} não está nas conversas ativas")
            # Tenta responder para informar o usuário
            try:
                await message.channel.send(
                    "Não consegui encontrar esta conversa no histórico ativo. "
                    "Por favor, inicie uma nova conversa com `/learn [tópico]` ou `!learn [tópico]`.",
                    reference=message,
                )
            except Exception as e:
                print(f"Erro ao enviar mensagem de resposta: {e}")

        return is_part

    async def _handle_learn_command(
        self, message: discord.Message, topic: str, user_id: str
    ) -> None:
        """Trata o comando de aprendizado em formato de texto"""
        if not topic:
            topic = "inglês geral"

        # Envia mensagem inicial
        response_message = await message.channel.send(
            f"🧠 Começando uma sessão de aprendizado sobre **{topic}**. Por favor, aguarde..."
        )

        try:
            # Inicia a sessão de aprendizado
            welcome_message = await self.conversation_handler.start_practice_session(
                user_id=user_id, topic=topic
            )

            # Atualiza a mensagem com o resultado
            await response_message.edit(
                content=f"**Tópico:** {topic}\n\n{welcome_message}\n\n*Para continuar a conversa, responda a esta mensagem ou mencione @VerbaMentor*"
            )

            print(
                f"Sessão de aprendizado iniciada com sucesso para o usuário {user_id} sobre {topic}"
            )

        except Exception as e:
            print(f"ERRO ao iniciar sessão de aprendizado: {e}")
            await response_message.edit(
                content=f"❌ Desculpe, ocorreu um erro ao iniciar a sessão sobre {topic}. Por favor, tente novamente."
            )

    async def _handle_progress_command(
        self, message: discord.Message, user_id: str
    ) -> None:
        """Trata o comando para exibir o progresso do usuário"""
        # Obtém o progresso do usuário
        progress = await self.user_management.get_user_progress(user_id)

        if not progress:
            await message.channel.send(
                "❌ Não foi possível recuperar seu progresso. Por favor, tente novamente mais tarde."
            )
            return

        # Cria um embed para exibir o progresso
        embed = discord.Embed(
            title="Seu Progresso de Aprendizado", color=discord.Color.blue()
        )

        embed.add_field(
            name="Nível", value=progress["proficiency_level"].upper(), inline=True
        )
        embed.add_field(
            name="Vocabulário",
            value=f"{progress['vocabulary_mastered']} palavras",
            inline=True,
        )
        embed.add_field(
            name="Lições",
            value=f"{progress['lessons_completed']} concluídas",
            inline=True,
        )

        embed.add_field(
            name="Pronúncia", value=f"{progress['pronunciation_score']}%", inline=True
        )
        embed.add_field(
            name="Gramática", value=f"{progress['grammar_accuracy']}%", inline=True
        )
        embed.add_field(
            name="Sessões",
            value=f"{progress['practice_sessions']} práticas",
            inline=True,
        )

        # Adiciona tópicos concluídos, se houver
        if progress["completed_topics"]:
            topics = ", ".join(progress["completed_topics"][:5])
            if len(progress["completed_topics"]) > 5:
                topics += f" e mais {len(progress['completed_topics']) - 5}..."

            embed.add_field(name="Tópicos Concluídos", value=topics, inline=False)

        # Adiciona a última atividade
        if progress.get("last_active"):
            embed.set_footer(text=f"Última atividade: {progress['last_active']}")

        await message.channel.send(embed=embed)

    async def _send_help_message(self, channel: discord.TextChannel) -> None:
        """Envia uma mensagem de ajuda com os comandos disponíveis"""
        embed = discord.Embed(
            title="Comandos do Bot",
            description="Aqui estão os comandos disponíveis para ajudar no seu aprendizado de inglês:",
            color=discord.Color.blue(),
        )

        # Comandos slash
        embed.add_field(
            name="Comandos Slash (Recomendados)",
            value=(
                "**/learn [tópico]** - Inicia uma sessão de aprendizado sobre um tópico\n"
                "**/practice** - Inicia uma sessão de prática conversacional\n"
                "**/progress** - Exibe seu progresso de aprendizado\n"
                "**/pronounce [texto]** - Avalia sua pronúncia de uma frase"
            ),
            inline=False,
        )

        # Comandos de texto
        embed.add_field(
            name="Comandos de Texto",
            value=(
                "**!help** - Exibe esta mensagem de ajuda\n"
                "**!learn [tópico]** - Inicia uma sessão de aprendizado\n"
                "**!progress** - Exibe seu progresso de aprendizado"
            ),
            inline=False,
        )

        embed.set_footer(
            text="Responda a qualquer mensagem do bot para continuar a conversa!"
        )

        await channel.send(embed=embed)

    async def _handle_debug_command(self, message: discord.Message) -> None:
        """Comando de debug para ver conversas ativas (somente admin)"""
        active_count = len(self.active_conversations)
        debug_text = f"🔍 Conversas ativas: {active_count}\n\n"

        if active_count == 0:
            debug_text += "Nenhuma conversa ativa no momento."
        else:
            for msg_id, data in self.active_conversations.items():
                user_id = data.get("user_id", "desconhecido")
                topic = data.get("topic", "sem tópico")
                debug_text += f"ID: {msg_id} | Usuário: {user_id} | Tópico: {topic}\n"

        # Dividir em partes se for muito longo
        if len(debug_text) > 1900:
            parts = [debug_text[i : i + 1900] for i in range(0, len(debug_text), 1900)]
            for part in parts:
                await message.channel.send(f"```{part}```")
        else:
            await message.channel.send(f"```{debug_text}```")
