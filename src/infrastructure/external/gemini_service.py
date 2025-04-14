import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory

from src.domain.interfaces.ai_service import AIService


class GeminiService(AIService):
    """Implementação parcial do serviço de AI usando a API do Google Gemini apenas para conversação"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key do Google Gemini não fornecida")

        # Configurar a API Gemini
        genai.configure(api_key=self.api_key)

        # Configurações do modelo
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }

        # Configurações de segurança
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        # Criar o modelo
        try:
            # Utilizar modelo gemini-pro por ser mais estável
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
            )
            print("Modelo Gemini-Pro inicializado com sucesso")
        except Exception as e:
            print(f"Erro ao inicializar o modelo Gemini: {e}")
            raise ValueError(f"Não foi possível inicializar o modelo Gemini. Erro: {e}")

    async def generate_response(
        self, messages: List[Dict[str, str]], user_level: str, max_tokens: int = 500
    ) -> str:
        """Gera uma resposta com base no histórico de mensagens e nível do usuário"""
        try:
            # Definir uma mensagem de sistema clara e explícita
            strong_instructions = (
                "INSTRUÇÕES IMPORTANTES: Você é o VerbaMentor, um tutor de inglês que ajuda alunos brasileiros. "
                f"O aluno está no nível {user_level}. "
                "SEMPRE responda em português brasileiro exceto ao demonstrar exemplos em inglês. "
                "Você NUNCA deve responder como se você fosse o aluno que está aprendendo inglês. "
                "Você NUNCA deve dizer frases como 'não preciso de ajuda com meu inglês' ou similares. "
                "Você é o PROFESSOR aqui para ensinar, e deve assumir que qualquer mensagem do usuário "
                "é de um ALUNO que precisa aprender inglês. Se a mensagem inicial parecer oferecer ajuda "
                "a você, considere que é apenas uma pergunta sobre um tema de inglês e responda como TUTOR."
            )

            # Inicializar um novo chat
            chat = self.model.start_chat(history=[])

            # Enviar primeiramente as instruções fortes
            chat.send_message(strong_instructions)

            # Extrair a mensagem do sistema se existir
            system_content = ""
            for msg in messages:
                if msg["role"] == "system":
                    system_content = msg["content"]
                    break

            # Enviar o contexto do sistema se existir
            if system_content:
                chat.send_message(f"Contexto adicional: {system_content}")

            # Processar mensagens do usuário e assistente
            user_messages = [msg for msg in messages if msg["role"] != "system"]

            # Se houver mensagens anteriores, processar as mensagens exceto a última
            if len(user_messages) > 1:
                for msg in user_messages[:-1]:
                    role = msg["role"]
                    content = msg["content"]

                    if role == "user":
                        chat.send_message(f"[ALUNO]: {content}")
                    else:
                        # Apenas adicionar ao histórico, não gerar resposta
                        chat.history.append({"role": "model", "parts": [content]})

            # Processar a última mensagem do usuário se existir
            if user_messages and user_messages[-1]["role"] == "user":
                last_message = user_messages[-1]["content"]
                response = chat.send_message(
                    f"[ALUNO]: {last_message}\n\nResponda como TUTOR DE INGLÊS em português, "
                    f"lembrando que você é o professor ajudando o aluno. NUNCA responda como se você fosse quem "
                    f"precisa aprender inglês."
                )
                return response.text

            # Se não houver mensagem do usuário, gerar uma mensagem de boas-vindas
            default_welcome = (
                "Olá! Sou seu tutor de inglês. Como posso ajudar você com seu aprendizado hoje? "
                "Podemos praticar gramática, vocabulário, pronúncia ou conversar sobre algum tema específico."
            )

            return default_welcome

        except Exception as e:
            print(f"Erro ao gerar resposta com Gemini: {e}")
            return "Desculpe, não consegui gerar uma resposta. Por favor, tente novamente mais tarde."

    # Os outros métodos da interface AIService são implementados como métodos vazios
    # já que vamos usar o GroqService para essas funcionalidades

    async def generate_lesson_content(
        self, topic: str, difficulty: str, category: str
    ) -> Dict[str, Any]:
        """Não implementado - será usado o GroqService"""
        raise NotImplementedError("Este método deve ser chamado através do GroqService")

    async def generate_exercises(
        self, lesson_content: str, num_exercises: int = 5, difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """Não implementado - será usado o GroqService"""
        raise NotImplementedError("Este método deve ser chamado através do GroqService")

    async def evaluate_response(
        self, expected_pattern: str, user_response: str, user_level: str
    ) -> Dict[str, Any]:
        """Não implementado - será usado o GroqService"""
        raise NotImplementedError("Este método deve ser chamado através do GroqService")

    async def evaluate_pronunciation(
        self, expected_text: str, audio_transcription: str
    ) -> Dict[str, Any]:
        """Não implementado - será usado o GroqService"""
        raise NotImplementedError("Este método deve ser chamado através do GroqService")

    async def generate_vocabulary_list(
        self, text: str, user_level: str, max_items: int = 10
    ) -> List[Dict[str, str]]:
        """Não implementado - será usado o GroqService"""
        raise NotImplementedError("Este método deve ser chamado através do GroqService")

    async def translate_text(self, text: str, target_language: str = "pt-br") -> str:
        """Não implementado - será usado o GroqService"""
        raise NotImplementedError("Este método deve ser chamado através do GroqService")
