"""
WebSocket handler for real-time translation.
"""
import asyncio
import json
import uuid
import time
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from typing import Optional

from app.services.stt_service import stt_service
from app.services.translation_service import translation_service
from app.services.tts_service import tts_service
from app.models.database import Session, TranslationLog, PerformanceMetric
from app.models.schemas import TranslationConfig, TranslationResponse, ErrorResponse
from app.utils.database import get_db_session


class TranslationSession:
    """Manages a single translation session."""
    
    def __init__(
        self,
        websocket: WebSocket,
        session_id: str,
        client_ip: str,
        user_agent: Optional[str] = None
    ):
        self.websocket = websocket
        self.session_id = session_id
        self.client_ip = client_ip
        self.user_agent = user_agent
        self.config: Optional[TranslationConfig] = None
        self.is_active = True
        self.start_time = datetime.utcnow()
        
        # Buffering for better translation quality
        self.text_buffer = []
        self.last_final_time = time.time()
    
    async def send_json(self, data: dict):
        """Send JSON message to client."""
        try:
            await self.websocket.send_json(data)
        except Exception as e:
            logger.error(f"Failed to send message to {self.session_id}: {e}")
            self.is_active = False
    
    async def send_error(self, message: str):
        """Send error message to client."""
        error = ErrorResponse(message=message)
        await self.send_json(error.dict())
    
    async def process_config(self, config_data: dict):
        """Process configuration message from client."""
        try:
            self.config = TranslationConfig(**config_data)
            logger.info(f"Session {self.session_id} configured: {self.config.source_lang} -> {self.config.target_lang}")
            
            # Create recognizer for this session
            stt_service.create_recognizer(
                self.session_id,
                self.config.source_lang
            )
            
            # Send confirmation
            await self.send_json({
                "type": "config_ack",
                "message": "Configuration accepted",
                "session_id": self.session_id
            })
            
        except Exception as e:
            logger.error(f"Configuration error for {self.session_id}: {e}")
            await self.send_error(f"Configuration error: {str(e)}")
    
    async def process_audio(self, audio_data: bytes):
        """Process audio chunk through the pipeline."""
        if not self.config:
            await self.send_error("Session not configured")
            return
        
        start_time = time.time()
        timings = {}
        
        try:
            # 1. Speech-to-Text
            stt_start = time.time()
            source_text, is_final = await stt_service.process_audio_chunk(
                self.session_id,
                audio_data,
                self.config.source_lang
            )
            timings['stt_ms'] = (time.time() - stt_start) * 1000
            
            # Skip if no text or empty
            if not source_text or not source_text.strip():
                return
            
            # Buffer partial results for better translation
            if not is_final:
                self.text_buffer.append(source_text)
                # Only translate if buffer is getting long or timeout
                if len(" ".join(self.text_buffer)) < 50 and (time.time() - self.last_final_time) < 2.0:
                    return
                source_text = " ".join(self.text_buffer)
            else:
                if self.text_buffer:
                    source_text = " ".join(self.text_buffer + [source_text])
                    self.text_buffer = []
                self.last_final_time = time.time()
            
            # 2. Machine Translation
            mt_start = time.time()
            translated_text = await translation_service.translate(
                source_text,
                self.config.source_lang,
                self.config.target_lang
            )
            timings['mt_ms'] = (time.time() - mt_start) * 1000
            
            if not translated_text:
                logger.warning(f"Translation failed for: {source_text}")
                return
            
            # 3. Text-to-Speech (if enabled)
            audio_base64 = None
            if self.config.enable_audio and is_final:
                tts_start = time.time()
                audio_base64 = await tts_service.synthesize_to_base64(
                    translated_text,
                    self.config.target_lang,
                    self.config.voice_gender
                )
                timings['tts_ms'] = (time.time() - tts_start) * 1000
            
            # Calculate total time
            timings['total_ms'] = (time.time() - start_time) * 1000
            
            # 4. Send response to client
            response = TranslationResponse(
                source_text=source_text,
                translated_text=translated_text,
                audio=audio_base64,
                final=is_final,
                stt_time_ms=timings.get('stt_ms'),
                mt_time_ms=timings.get('mt_ms'),
                tts_time_ms=timings.get('tts_ms')
            )
            
            await self.send_json(response.dict())
            
            # 5. Log to database (async, don't block)
            asyncio.create_task(self._log_translation(
                source_text,
                translated_text,
                is_final,
                timings,
                "success"
            ))
            
            logger.info(
                f"Translation ({self.session_id}): "
                f"STT:{timings.get('stt_ms', 0):.0f}ms, "
                f"MT:{timings.get('mt_ms', 0):.0f}ms, "
                f"TTS:{timings.get('tts_ms', 0):.0f}ms, "
                f"Total:{timings.get('total_ms', 0):.0f}ms"
            )
            
        except Exception as e:
            logger.error(f"Translation pipeline error for {self.session_id}: {e}")
            await self.send_error(f"Translation error: {str(e)}")
            
            # Log error
            asyncio.create_task(self._log_translation(
                source_text if 'source_text' in locals() else "",
                "",
                is_final if 'is_final' in locals() else False,
                timings,
                "error",
                str(e)
            ))
    
    async def _log_translation(
        self,
        source_text: str,
        translated_text: str,
        is_final: bool,
        timings: dict,
        status: str,
        error_message: Optional[str] = None
    ):
        """Log translation to database."""
        try:
            async with get_db_session() as db:
                log_entry = TranslationLog(
                    session_id=self.session_id,
                    source_lang=self.config.source_lang,
                    target_lang=self.config.target_lang,
                    source_text=source_text,
                    translated_text=translated_text,
                    stt_time_ms=timings.get('stt_ms'),
                    mt_time_ms=timings.get('mt_ms'),
                    tts_time_ms=timings.get('tts_ms'),
                    total_time_ms=timings.get('total_ms'),
                    is_final=is_final,
                    status=status,
                    error_message=error_message
                )
                db.add(log_entry)
                
                # Also log performance metrics
                for metric_type, value in timings.items():
                    if value is not None:
                        metric = PerformanceMetric(
                            metric_type=metric_type.replace('_ms', '_latency'),
                            value=value,
                            session_id=self.session_id,
                            language_pair=f"{self.config.source_lang}-{self.config.target_lang}"
                        )
                        db.add(metric)
                
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log translation: {e}")
    
    async def cleanup(self):
        """Clean up session resources."""
        self.is_active = False
        stt_service.remove_recognizer(self.session_id)
        
        # Update session end time in database
        try:
            async with get_db_session() as db:
                from sqlalchemy import select, update
                
                stmt = (
                    update(Session)
                    .where(Session.id == self.session_id)
                    .values(
                        end_time=datetime.utcnow(),
                        status="completed"
                    )
                )
                await db.execute(stmt)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update session end time: {e}")


