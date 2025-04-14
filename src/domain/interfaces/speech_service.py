from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class SpeechService(ABC):
    """Interface para serviços de processamento de fala seguindo o princípio de inversão de dependência"""

    @abstractmethod
    async def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcreve um arquivo de áudio para texto"""
        pass

    @abstractmethod
    async def analyze_pronunciation(
        self, audio_file_path: str, expected_text: str
    ) -> Dict[str, Any]:
        """Analisa a pronúncia em um arquivo de áudio comparando com um texto esperado"""
        pass

    @abstractmethod
    async def detect_language(self, audio_file_path: str) -> str:
        """Detecta o idioma falado em um arquivo de áudio"""
        pass

    @abstractmethod
    async def text_to_speech(
        self, text: str, voice: str = "default", output_path: Optional[str] = None
    ) -> str:
        """Converte texto em fala e retorna o caminho para o arquivo de áudio gerado"""
        pass

    @abstractmethod
    async def process_user_voice_recording(
        self, discord_attachment_url: str, user_id: str
    ) -> Dict[str, Any]:
        """Processa uma gravação de voz enviada por um usuário do Discord"""
        pass
