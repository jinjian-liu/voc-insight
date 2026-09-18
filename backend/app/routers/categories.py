from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_runtime_session
from app.models import Category
from app.schemas import CategoryCreate, CategoryView
from app.session_store import RuntimeSession


router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryView])
def list_categories(
    db: Session = Depends(get_db),
    _: RuntimeSession = Depends(require_runtime_session),
) -> list[Category]:
    return list(
        db.scalars(
            select(Category)
            .where(Category.deleted_at.is_(None))
            .order_by(Category.sort_order, Category.id)
        ).all()
    )


@router.post("", response_model=CategoryView, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: RuntimeSession = Depends(require_runtime_session),
) -> Category:
    max_order = max(db.scalars(select(Category.sort_order)).all() or [0])
    category = Category(name=payload.name.strip(), description=payload.description, sort_order=max_order + 1)
    db.add(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="分类名称已存在")
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryView)
def update_category(
    category_id: int,
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: RuntimeSession = Depends(require_runtime_session),
) -> Category:
    category = db.get(Category, category_id)
    if category is None or category.deleted_at is not None:
        raise HTTPException(status_code=404, detail="分类不存在")
    category.name = payload.name.strip()
    category.description = payload.description
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="分类名称已存在")
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: RuntimeSession = Depends(require_runtime_session),
) -> None:
    category = db.get(Category, category_id)
    if category is None or category.deleted_at is not None:
        raise HTTPException(status_code=404, detail="分类不存在")
    category.deleted_at = datetime.now(timezone.utc)
    db.commit()

