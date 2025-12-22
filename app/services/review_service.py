"""
Review service for review management operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, desc
from sqlalchemy.orm import selectinload

from app.models.models import Review, Book, User
from app.models.schemas import ReviewCreate, ReviewUpdate


class ReviewService:
    """Service class for review operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_review(self, review_data: ReviewCreate, book_id: int, user_id: int) -> Review:
        """Create a new review."""
        # Check if book exists
        stmt = select(Book).where(Book.id == book_id)
        result = await self.db.execute(stmt)
        book = result.scalar_one_or_none()
        if not book:
            raise ValueError("Book not found")
        
        # Check if user already reviewed this book
        stmt = select(Review).where(
            and_(Review.book_id == book_id, Review.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        existing_review = result.scalar_one_or_none()
        if existing_review:
            raise ValueError("User has already reviewed this book")
        
        # Create review
        db_review = Review(
            book_id=book_id,
            user_id=user_id,
            review_text=review_data.review_text,
            rating=review_data.rating
        )
        
        self.db.add(db_review)
        await self.db.commit()
        await self.db.refresh(db_review)
        
        return db_review
    
    async def get_review_by_id(self, review_id: int) -> Optional[Review]:
        """Get review by ID with user information."""
        stmt = (
            select(Review)
            .options(selectinload(Review.user), selectinload(Review.book))
            .where(Review.id == review_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_reviews_by_book(
        self, 
        book_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Review]:
        """Get reviews for a specific book."""
        stmt = (
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.book_id == book_id)
            .order_by(desc(Review.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_book_reviews(
        self,
        book_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Review]:
        """Alias for getting reviews for a specific book (API/tests compatibility)."""
        return await self.get_reviews_by_book(book_id, skip=skip, limit=limit)
    
    async def get_reviews_by_user(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Review]:
        """Get reviews by a specific user."""
        stmt = (
            select(Review)
            .options(selectinload(Review.book))
            .where(Review.user_id == user_id)
            .order_by(desc(Review.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_user_reviews(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Review]:
        """Alias for getting reviews by a specific user (API/tests compatibility)."""
        return await self.get_reviews_by_user(user_id, skip=skip, limit=limit)
    
    async def update_review(
        self, 
        review_id: int, 
        review_update: ReviewUpdate,
        user_id: int
    ) -> Optional[Review]:
        """Update review (only by the review author)."""
        # Check if review exists and belongs to user
        review = await self.get_review_by_id(review_id)
        if not review:
            return None
        
        if review.user_id != user_id:
            raise ValueError("User can only update their own reviews")
        
        # Update fields
        update_data = review_update.model_dump(exclude_unset=True)
        if update_data:
            stmt = update(Review).where(Review.id == review_id).values(**update_data)
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(review)
        
        return review
    
    async def delete_review(self, review_id: int, user_id: int) -> bool:
        """Delete review (only by the review author or admin)."""
        review = await self.get_review_by_id(review_id)
        if not review:
            return False
        
        # Check if user owns the review (admin check should be done at API level)
        if review.user_id != user_id:
            raise ValueError("User can only delete their own reviews")
        
        await self.db.delete(review)
        await self.db.commit()
        return True

    async def get_review(self, review_id: int) -> Optional[Review]:
        """Alias for getting a review by ID (tests convenience)."""
        return await self.get_review_by_id(review_id)
    
    async def get_book_review_summary(self, book_id: int) -> Dict[str, Any]:
        """Get comprehensive review summary for a book."""
        # Get overall statistics
        stmt = (
            select(
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("total_reviews"),
                func.min(Review.rating).label("min_rating"),
                func.max(Review.rating).label("max_rating")
            )
            .where(Review.book_id == book_id)
        )
        result = await self.db.execute(stmt)
        stats = result.first()
        
        # Get rating distribution
        rating_dist_stmt = (
            select(
                Review.rating,
                func.count(Review.id).label("count")
            )
            .where(Review.book_id == book_id)
            .group_by(Review.rating)
            .order_by(Review.rating)
        )
        rating_dist_result = await self.db.execute(rating_dist_stmt)
        rating_distribution = {
            str(rating): count for rating, count in rating_dist_result.all()
        }
        
        # Get recent reviews
        recent_reviews_stmt = (
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.book_id == book_id)
            .order_by(desc(Review.created_at))
            .limit(5)
        )
        recent_reviews_result = await self.db.execute(recent_reviews_stmt)
        recent_reviews = recent_reviews_result.scalars().all()
        
        return {
            "average_rating": float(stats.avg_rating) if stats.avg_rating else None,
            "total_reviews": stats.total_reviews,
            "min_rating": float(stats.min_rating) if stats.min_rating else None,
            "max_rating": float(stats.max_rating) if stats.max_rating else None,
            "rating_distribution": rating_distribution,
            "recent_reviews": recent_reviews
        }

    async def get_book_rating_summary(self, book_id: int) -> Dict[str, Any]:
        """Return only rating-focused summary for a book (tests convenience)."""
        summary = await self.get_book_review_summary(book_id)
        return {
            "average_rating": summary["average_rating"],
            "total_reviews": summary["total_reviews"],
            "min_rating": summary["min_rating"],
            "max_rating": summary["max_rating"],
            "rating_distribution": summary["rating_distribution"],
        }
    
    async def get_user_review_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get review statistics for a user."""
        stmt = (
            select(
                func.count(Review.id).label("total_reviews"),
                func.avg(Review.rating).label("avg_rating_given"),
                func.min(Review.created_at).label("first_review_date"),
                func.max(Review.created_at).label("last_review_date")
            )
            .where(Review.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        stats = result.first()
        
        return {
            "total_reviews": stats.total_reviews,
            "average_rating_given": float(stats.avg_rating_given) if stats.avg_rating_given else None,
            "first_review_date": stats.first_review_date,
            "last_review_date": stats.last_review_date
        }