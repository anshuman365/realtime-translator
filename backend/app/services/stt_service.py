"""
Speech-to-Text service using Vosk.
"""
import asyncio
import json
from typing import Optional, AsyncGenerator
from vosk import Model, KaldiRecognizer
import wave
import io
from loguru import logger
from app.config import get_vosk_model_path, settings


class VoskSTTService:
    """Vosk-based Speech-to-Text service with streaming support."""
    
    def __init__(self):
        self.models = {}  # Cache loaded models
        self.recognizers = {}  # Cache recognizers per session
    
    def _get_model(self, lang: str) -> Model:
        """Get or load Vosk model for a language."""
        if lang not in self.models:
            model_path = get_vosk_model_path(lang)
            logger.info(f"Loading Vosk model for {lang} from {model_path}")
            try:
                self.models[lang] = Model(model_path)
                logger.success(f"Vosk model loaded for {lang}")
            except Exception as e:
                logger.error(f"Failed to load Vosk model for {lang}: {e}")
                # Fallback to English if available
                if lang != "en":
                    logger.warning(f"Falling back to English model")
                    return self._get_model("en")
                raise
        return self.models[lang]
    
    def create_recognizer(self, session_id: str, lang: str, sample_rate: int = 16000) -> KaldiRecognizer:
        """Create a new recognizer for a session."""
        model = self._get_model(lang)
        recognizer = KaldiRecognizer(model, sample_rate)
        recognizer.SetWords(True)  # Get word-level timestamps
        self.recognizers[session_id] = recognizer
        logger.info(f"Created recognizer for session {session_id}, lang={lang}")
        return recognizer
    
    def get_recognizer(self, session_id: str) -> Optional[KaldiRecognizer]:
        """Get recognizer for a session."""
        return self.recognizers.get(session_id)
    
    def remove_recognizer(self, session_id: str):
        """Remove recognizer for a session."""
        if session_id in self.recognizers:
            del self.recognizers[session_id]
            logger.info(f"Removed recognizer for session {session_id}")
    
    async def process_audio_chunk(
        self, 
        session_id: str, 
        audio_data: bytes,
        lang: str = "en"
    ) -> tuple[Optional[str], bool]:
        """
        Process audio chunk and return (text, is_final).
        
        Args:
            session_id: Session identifier
            audio_data: PCM audio data (16kHz, 16-bit, mono)
            lang: Language code
        
        Returns:
            Tuple of (transcribed_text, is_final_result)
        """
        recognizer = self.get_recognizer(session_id)
        if recognizer is None:
            recognizer = self.create_recognizer(session_id, lang)
        
        # Process in thread pool to avoid blocking
        def process():
            if recognizer.AcceptWaveform(audio_data):
                # Final result
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                return text, True
            else:
                # Partial result
                result = json.loads(recognizer.PartialResult())
                text = result.get("partial", "")
                return text, False
        
        try:
            loop = asyncio.get_event_loop()
            text, is_final = await loop.run_in_executor(None, process)
            
            if text:
                logger.debug(f"STT ({session_id}): '{text}' (final={is_final})")
            
            return text, is_final
        except Exception as e:
            logger.error(f"STT error in session {session_id}: {e}")
            return None, False
    
    async def process_audio_file(self, audio_file_path: str, lang: str = "en") -> str:
        """
        Process complete audio file (for testing).
        
        Args:
            audio_file_path: Path to WAV file
            lang: Language code
        
        Returns:
            Transcribed text
        """
        model = self._get_model(lang)
        
        def transcribe():
            with wave.open(audio_file_path, "rb") as wf:
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                    logger.warning(f"Audio format not optimal: {wf.getnchannels()}ch, {wf.getsampwidth()}bytes, {wf.getframerate()}Hz")
                
                recognizer = KaldiRecognizer(model, wf.getframerate())
                recognizer.SetWords(True)
                
                results = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "")
                        if text:
                            results.append(text)
                
                # Get final result
                result = json.loads(recognizer.FinalResult())
                text = result.get("text", "")
                if text:
                    results.append(text)
                
                return " ".join(results)
        
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, transcribe)
        logger.info(f"Transcribed file: {audio_file_path} -> '{text}'")
        return text
    
    def reset_recognizer(self, session_id: str):
        """Reset recognizer for a session (clears context)."""
        recognizer = self.get_recognizer(session_id)
        if recognizer:
            recognizer.Reset()
            logger.info(f"Reset recognizer for session {session_id}")


# Global STT service instance
stt_service = VoskSTTService()
