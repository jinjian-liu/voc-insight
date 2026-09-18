from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    feedback_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    product_module: Mapped[str | None] = mapped_column(String(100))
    external_id: Mapped[str | None] = mapped_column(String(100), index=True)
    note: Mapped[str | None] = mapped_column(Text)
    analysis_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    created_by_name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    deleted_by_name: Mapped[str | None] = mapped_column(String(50))

    analysis: Mapped["FeedbackAnalysis | None"] = relationship(
        back_populates="feedback", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    issue_links: Mapped[list["IssueFeedback"]] = relationship(back_populates="feedback")


class FeedbackAnalysis(Base):
    __tablename__ = "feedback_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feedback_id: Mapped[int] = mapped_column(ForeignKey("feedbacks.id"), unique=True, index=True)
    summary: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100))
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    user_impact: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_priority: Mapped[str] = mapped_column(String(10), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    information_missing: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    raw_response: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(30), default="v1", nullable=False)
    confirmed: Mapped[bool] = mapped_column(default=False, nullable=False)
    confirmed_by_name: Mapped[str | None] = mapped_column(String(50))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    feedback: Mapped[Feedback] = relationship(back_populates="analysis")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(300))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    processed_by_name: Mapped[str | None] = mapped_column(String(50))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    solution: Mapped[str | None] = mapped_column(Text)
    created_by_name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    deleted_by_name: Mapped[str | None] = mapped_column(String(50))

    feedback_links: Mapped[list["IssueFeedback"]] = relationship(
        back_populates="issue", cascade="all, delete-orphan", lazy="selectin"
    )
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="issue", cascade="all, delete-orphan", lazy="selectin"
    )


class IssueFeedback(Base):
    __tablename__ = "issue_feedbacks"
    __table_args__ = (UniqueConstraint("issue_id", "feedback_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), index=True)
    feedback_id: Mapped[int] = mapped_column(ForeignKey("feedbacks.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)
    similarity_score: Mapped[float | None] = mapped_column(Float)
    confirmed_by_name: Mapped[str] = mapped_column(String(50), nullable=False)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    issue: Mapped[Issue] = relationship(back_populates="feedback_links")
    feedback: Mapped[Feedback] = relationship(back_populates="issue_links", lazy="selectin")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    operator_name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    issue: Mapped[Issue] = relationship(back_populates="activities")
