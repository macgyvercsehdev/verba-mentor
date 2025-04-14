import asyncio
import os
import tempfile
import uuid
from typing import Any, Dict, Optional

import aiohttp
import speech_recognition as sr
from pydub import AudioSegment

from src.domain.interfaces.speech_service import SpeechService


class SpeechServiceImpl(SpeechService):
    """Implementação do serviço de processamento de fala"""

    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("API Key da OpenAI não fornecida")

        self.recognizer = sr.Recognizer()
        self.temp_dir = tempfile.gettempdir()

    async def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcreve um arquivo de áudio para texto"""
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(audio_file_path):
                return {"error": "Arquivo de áudio não encontrado", "text": ""}

            # Converte o áudio para o formato adequado (WAV) se necessário
            audio_file_wav = self._convert_to_wav(audio_file_path)

            # Realiza a transcrição usando o SpeechRecognition com a API da OpenAI
            with sr.AudioFile(audio_file_wav) as source:
                audio_data = self.recognizer.record(source)

                # Tenta usar a API Whisper da OpenAI para transcrição de alta precisão
                try:
                    text = self.recognizer.recognize_whisper(
                        audio_data, api_key=self.openai_api_key
                    )
                    return {"text": text, "success": True}
                except sr.RequestError:
                    # Fallback para reconhecimento offline da Google se a API da OpenAI falhar
                    try:
                        text = self.recognizer.recognize_google(audio_data)
                        return {
                            "text": text,
                            "success": True,
                            "note": "Usando reconhecimento de fallback",
                        }
                    except:
                        return {
                            "error": "Falha na transcrição",
                            "text": "",
                            "success": False,
                        }

        except Exception as e:
            print(f"Erro ao transcrever áudio: {e}")
            return {"error": str(e), "text": "", "success": False}

    async def analyze_pronunciation(
        self, audio_file_path: str, expected_text: str
    ) -> Dict[str, Any]:
        """Analisa a pronúncia em um arquivo de áudio comparando com um texto esperado"""
        transcription_result = await self.transcribe_audio(audio_file_path)

        if not transcription_result.get("success", False):
            return {
                "error": transcription_result.get("error", "Falha na transcrição"),
                "pronunciation_score": 0.0,
                "feedback": "Não foi possível analisar a pronúncia devido a um erro na transcrição.",
            }

        transcribed_text = transcription_result.get("text", "")

        # Implementação simples de avaliação de pronúncia baseada em comparação de texto
        # Em um sistema real, usaríamos um serviço mais sofisticado para análise fonética

        # Normaliza os textos para comparação
        expected_lower = expected_text.lower().strip()
        transcribed_lower = transcribed_text.lower().strip()

        # Calcula o score baseado na similaridade de palavras
        expected_words = expected_lower.split()
        transcribed_words = transcribed_lower.split()

        # Conta palavras corretas
        correct_words = 0
        for word in transcribed_words:
            if word in expected_words:
                correct_words += 1

        # Calcula o score
        max_words = max(len(expected_words), len(transcribed_words))
        score = correct_words / max_words if max_words > 0 else 0

        # Gera feedback
        if score > 0.9:
            feedback = "Excelente pronúncia! Você disse o texto quase perfeitamente."
        elif score > 0.7:
            feedback = "Boa pronúncia. Algumas pequenas diferenças do texto esperado."
        elif score > 0.5:
            feedback = (
                "Pronúncia razoável. Há algumas palavras que precisam de prática."
            )
        else:
            feedback = "Sua pronúncia precisa de mais prática. Tente novamente depois de revisar o texto."

        return {
            "pronunciation_score": score,
            "transcribed_text": transcribed_text,
            "expected_text": expected_text,
            "feedback": feedback,
            "success": True,
        }

    async def detect_language(self, audio_file_path: str) -> str:
        """Detecta o idioma falado em um arquivo de áudio"""
        # Esta é uma implementação simplificada
        # Em um sistema real, usaríamos um serviço especializado em detecção de idioma

        try:
            transcription_result = await self.transcribe_audio(audio_file_path)

            if not transcription_result.get("success", False):
                return "unknown"

            # Aqui usaríamos um serviço específico para detecção de idioma
            # Por simplicidade, assumimos inglês se a transcrição for bem-sucedida
            return "en"
        except Exception as e:
            print(f"Erro ao detectar idioma: {e}")
            return "unknown"

    async def text_to_speech(
        self, text: str, voice: str = "default", output_path: Optional[str] = None
    ) -> str:
        """Converte texto em fala e retorna o caminho para o arquivo de áudio gerado"""
        # Por simplicidade, esta função é um placeholder
        # Em um sistema real, usaríamos a API da OpenAI, Google ou AWS Polly

        if not output_path:
            output_path = os.path.join(self.temp_dir, f"tts_{uuid.uuid4()}.mp3")

        # Aqui usaríamos uma API real de text-to-speech
        # Por simplificação, apenas retornamos o caminho que seria criado

        print(f"[TTS] Texto '{text}' seria convertido para áudio em '{output_path}'")

        # Simula um atraso de processamento
        await asyncio.sleep(0.5)

        return output_path

    async def process_user_voice_recording(
        self, discord_attachment_url: str, user_id: str
    ) -> Dict[str, Any]:
        """Processa uma gravação de voz enviada por um usuário do Discord"""
        try:
            # Baixar o arquivo de áudio do Discord
            local_file_path = await self._download_attachment(
                discord_attachment_url, user_id
            )

            if not local_file_path:
                return {
                    "error": "Não foi possível baixar o arquivo de áudio",
                    "success": False,
                }

            # Transcrever o áudio
            transcription = await self.transcribe_audio(local_file_path)

            # Limpar o arquivo temporário
            try:
                os.remove(local_file_path)
            except:
                pass

            return transcription

        except Exception as e:
            print(f"Erro ao processar gravação de voz: {e}")
            return {"error": str(e), "success": False}

    async def _download_attachment(self, url: str, user_id: str) -> Optional[str]:
        """Faz o download de um anexo de áudio do Discord"""
        try:
            # Criar diretório temporário para o usuário se não existir
            user_temp_dir = os.path.join(self.temp_dir, f"user_{user_id}")
            os.makedirs(user_temp_dir, exist_ok=True)

            # Caminho para salvar o arquivo
            file_ext = url.split(".")[-1] if "." in url else "ogg"
            local_file_path = os.path.join(
                user_temp_dir, f"audio_{uuid.uuid4()}.{file_ext}"
            )

            # Fazer o download usando aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(local_file_path, "wb") as f:
                            f.write(await response.read())
                        return local_file_path
                    else:
                        print(f"Erro ao baixar anexo: {response.status}")
                        return None

        except Exception as e:
            print(f"Erro no download do anexo: {e}")
            return None

    def _convert_to_wav(self, audio_file_path: str) -> str:
        """Converte um arquivo de áudio para o formato WAV"""
        try:
            # Verifica a extensão do arquivo
            file_ext = os.path.splitext(audio_file_path)[1].lower()

            # Se já for WAV, retorna o caminho original
            if file_ext == ".wav":
                return audio_file_path

            # Caso contrário, converte para WAV
            output_path = os.path.splitext(audio_file_path)[0] + ".wav"

            # Usa pydub para conversão
            audio = AudioSegment.from_file(audio_file_path)
            audio.export(output_path, format="wav")

            return output_path

        except Exception as e:
            print(f"Erro ao converter áudio para WAV: {e}")
            # Se falhar, retorna o caminho original
            return audio_file_path
