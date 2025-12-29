"""
Review management API endpoints.
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import get_current_active_user, get_moderator_user
from app.database.session import get_db
from app.models.models import User
from app.models.schemas import (
    Review as ReviewSchema,
    ReviewCreate,
    ReviewUpdate
)
from app.services.review_service import ReviewService
from app.services.book_service import BookService

router = APIRouter()

@router.get("/my-reviews", response_model=List[ReviewSchema])
async def get_my_reviews_alias(
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Alias endpoint used by tests: `/reviews/my-reviews`.
    Placed before dynamic `{review_id}` routes to avoid path conflicts.
    """
    review_service = ReviewService(db)
    reviews = await review_service.get_reviews_by_user(current_user.id, skip, limit)
    return reviews


@router.post("/books/{book_id}/reviews", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    book_id: int,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new review for a book.
    """
    # Check if book exists
    book_service = BookService(db)
    book = await book_service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    review_service = ReviewService(db)

    review = await review_service.create_review(review_data, book_id, current_user.id)
    
    return review


@router.get("/books/{book_id}/reviews", response_model=List[ReviewSchema])
async def get_book_reviews(
    book_id: int,
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all reviews for a book.
    """
    # Check if book exists
    book_service = BookService(db)
    book = await book_service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    review_service = ReviewService(db)
    reviews = await review_service.get_reviews_by_book(book_id, skip, limit)
    
    return reviews


@router.get("/{review_id}", response_model=ReviewSchema)
async def get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get a specific review by ID.
    """
    review_service = ReviewService(db)
    review = await review_service.get_review_by_id(review_id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return review


@router.put("/{review_id}", response_model=ReviewSchema)
async def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update a review. Users can only update their own reviews.
    """
    review_service = ReviewService(db)
    review = await review_service.get_review_by_id(review_id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if user owns the review or is moderator/admin
    if review.user_id != current_user.id and current_user.role.value not in ['admin', 'moderator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own reviews"
        )
    
    try:
        updated_review = await review_service.update_review(review_id, review_update, current_user.id)
        return updated_review
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{review_id}", status_code=status.HTTP_200_OK)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a review. Users can only delete their own reviews unless they are moderators/admins.
    """
    review_service = ReviewService(db)
    review = await review_service.get_review_by_id(review_id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if user owns the review or is moderator/admin
    if review.user_id != current_user.id and current_user.role.value not in ['admin', 'moderator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own reviews"
        )
    
    try:
        success = await review_service.delete_review(review_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    return {"status": "deleted", "id": review_id}


@router.get("/user/{user_id}", response_model=List[ReviewSchema])
async def get_user_reviews(
    user_id: int,
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all reviews by a specific user.
    """
    review_service = ReviewService(db)
    reviews = await review_service.get_reviews_by_user(user_id, skip, limit)
    
    return reviews


@router.get("/user/me/reviews", response_model=List[ReviewSchema])
async def get_my_reviews(
    skip: int = Query(0, ge=0, description="Number of reviews to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get current user's reviews.
    """
    review_service = ReviewService(db)
    reviews = await review_service.get_reviews_by_user(current_user.id, skip, limit)
    
    return reviews
