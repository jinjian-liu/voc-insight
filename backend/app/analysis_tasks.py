from sqlalchemy import select

from app.ai_service import analyze_feedback
from app.config import get_settings
from app.database import SessionLocal
from app.models import Category, Feedback, FeedbackAnalysis


async def analyze_feedback_task(feedback_id: int, api_key: str) -> None:
    with SessionLocal() as db:
        feedback = db.get(Feedback, feedback_id)
        if feedback is None or feedback.deleted_at is not None:
            return
        categories = list(
            db.scalars(
                select(Category.name)
                .where(Category.deleted_at.is_(None))
                .order_by(Category.sort_order, Category.id)
            ).all()
        )
        try:
            result, raw_response = await analyze_feedback(api_key, feedback.content, categories)
            analysis = db.scalar(
                select(FeedbackAnalysis).where(FeedbackAnalysis.feedback_id == feedback_id)
            )
            values = result.model_dump()
            if analysis is None:
                analysis = FeedbackAnalysis(
                    feedback_id=feedback_id,
                    **values,
                    raw_response=raw_response,
                    model_name=get_settings().deepseek_model,
                )
                db.add(analysis)
            else:
                for key, value in values.items():
                    setattr(analysis, key, value)
                analysis.raw_response = raw_response
                analysis.model_name = get_settings().deepseek_model
                analysis.confirmed = False
                analysis.confirmed_by_name = None
                analysis.confirmed_at = None
            feedback.analysis_status = "success"
        except Exception:
            feedback.analysis_status = "failed"
        db.commit()
