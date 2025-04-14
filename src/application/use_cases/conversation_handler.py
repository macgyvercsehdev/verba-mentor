from typing import Any, Dict, List, Optional

from src.domain.entities.user import User
from src.domain.interfaces.ai_service import AIService
from src.domain.interfaces.user_repository import UserRepository


class ConversationHandlerUseCase:
    """Caso de uso para lidar com conversações seguindo o princípio de responsabilidade única"""

    def __init__(self, ai_service: AIService, user_repository: UserRepository):
        self.ai_service = ai_service
        self.user_repository = user_repository

    async def process_message(self, user_id: str, message_content: str) -> str:
        """Processa uma mensagem de texto de um usuário e gera uma resposta apropriada"""
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return "Desculpe, não consegui encontrar seu registro. Por favor, registre-se primeiro."

        # Adicionar mensagem do usuário ao histórico
        user.add_to_conversation_history("user", message_content)
        user.update_last_interaction()

        # Preparar o contexto para a AI com base no nível do usuário
        messages = self._prepare_context_for_ai(user)

        # Gerar resposta usando a IA
        response = await self.ai_service.generate_response(
            messages=messages, user_level=user.proficiency_level.value
        )

        # Adicionar resposta ao histórico
        user.add_to_conversation_history("assistant", response)

        # Salvar usuário atualizado
        await self.user_repository.save(user)

        return response

    async def start_practice_session(
        self, user_id: str, topic: Optional[str] = None
    ) -> str:
        """Inicia uma sessão de prática conversacional com um usuário"""
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return "Desculpe, não consegui encontrar seu registro. Por favor, registre-se primeiro."

        # Preparar mensagem de sistema específica para prática
        practice_prompt = self._get_practice_prompt(user.proficiency_level.value, topic)

        # Adicionar instruções explícitas para iniciar a conversa corretamente
        initial_instructions = (
            "IMPORTANTE: Esta é uma nova conversa sendo iniciada. "
            "Você é o tutor de inglês VerbaMentor e está aqui para ensinar um aluno. "
            "Ao responder a primeira mensagem, apresente-se como o tutor, "
            "explique o tópico de hoje e faça uma pergunta introdutória ao aluno. "
            "NUNCA comece a conversa agindo como se o aluno tivesse oferecido ajuda a você. "
            "Esta é uma nova conversa, então não faça referência a conversas anteriores."
        )

        # Limpar histórico de conversação anterior para iniciar uma nova sessão
        user.conversation_history = []

        # Adicionar contexto inicial com instruções explícitas
        combined_prompt = f"{initial_instructions}\n\n{practice_prompt}"
        user.add_to_conversation_history("system", combined_prompt)
        user.update_last_interaction()

        # Gerar mensagem inicial com instruções explícitas para primeira resposta
        intro_prompt = "Olá! Nova sessão de tutoria iniciada sobre o tema: " + (
            topic if topic else "gramática inglesa"
        )
        messages = [
            {"role": "system", "content": combined_prompt},
            {"role": "user", "content": intro_prompt},
        ]

        welcome_message = await self.ai_service.generate_response(
            messages=messages,
            user_level=user.proficiency_level.value,
        )

        # Adicionar resposta do assistente ao histórico
        user.add_to_conversation_history("assistant", welcome_message)

        # Atualizar progresso do usuário - incrementar sessões de prática
        user.update_progress(practice_sessions=1)

        # Salvar usuário atualizado
        await self.user_repository.save(user)

        return welcome_message

    async def evaluate_user_response(
        self, user_id: str, user_response: str, expected_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Avalia a resposta de um usuário e fornece feedback"""
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return {"error": "Usuário não encontrado"}

        # Se não houver um padrão esperado, usamos o contexto conversacional
        if not expected_pattern and user.conversation_history:
            # Pegar a última mensagem do assistente como contexto
            assistant_messages = [
                msg
                for msg in user.conversation_history
                if msg.get("role") == "assistant"
            ]

            if assistant_messages:
                last_message = assistant_messages[-1].get("content", "")
                # Usar a última mensagem como contexto para avaliação
                evaluation = await self.ai_service.evaluate_response(
                    expected_pattern=last_message,
                    user_response=user_response,
                    user_level=user.proficiency_level.value,
                )
                return evaluation

        # Caso tenha um padrão esperado específico
        if expected_pattern:
            evaluation = await self.ai_service.evaluate_response(
                expected_pattern=expected_pattern,
                user_response=user_response,
                user_level=user.proficiency_level.value,
            )

            # Atualizar progresso com base na avaliação
            if "grammar_score" in evaluation:
                user.update_progress(grammar_accuracy=evaluation["grammar_score"])
                await self.user_repository.save(user)

            return evaluation

        return {"error": "Não foi possível avaliar a resposta sem contexto adequado"}

    def _prepare_context_for_ai(self, user: User) -> List[Dict[str, str]]:
        """Prepara o contexto para enviar à IA com base no usuário"""
        # Inicializar com uma mensagem de sistema
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt(user.proficiency_level.value),
            }
        ]

        # Adicionar histórico de conversação recente
        for message in user.conversation_history:
            if "role" in message and "content" in message:
                messages.append(
                    {"role": message["role"], "content": message["content"]}
                )

        return messages

    def _get_system_prompt(self, user_level: str) -> str:
        """Obtém o prompt de sistema apropriado com base no nível do usuário"""
        base_prompt = (
            "Você é um tutor de inglês amigável e paciente. "
            "Seu objetivo é ajudar o aluno a aprender inglês de forma natural e eficaz. "
            "SEMPRE responda em português brasileiro, exceto quando demonstrar exemplos em inglês. "
            "NUNCA responda como se você fosse o aluno ou como se não precisasse de ajuda com inglês. "
            "IMPORTANTE: Você é o TUTOR, não o aluno. Nunca responda com frases como "
            "'Como tutor, eu não preciso de ajuda com meu inglês' ou 'Eu sou o tutor, não preciso aprender inglês', "
            "pois isso confunde os papéis. O usuário que está enviando mensagens é sempre o aluno "
            "que precisa da sua ajuda para aprender inglês. "
            "Seu papel é ajudar alunos brasileiros a aprenderem inglês, não o contrário. "
        )

        if user_level == "beginner":
            return base_prompt + (
                "Este aluno está no nível INICIANTE. Use vocabulário simples, frases curtas, e "
                "explique conceitos básicos. Use português para explicações. "
                "Encoraje o uso de inglês simples e ofereça muitos exemplos básicos."
            )
        elif user_level == "intermediate":
            return base_prompt + (
                "Este aluno está no nível INTERMEDIÁRIO. Use vocabulário mais diversificado, "
                "construções gramaticais de média complexidade e use português para explicações "
                "mais complexas. Corrija erros gentilmente e explique os motivos."
            )
        elif user_level == "advanced":
            return base_prompt + (
                "Este aluno está no nível AVANÇADO. Use vocabulário rico, expressões idiomáticas, "
                "e estruturas gramaticais complexas. Foque em nuances da língua, pronúncia refinada "
                "e fluência. Corrija apenas erros significativos e desafie o aluno."
            )
        else:
            return base_prompt

    def _get_practice_prompt(self, user_level: str, topic: Optional[str] = None) -> str:
        """Obtém o prompt para uma sessão de prática baseado no nível e tópico"""
        base_prompt = (
            "Você é um tutor de inglês conduzindo uma sessão de prática conversacional. "
            "Faça perguntas, encoraje respostas e forneça feedback gentil. "
            "SEMPRE responda em português brasileiro, exceto quando demonstrar exemplos em inglês. "
            "NUNCA responda como se você fosse o aluno ou como se não precisasse de ajuda com inglês. "
            "Como tutor, seu papel é ajudar alunos brasileiros a aprenderem inglês, não o contrário. "
            "IMPORTANTE: Você NUNCA deve dizer frases como 'Como tutor, eu não preciso de ajuda com meu inglês', "
            "pois isso é confundir seu papel. Você deve assumir que o usuário é o aluno que precisa de sua ajuda. "
        )

        topic_context = ""
        if topic:
            topic_context = f"O tópico desta sessão é: {topic}. "

        level_context = ""
        if user_level == "beginner":
            level_context = (
                "O aluno é INICIANTE. Use vocabulário simples, faça perguntas básicas "
                "e forneça muito suporte. Corrija erros fundamentais."
            )
        elif user_level == "intermediate":
            level_context = (
                "O aluno é INTERMEDIÁRIO. Use vocabulário mais diversificado, "
                "faça perguntas abertas e discuta tópicos de média complexidade."
            )
        elif user_level == "advanced":
            level_context = (
                "O aluno é AVANÇADO. Use vocabulário rico, discuta tópicos complexos, "
                "utilize expressões idiomáticas e estimule o pensamento crítico."
            )

        return base_prompt + topic_context + level_context
