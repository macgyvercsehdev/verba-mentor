import json
import os
from typing import Any, Dict, List, Optional

import requests

from src.domain.interfaces.ai_service import AIService


class GroqService(AIService):
    """Implementação do serviço de AI usando a API da Groq"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv(
            "OPENAI_API_KEY"
        )  # Reusa a variável de ambiente
        if not self.api_key:
            raise ValueError("API Key da Groq não fornecida")

        self.api_base = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Modelo padrão da Groq
        self.model = "llama2-70b-4096"  # ou "mixtral-8x7b-32768" para contextos maiores

    async def generate_response(
        self, messages: List[Dict[str, str]], user_level: str, max_tokens: int = 500
    ) -> str:
        """Gera uma resposta com base no histórico de mensagens e nível do usuário"""
        try:
            # Adicionar instruções de sistema claras para evitar confusão de papéis
            system_message = {
                "role": "system",
                "content": (
                    "Você é um tutor de inglês chamado VerbaMentor que ajuda estudantes brasileiros a aprender inglês. "
                    f"O estudante tem nível {user_level}. "
                    "NUNCA responda como se você fosse o aluno ou como se você precisasse de ajuda com inglês. "
                    "Seu papel é ensinar inglês ao aluno, não o contrário. "
                    "Se o aluno perguntar se você precisa de ajuda com inglês, explique educadamente que você é o tutor "
                    "e está aqui para ajudá-lo a aprender inglês."
                ),
            }

            # Verificar se já existe uma mensagem de sistema e substituí-la ou adicionar nova
            has_system_message = False
            for i, msg in enumerate(messages):
                if msg["role"] == "system":
                    messages[i] = system_message
                    has_system_message = True
                    break

            if not has_system_message:
                messages.insert(0, system_message)

            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
            }

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Erro ao gerar resposta: {e}")
            return "Desculpe, não consegui gerar uma resposta. Por favor, tente novamente mais tarde."

    async def generate_lesson_content(
        self, topic: str, difficulty: str, category: str
    ) -> Dict[str, Any]:
        """Gera conteúdo para uma lição com base no tópico, dificuldade e categoria"""
        prompt = (
            f"Crie uma lição de inglês completa sobre '{topic}'. "
            f"Nível: {difficulty}. Categoria: {category}. "
            "A lição deve incluir: introdução, conteúdo principal, exemplos, "
            "prática e conclusão. Forneça também um título adequado e "
            "uma breve descrição. Responda em formato JSON com as seguintes chaves: "
            "title, description, introduction, main_content, examples, practice, conclusion."
        )

        try:
            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Você é um especialista em criar materiais didáticos para ensino de inglês.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1500,
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
            }

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            return json.loads(content)
        except Exception as e:
            print(f"Erro ao gerar conteúdo da lição: {e}")
            return {
                "title": f"Lição sobre {topic}",
                "description": "Conteúdo não disponível no momento.",
                "introduction": "Não foi possível gerar a introdução.",
                "main_content": "Não foi possível gerar o conteúdo principal.",
                "examples": "Não foi possível gerar exemplos.",
                "practice": "Não foi possível gerar exercícios de prática.",
                "conclusion": "Não foi possível gerar a conclusão.",
            }

    async def generate_exercises(
        self, lesson_content: str, num_exercises: int = 5, difficulty: str = "medium"
    ) -> List[Dict[str, Any]]:
        """Gera exercícios baseados no conteúdo da lição"""
        prompt = (
            f"Com base no seguinte conteúdo de lição de inglês:\n\n{lesson_content}\n\n"
            f"Crie {num_exercises} exercícios de nível {difficulty}. "
            "Inclua uma mistura de perguntas de múltipla escolha e perguntas abertas. "
            "Para cada exercício, forneça: pergunta, opções (quando aplicável), "
            "resposta correta e explicação. Responda em formato JSON como um array de exercícios."
        )

        try:
            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Você é um especialista em criar exercícios para ensino de inglês.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1500,
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
            }

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            exercises_data = json.loads(content)

            # Garantir que o retorno seja uma lista
            if isinstance(exercises_data, dict) and "exercises" in exercises_data:
                return exercises_data["exercises"]
            elif isinstance(exercises_data, list):
                return exercises_data
            else:
                return []
        except Exception as e:
            print(f"Erro ao gerar exercícios: {e}")
            return []

    async def evaluate_response(
        self, expected_pattern: str, user_response: str, user_level: str
    ) -> Dict[str, Any]:
        """Avalia a resposta do usuário em relação a um padrão esperado"""
        prompt = (
            f"Avalie a resposta de um estudante de inglês de nível {user_level}.\n\n"
            f"Contexto ou pergunta: {expected_pattern}\n\n"
            f"Resposta do estudante: {user_response}\n\n"
            "Forneça uma avaliação detalhada incluindo: correções gramaticais, "
            "avaliação de vocabulário, sugestões de melhoria, e uma pontuação de 0 a 1 "
            "para gramática e adequação da resposta. Responda em formato JSON com as seguintes chaves: "
            "feedback, grammar_corrections, vocabulary_suggestions, grammar_score, adequacy_score."
        )

        try:
            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Você é um professor de inglês avaliando respostas de alunos.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1000,
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            }

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            print(f"Erro ao avaliar resposta: {e}")
            return {
                "feedback": "Não foi possível avaliar a resposta.",
                "grammar_corrections": [],
                "vocabulary_suggestions": [],
                "grammar_score": 0.5,
                "adequacy_score": 0.5,
            }

    async def evaluate_pronunciation(
        self, expected_text: str, audio_transcription: str
    ) -> Dict[str, Any]:
        """Avalia a pronúncia do usuário comparando o texto esperado com a transcrição do áudio"""
        prompt = (
            f"Avalie a pronúncia de um estudante de inglês.\n\n"
            f"Texto esperado: {expected_text}\n\n"
            f"Texto transcrito do áudio: {audio_transcription}\n\n"
            "Compare os dois textos e identifique erros de pronúncia, palavras omitidas ou adicionadas. "
            "Forneça feedback detalhado, sugestões de melhoria, e uma pontuação de 0 a 1. "
            "Responda em formato JSON com as seguintes chaves: pronunciation_feedback, "
            "identified_errors, improvement_suggestions, pronunciation_score."
        )

        try:
            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Você é um especialista em pronúncia de inglês.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 800,
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            }

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            print(f"Erro ao avaliar pronúncia: {e}")
            return {
                "pronunciation_feedback": "Não foi possível avaliar a pronúncia.",
                "identified_errors": [],
                "improvement_suggestions": [],
                "pronunciation_score": 0.5,
            }

    async def generate_vocabulary_list(
        self, text: str, user_level: str, max_items: int = 10
    ) -> List[Dict[str, str]]:
        """Gera uma lista de vocabulário a partir de um texto, adequada ao nível do usuário"""
        prompt = (
            f"A partir do seguinte texto em inglês:\n\n{text}\n\n"
            f"Extraia até {max_items} palavras ou expressões importantes para um estudante de nível {user_level}. "
            "Para cada item, forneça: a palavra/expressão, definição em inglês, definição em português, "
            "e um exemplo de uso em uma frase. Responda em formato JSON como um array de itens."
        )

        try:
            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Você é um especialista em ensino de vocabulário de inglês.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1000,
                "temperature": 0.5,
                "response_format": {"type": "json_object"},
            }

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            vocabulary_data = json.loads(content)

            # Garantir que o retorno seja uma lista
            if isinstance(vocabulary_data, dict) and "vocabulary" in vocabulary_data:
                return vocabulary_data["vocabulary"]
            elif isinstance(vocabulary_data, list):
                return vocabulary_data
            else:
                return []
        except Exception as e:
            print(f"Erro ao gerar lista de vocabulário: {e}")
            return []

    async def translate_text(self, text: str, target_language: str = "pt-br") -> str:
        """Traduz um texto para o idioma de destino"""
        prompt = f"Traduza o seguinte texto para {target_language}:\n\n{text}"

        try:
            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Você é um tradutor profissional."},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1000,
                "temperature": 0.3,
            }

            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()

            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Erro ao traduzir texto: {e}")
            return f"Erro na tradução: {text}"
