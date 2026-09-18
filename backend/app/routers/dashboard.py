from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_runtime_session
from app.models import Feedback, FeedbackAnalysis, Issue
from app.routers.issues import to_issue_view
from app.schemas import DashboardOverview
from app.session_store import RuntimeSession


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
def dashboard_overview(
    db: Session = Depends(get_db),
    _: RuntimeSession = Depends(require_runtime_session),
) -> DashboardOverview:
    feedback_total = db.scalar(
        select(func.count(Feedback.id)).where(Feedback.deleted_at.is_(None))
    ) or 0
    feedback_pending = db.scalar(
        select(func.count(Feedback.id)).where(
            Feedback.deleted_at.is_(None), Feedback.analysis_status.in_(["pending", "failed"])
        )
    ) or 0
    issue_pending = db.scalar(
        select(func.count(Issue.id)).where(Issue.deleted_at.is_(None), Issue.status == "pending")
    ) or 0
    issue_processed = db.scalar(
        select(func.count(Issue.id)).where(Issue.deleted_at.is_(None), Issue.status == "processed")
    ) or 0
    high_pending = db.scalar(
        select(func.count(Issue.id)).where(
            Issue.deleted_at.is_(None),
            Issue.status == "pending",
            Issue.severity.in_(["high", "urgent"]),
        )
    ) or 0

    category_rows = db.execute(
        select(FeedbackAnalysis.category, func.count(FeedbackAnalysis.id))
        .join(Feedback, Feedback.id == FeedbackAnalysis.feedback_id)
        .where(Feedback.deleted_at.is_(None))
        .group_by(FeedbackAnalysis.category)
        .order_by(func.count(FeedbackAnalysis.id).desc())
    ).all()

    processed_issues = list(db.scalars(
        select(Issue).where(Issue.deleted_at.is_(None), Issue.status == "processed")
    ).all())
    resolution_hours = [
        (issue.processed_at - issue.created_at).total_seconds() / 3600
        for issue in processed_issues
        if issue.processed_at is not None
    ]

    all_issues = list(db.scalars(
        select(Issue).where(Issue.deleted_at.is_(None)).order_by(Issue.updated_at.desc())
    ).all())
    top_issues = sorted(all_issues, key=lambda item: len(item.feedback_links), reverse=True)[:5]

    return DashboardOverview(
        feedback_total=feedback_total,
        feedback_pending_analysis=feedback_pending,
        issue_pending=issue_pending,
        issue_processed=issue_processed,
        high_severity_pending=high_pending,
        average_resolution_hours=(round(sum(resolution_hours) / len(resolution_hours), 1) if resolution_hours else None),
        category_distribution=[{"name": name, "value": count} for name, count in category_rows],
        status_distribution=[
            {"name": "待处理", "value": issue_pending},
            {"name": "已处理", "value": issue_processed},
        ],
        top_issues=[to_issue_view(issue) for issue in top_issues],
    )