class TranslationSessionManager:
    """Manages multiple translation sessions."""
    
    def __init__(self):
        self.sessions: dict[str, TranslationSession] = {}
    
    async def create_session(
        self,
        websocket: WebSocket,
        client_ip: str,
        user_agent: Optional[str] = None
    ) -> TranslationSession:
        """Create a new translation session."""
        session_id = str(uuid.uuid4())
        session = TranslationSession(websocket, session_id, client_ip, user_agent)
        self.sessions[session_id] = session
        
        # Create session record in database
        try:
            async with get_db_session() as db:
                db_session = Session(
                    id=session_id,
                    client_ip=client_ip,
                    source_lang="",  # Will be set when configured
                    target_lang="",
                    user_agent=user_agent,
                    status="active"
                )
                db.add(db_session)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to create session record: {e}")
        
        logger.info(f"Created session {session_id} for {client_ip}")
        return session
    
    async def remove_session(self, session_id: str):
        """Remove a session."""
        session = self.sessions.pop(session_id, None)
        if session:
            await session.cleanup()
            logger.info(f"Removed session {session_id}")
    
    def get_session(self, session_id: str) -> Optional[TranslationSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        return len(self.sessions)


# Global session manager
session_manager = TranslationSessionManager()


async def handle_websocket(websocket: WebSocket, client_ip: str, user_agent: Optional[str] = None):
    """
    Handle WebSocket connection for translation.
    
    Protocol:
    - Client sends config message: {"type": "config", "source_lang": "en", "target_lang": "hi", ...}
    - Client sends audio as binary data
    - Server sends translation responses as JSON
    """
    await websocket.accept()
    session = await session_manager.create_session(websocket, client_ip, user_agent)
    
    try:
        while session.is_active:
            # Receive message (either text config or binary audio)
            message = await websocket.receive()
            
            if "text" in message:
                # Configuration message
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "config":
                        await session.process_config(data)
                        
                        # Update session in database with languages
                        if session.config:
                            async with get_db_session() as db:
                                from sqlalchemy import update
                                stmt = (
                                    update(Session)
                                    .where(Session.id == session.session_id)
                                    .values(
                                        source_lang=session.config.source_lang,
                                        target_lang=session.config.target_lang
                                    )
                                )
                                await db.execute(stmt)
                                await db.commit()
                except json.JSONDecodeError:
                    await session.send_error("Invalid JSON")
            
            elif "bytes" in message:
                # Audio data
                audio_data = message["bytes"]
                await session.process_audio(audio_data)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session.session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {session.session_id}: {e}")
    finally:
        await session_manager.remove_session(session.session_id)
