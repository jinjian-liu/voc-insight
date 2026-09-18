from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SessionCreate(BaseModel):
    operator_name: str = Field(min_length=1, max_length=50)
    api_key: str = Field(min_length=1, max_length=500)

    @field_validator("operator_name", "api_key")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value


class SessionView(BaseModel):
    ready: bool
    operator_name: str
    expires_at: datetime


class FeedbackCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10_000)
    source: str = Field(min_length=1, max_length=50)
    feedback_time: datetime
    product_module: str | None = Field(default=None, max_length=100)
    external_id: str | None = Field(default=None, max_length=100)
    note: str | None = Field(default=None, max_length=2_000)

    @field_validator("content", "source")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value

    @field_validator("product_module", "external_id", "note")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class FeedbackView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    source: str
    feedback_time: datetime
    product_module: str | None
    external_id: str | None
    note: str | None
    analysis_status: str
    created_by_name: str
    created_at: datetime
    analysis: "AnalysisView | None" = None


class FeedbackPage(BaseModel):
    items: list[FeedbackView]
    total: int
    page: int
    page_size: int


class ImportResult(BaseModel):
    success: int
    failed: int
    errors: list[str] = Field(default_factory=list)


class AnalysisPayload(BaseModel):
    summary: str = Field(min_length=1, max_length=300)
    category: str = Field(min_length=1, max_length=100)
    subcategory: str | None = Field(default=None, max_length=100)
    keywords: list[str] = Field(default_factory=list, max_length=10)
    sentiment: Literal["positive", "neutral", "negative"]
    severity: Literal["low", "medium", "high", "urgent"]
    user_impact: str = Field(min_length=1, max_length=2_000)
    suggested_priority: Literal["P0", "P1", "P2", "P3"]
    confidence: float = Field(ge=0, le=1)
    information_missing: list[str] = Field(default_factory=list, max_length=10)


class AnalysisView(AnalysisPayload):
    model_config = ConfigDict(from_attributes=True)

    id: int
    feedback_id: int
    model_name: str
    prompt_version: str
    confirmed: bool
    confirmed_by_name: str | None
    confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AnalysisUpdate(AnalysisPayload):
    confirmed: bool = True


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)


class CategoryView(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sort_order: int


class IssueCreate(BaseModel):
    feedback_id: int
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=5_000)
    category: str = Field(min_length=1, max_length=100)
    severity: str
    priority: str


class IssueUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, min_length=1, max_length=5_000)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    severity: str | None = None
    priority: str | None = None


class IssueComplete(BaseModel):
    solution: str = Field(min_length=1, max_length=5_000)


class IssueLink(BaseModel):
    feedback_id: int


class ActivityView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_type: str
    comment: str | None
    operator_name: str
    created_at: datetime


class IssueView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    category: str
    status: str
    severity: str
    priority: str
    processed_by_name: str | None
    processed_at: datetime | None
    solution: str | None
    created_by_name: str
    created_at: datetime
    updated_at: datetime
    feedback_count: int = 0


class IssueDetail(IssueView):
    feedbacks: list[FeedbackView] = Field(default_factory=list)
    activities: list[ActivityView] = Field(default_factory=list)


class IssuePage(BaseModel):
    items: list[IssueView]
    total: int
    page: int
    page_size: int


class SimilarIssue(IssueView):
    similarity_score: float


class DashboardOverview(BaseModel):
    feedback_total: int
    feedback_pending_analysis: int
    issue_pending: int
    issue_processed: int
    high_severity_pending: int
    average_resolution_hours: float | None
    category_distribution: list[dict]
    status_distribution: list[dict]
    top_issues: list[IssueView]


FeedbackView.model_rebuild()
