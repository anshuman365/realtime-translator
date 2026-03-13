"""
Text-to-Speech service using Piper TTS.
"""
import asyncio
import subprocess
import base64
import io
import os
from typing import Optional
from loguru import logger
from app.config import get_tts_voice_path, settings


class PiperTTSService:
    """Piper-based Text-to-Speech service."""
    
    def __init__(self):
        self.voice_cache = {}  # Cache voice paths
        self.piper_binary = self._find_piper_binary()
    
    def _find_piper_binary(self) -> str:
        """Find Piper binary in system."""
        # Try common locations
        paths_to_try = [
            "piper",  # In PATH
            "/usr/local/bin/piper",
            "/usr/bin/piper",
            "./piper",
            os.path.join(os.path.dirname(__file__), "../../bin/piper")
        ]
        
        for path in paths_to_try:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Found Piper binary at: {path}")
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        logger.warning("Piper binary not found in common locations")
        return "piper"  # Hope it's in PATH
    
    async def synthesize(
        self,
        text: str,
        lang: str,
        gender: str = "female"
    ) -> Optional[bytes]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            lang: Language code
            gender: Voice gender (female/male)
        
        Returns:
            Audio data as bytes (WAV format) or None if error
        """
        if not text or not text.strip():
            return None
        
        voice_path = get_tts_voice_path(lang, gender)
        
        # Check if voice exists
        if not os.path.exists(voice_path):
            logger.error(f"Voice file not found: {voice_path}")
            # Try to fallback to English
            if lang != "en":
                logger.warning("Falling back to English voice")
                voice_path = get_tts_voice_path("en", gender)
                if not os.path.exists(voice_path):
                    logger.error("English fallback voice also not found")
                    return None
        
        def _synthesize():
            try:
                # Run Piper command
                # piper --model <voice.onnx> --output_file <output.wav>
                # Or use stdin/stdout
                process = subprocess.Popen(
                    [
                        self.piper_binary,
                        "--model", voice_path,
                        "--output-raw"  # Output raw PCM
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Send text to stdin
                stdout, stderr = process.communicate(input=text.encode("utf-8"), timeout=10)
                
                if process.returncode != 0:
                    logger.error(f"Piper error: {stderr.decode()}")
                    return None
                
                # Convert raw PCM to WAV
                # Piper outputs 16kHz, 16-bit mono PCM
                audio_data = self._pcm_to_wav(stdout, sample_rate=22050)
                return audio_data
                
            except subprocess.TimeoutExpired:
                logger.error("Piper synthesis timeout")
                process.kill()
                return None
            except Exception as e:
                logger.error(f"Piper synthesis error: {e}")
                return None
        
        try:
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(None, _synthesize)
            
            if audio_bytes:
                logger.debug(f"TTS ({lang}, {gender}): Generated {len(audio_bytes)} bytes for '{text[:50]}...'")
            
            return audio_bytes
        except Exception as e:
            logger.error(f"TTS async error: {e}")
            return None
    
    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int = 22050, channels: int = 1, bit_depth: int = 16) -> bytes:
        """
        Convert raw PCM data to WAV format.
        
        Args:
            pcm_data: Raw PCM audio data
            sample_rate: Sample rate in Hz
            channels: Number of channels
            bit_depth: Bits per sample
        
        Returns:
            WAV file data as bytes
        """
        import wave
        
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(bit_depth // 8)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
        
        return wav_buffer.getvalue()
    
    async def synthesize_to_base64(
        self,
        text: str,
        lang: str,
        gender: str = "female"
    ) -> Optional[str]:
        """
        Synthesize speech and return as base64 string.
        
        Args:
            text: Text to synthesize
            lang: Language code
            gender: Voice gender
        
        Returns:
            Base64 encoded audio or None
        """
        audio_bytes = await self.synthesize(text, lang, gender)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode("utf-8")
        return None
    
    async def save_audio(
        self,
        text: str,
        output_path: str,
        lang: str,
        gender: str = "female"
    ) -> bool:
        """
        Synthesize and save audio to file.
        
        Args:
            text: Text to synthesize
            output_path: Path to save WAV file
            lang: Language code
            gender: Voice gender
        
        Returns:
            True if successful, False otherwise
        """
        audio_bytes = await self.synthesize(text, lang, gender)
        if audio_bytes:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
                logger.info(f"Saved audio to {output_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to save audio: {e}")
                return False
        return False


# Global TTS service instance
tts_service = PiperTTSService()
