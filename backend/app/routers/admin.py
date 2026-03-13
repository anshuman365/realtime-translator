"""
Admin API routes for control panel.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import List

from app.utils.database import get_db
from app.utils.auth import get_current_user
from app.models.database import Session, TranslationLog, PerformanceMetric, SystemSetting
from app.models.schemas import (
    SessionInfo, LogEntry, MetricsSummary, SettingUpdate, LogQuery
)
from app.services.websocket_handler import session_manager

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/sessions", response_model=List[SessionInfo])
async def get_sessions(
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all sessions (active and historical)."""
    result = await db.execute(
        select(Session).order_by(Session.start_time.desc()).limit(100)
    )
    sessions = result.scalars().all()
    return [SessionInfo(**s.to_dict()) for s in sessions]


@router.get("/sessions/active", response_model=List[SessionInfo])
async def get_active_sessions(
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get currently active sessions."""
    result = await db.execute(
        select(Session).where(Session.status == "active")
    )
    sessions = result.scalars().all()
    return [SessionInfo(**s.to_dict()) for s in sessions]


@router.get("/logs", response_model=List[LogEntry])
async def get_logs(
    session_id: str = None,
    source_lang: str = None,
    target_lang: str = None,
    status: str = None,
    limit: int = 100,
    offset: int = 0,
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Query translation logs with filters."""
    query = select(TranslationLog).order_by(TranslationLog.timestamp.desc())
    
    # Apply filters
    conditions = []
    if session_id:
        conditions.append(TranslationLog.session_id == session_id)
    if source_lang:
        conditions.append(TranslationLog.source_lang == source_lang)
    if target_lang:
        conditions.append(TranslationLog.target_lang == target_lang)
    if status:
        conditions.append(TranslationLog.status == status)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    return [LogEntry(**log.to_dict()) for log in logs]


@router.get("/metrics", response_model=MetricsSummary)
async def get_metrics(
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system performance metrics."""
    # Active sessions count
    active_sessions = session_manager.get_active_sessions_count()
    
    # Today's sessions count
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(Session.id))
        .where(Session.start_time >= today_start)
    )
    total_sessions_today = result.scalar() or 0
    
    # Today's translations count
    result = await db.execute(
        select(func.count(TranslationLog.id))
        .where(TranslationLog.timestamp >= today_start)
    )
    total_translations_today = result.scalar() or 0
    
    # Average latencies (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    async def get_avg_latency(metric_type: str) -> float:
        result = await db.execute(
            select(func.avg(PerformanceMetric.value))
            .where(
                and_(
                    PerformanceMetric.metric_type == metric_type,
                    PerformanceMetric.timestamp >= yesterday
                )
            )
        )
        return result.scalar() or 0.0
    
    avg_stt = await get_avg_latency("stt_latency")
    avg_mt = await get_avg_latency("mt_latency")
    avg_tts = await get_avg_latency("tts_latency")
    avg_total = await get_avg_latency("total_latency")
    
    # Error rate (last 24 hours)
    result = await db.execute(
        select(func.count(TranslationLog.id))
        .where(
            and_(
                TranslationLog.timestamp >= yesterday,
                TranslationLog.status == "error"
            )
        )
    )
    errors = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(TranslationLog.id))
        .where(TranslationLog.timestamp >= yesterday)
    )
    total = result.scalar() or 1  # Avoid division by zero
    
    error_rate = (errors / total) * 100 if total > 0 else 0.0
    
    # Top language pairs (last 24 hours)
    result = await db.execute(
        select(
            TranslationLog.source_lang,
            TranslationLog.target_lang,
            func.count(TranslationLog.id).label("count")
        )
        .where(TranslationLog.timestamp >= yesterday)
        .group_by(TranslationLog.source_lang, TranslationLog.target_lang)
        .order_by(func.count(TranslationLog.id).desc())
        .limit(5)
    )
    top_pairs = [
        {
            "source": row[0],
            "target": row[1],
            "count": row[2]
        }
        for row in result.all()
    ]
    
    return MetricsSummary(
        active_sessions=active_sessions,
        total_sessions_today=total_sessions_today,
        total_translations_today=total_translations_today,
        average_stt_latency_ms=avg_stt,
        average_mt_latency_ms=avg_mt,
        average_tts_latency_ms=avg_tts,
        average_total_latency_ms=avg_total,
        error_rate=error_rate,
        top_language_pairs=top_pairs
    )


@router.post("/settings")
async def update_setting(
    setting: SettingUpdate,
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a system setting."""
    # Check if setting exists
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == setting.key)
    )
    db_setting = result.scalar_one_or_none()
    
    if db_setting:
        # Update existing
        db_setting.value = setting.value
        if setting.description:
            db_setting.description = setting.description
    else:
        # Create new
        db_setting = SystemSetting(
            key=setting.key,
            value=setting.value,
            description=setting.description
        )
        db.add(db_setting)
    
    await db.commit()
    await db.refresh(db_setting)
    
    return {"message": "Setting updated", "setting": db_setting.to_dict()}


@router.get("/settings")
async def get_settings(
    username: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all system settings."""
    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    return [s.to_dict() for s in settings]


@router.get("/health")
async def health_check(username: str = Depends(get_current_user)):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": session_manager.get_active_sessions_count(),
        "timestamp": datetime.utcnow().isoformat()
    }
