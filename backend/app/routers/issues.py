from datetime import datetime, timezone
from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_runtime_session
from app.models import Activity, Feedback, Issue, IssueFeedback
from app.schemas import (
    IssueComplete,
    IssueCreate,
    IssueDetail,
    IssueLink,
    IssuePage,
    IssueUpdate,
    IssueView,
    SimilarIssue,
)
from app.session_store import RuntimeSession


router = APIRouter(prefix="/issues", tags=["issues"])


def to_issue_view(issue: Issue) -> IssueView:
    return IssueView.model_validate(issue).model_copy(update={"feedback_count": len(issue.feedback_links)})


@router.get("", response_model=IssuePage)
def list_issues(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None, max_length=100),
    issue_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: RuntimeSession = Depends(require_runtime_session),
) -> IssuePage:
    conditions = [Issue.deleted_at.is_(None)]
    if keyword:
        pattern = f"%{keyword.strip()}%"
        conditions.append(or_(Issue.title.ilike(pattern), Issue.description.ilike(pattern)))
    if issue_status:
        conditions.append(Issue.status == issue_status)
    total = db.scalar(select(func.count(Issue.id)).where(*conditions)) or 0
    issues = db.scalars(
        select(Issue)
        .where(*conditions)
        .order_by(Issue.updated_at.desc(), Issue.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return IssuePage(
        items=[to_issue_view(item) for item in issues],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=IssueView, status_code=status.HTTP_201_CREATED)
def create_issue(
    payload: IssueCreate,
    db: Session = Depends(get_db),
    runtime: RuntimeSession = Depends(require_runtime_session),
) -> IssueView:
    feedback = db.get(Feedback, payload.feedback_id)
    if feedback is None or feedback.deleted_at is not None:
        raise HTTPException(status_code=404, detail="反馈不存在")
    issue = Issue(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        severity=payload.severity,
        priority=payload.priority,
        created_by_name=runtime.operator_name,
    )
    db.add(issue)
    db.flush()
    db.add(IssueFeedback(
        issue_id=issue.id,
        feedback_id=feedback.id,
        relation_type="created_from",
        confirmed_by_name=runtime.operator_name,
    ))
    db.add(Activity(
        issue_id=issue.id,
        action_type="created",
        comment="由反馈创建问题",
        operator_name=runtime.operator_name,
    ))
    db.commit()
    db.refresh(issue)
    return to_issue_view(issue)


@router.get("/similar", response_model=list[SimilarIssue])
def similar_issues(
    title: str = Query(min_length=1, max_length=300),
    category: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    _: RuntimeSession = Depends(require_runtime_session),
) -> list[SimilarIssue]:
    candidates = db.scalars(
        select(Issue).where(Issue.deleted_at.is_(None)).order_by(Issue.updated_at.desc()).limit(50)
    ).all()
    ranked: list[tuple[float, Issue]] = []
    for issue in candidates:
        text_score = SequenceMatcher(None, title.lower(), issue.title.lower()).ratio()
        category_bonus = 0.15 if category and issue.category == category else 0
        score = min(1.0, text_score + category_bonus)
        if score >= 0.25:
            ranked.append((score, issue))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [
        SimilarIssue(**to_issue_view(issue).model_dump(), similarity_score=round(score, 3))
        for score, issue in ranked[:5]
    ]


@router.get("/{issue_id}", response_model=IssueDetail)
def get_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    _: RuntimeSession = Depends(require_runtime_session),
) -> IssueDetail:
    issue = db.get(Issue, issue_id)
    if issue is None or issue.deleted_at is not None:
        raise HTTPException(status_code=404, detail="问题不存在")
    feedbacks = [link.feedback for link in issue.feedback_links if link.feedback.deleted_at is None]
    return IssueDetail(
        **to_issue_view(issue).model_dump(),
        feedbacks=feedbacks,
        activities=sorted(issue.activities, key=lambda item: item.created_at, reverse=True),
    )


@router.put("/{issue_id}", response_model=IssueView)
def update_issue(
    issue_id: int,
    payload: IssueUpdate,
    db: Session = Depends(get_db),
    runtime: RuntimeSession = Depends(require_runtime_session),
) -> IssueView:
    issue = db.get(Issue, issue_id)
    if issue is None or issue.deleted_at is not None:
        raise HTTPException(status_code=404, detail="问题不存在")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(issue, key, value)
    db.add(Activity(issue_id=issue.id, action_type="updated", comment="修改问题信息", operator_name=runtime.operator_name))
    db.commit()
    db.refresh(issue)
    return to_issue_view(issue)


@router.post("/{issue_id}/link", response_model=IssueView)
def link_feedback(
    issue_id: int,
    payload: IssueLink,
    db: Session = Depends(get_db),
    runtime: RuntimeSession = Depends(require_runtime_session),
) -> IssueView:
    issue = db.get(Issue, issue_id)
    feedback = db.get(Feedback, payload.feedback_id)
    if issue is None or issue.deleted_at is not None:
        raise HTTPException(status_code=404, detail="问题不存在")
    if feedback is None or feedback.deleted_at is not None:
        raise HTTPException(status_code=404, detail="反馈不存在")
    exists = db.scalar(select(IssueFeedback).where(
        IssueFeedback.issue_id == issue_id, IssueFeedback.feedback_id == payload.feedback_id
    ))
    if exists is None:
        db.add(IssueFeedback(issue_id=issue_id, feedback_id=payload.feedback_id, relation_type="manual", confirmed_by_name=runtime.operator_name))
        db.add(Activity(issue_id=issue_id, action_type="feedback_linked", comment=f"关联反馈 FB-{payload.feedback_id:04d}", operator_name=runtime.operator_name))
        db.commit()
        db.refresh(issue)
    return to_issue_view(issue)


@router.post("/{issue_id}/complete", response_model=IssueView)
def complete_issue(
    issue_id: int,
    payload: IssueComplete,
    db: Session = Depends(get_db),
    runtime: RuntimeSession = Depends(require_runtime_session),
) -> IssueView:
    issue = db.get(Issue, issue_id)
    if issue is None or issue.deleted_at is not None:
        raise HTTPException(status_code=404, detail="问题不存在")
    issue.status = "processed"
    issue.solution = payload.solution
    issue.processed_by_name = runtime.operator_name
    issue.processed_at = datetime.now(timezone.utc)
    db.add(Activity(issue_id=issue.id, action_type="processed", comment=payload.solution, operator_name=runtime.operator_name))
    db.commit()
    db.refresh(issue)
    return to_issue_view(issue)


@router.delete("/{issue_id}", status_code=204)
def delete_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    runtime: RuntimeSession = Depends(require_runtime_session),
) -> None:
    issue = db.get(Issue, issue_id)
    if issue is None or issue.deleted_at is not None:
        raise HTTPException(status_code=404, detail="问题不存在")
    issue.deleted_at = datetime.now(timezone.utc)
    issue.deleted_by_name = runtime.operator_name
    db.add(Activity(issue_id=issue.id, action_type="deleted", comment="删除问题", operator_name=runtime.operator_name))
    db.commit()

