"""
Book management API endpoints.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import get_current_active_user, get_moderator_user
from app.database.session import get_db
from app.models.models import User
from app.models.schemas import (
    Book as BookSchema,
    BookCreate,
    BookUpdate, 
    BookWithReviews,
    BookSummary,
    PaginatedBooksResponse,
    Review as ReviewSchema,
    ReviewCreate,
)
from app.services.book_service import BookService
from app.services.ai_service import AIService
from app.services.review_service import ReviewService

router = APIRouter()


@router.post("/", response_model=BookSchema, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_data: BookCreate,
    current_user: User = Depends(get_moderator_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new book. Requires moderator or admin role.
    """
    book_service = BookService(db)
    
    try:
        book = await book_service.create_book(book_data)
        
        # Generate summary if content is provided
        if book_data.content and len(book_data.content) > 50:
            try:
                ai_service = AIService()
                summary_response = await ai_service.generate_book_summary(
                    book.title, 
                    book.author, 
                    book_data.content
                )
                await book_service.update_book_summary(book.id, summary_response.summary)
            except Exception as e:
                # Log error but don't fail the book creation
                print(f"Failed to generate summary: {e}")
        
        return await book_service.get_book_by_id(book.id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=PaginatedBooksResponse)
async def get_books(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    author: Optional[str] = Query(None, description="Filter by author"),
    year_from: Optional[int] = Query(None, ge=1000, description="Filter books from this year"),
    year_to: Optional[int] = Query(None, le=2024, description="Filter books up to this year"),
    search: Optional[str] = Query(None, description="Search in title, author, or summary"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get list of books with filtering and pagination.
    """
    book_service = BookService(db)
    result = await book_service.get_books(
        genre=genre,
        author=author,
        year_from=year_from,
        year_to=year_to,
        search=search,
        page=page,
        size=size,
    )
    return result

@router.get("/recommendations")
async def get_recommendations(
    genre: str = Query(None, description="Preferred genre"),
    limit: int = Query(10, ge=1, le=50, description="Max recommendations"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Alias endpoint under /books to provide AI recommendations for tests."""
    book_service = BookService(db)
    available_books = await book_service.get_books(skip=0, limit=1000)
    prefs = {"genres": [genre] if genre else [], "authors": [], "min_rating": None}
    ai_service = AIService()
    recs = await ai_service.generate_recommendations(user_preferences=prefs, available_books=available_books, limit=limit)
    if isinstance(recs, list):
        return {"recommendations": recs}
    titles = [b.title for b in getattr(recs, "books", [])]
    return {"recommendations": titles}

@router.get("/{book_id}", response_model=BookSchema)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get a specific book by ID.
    """
    book_service = BookService(db)
    book = await book_service.get_book_by_id(book_id)
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    return book


@router.put("/{book_id}", response_model=BookSchema)
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    current_user: User = Depends(get_moderator_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update a book's information. Requires moderator or admin role.
    """
    book_service = BookService(db)
    
    try:
        book = await book_service.update_book(book_id, book_update)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        # Regenerate summary if content was updated
        if book_update.content and len(book_update.content) > 50:
            try:
                ai_service = AIService()
                summary_response = await ai_service.generate_book_summary(
                    book.title,
                    book.author,
                    book_update.content
                )
                await book_service.update_book_summary(book.id, summary_response.summary)
            except Exception as e:
                print(f"Failed to regenerate summary: {e}")
        
        return await book_service.get_book_by_id(book_id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{book_id}", status_code=status.HTTP_200_OK)
async def delete_book(
    book_id: int,
    current_user: User = Depends(get_moderator_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a book. Requires moderator or admin role.
    """
    book_service = BookService(db)
    
    success = await book_service.delete_book(book_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    # Return a simple confirmation body for tests expecting 200
    return {"status": "deleted", "id": book_id}


@router.get("/{book_id}/summary", response_model=BookSummary)
async def get_book_summary(
    book_id: int,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get book summary with reviews and ratings.
    """
    book_service = BookService(db)
    
    # Get book with reviews
    book = await book_service.get_book_with_reviews(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Get statistics
    stats = await book_service.get_book_statistics(book_id)
    
    # Get recent reviews (limit to 5)
    recent_reviews = book.reviews[:5] if book.reviews else []
    
    # Generate review summary if there are reviews
    review_summary = book.summary or "No summary available."
    if book.reviews:
        try:
            ai_service = AIService()
            review_texts = [review.review_text for review in book.reviews]
            ratings = [review.rating for review in book.reviews]
            
            ai_review_summary = await ai_service.generate_review_summary(
                book.title, review_texts, ratings
            )
            review_summary = f"{book.summary}\n\nReader Reviews Summary:\n{ai_review_summary}"
        except Exception as e:
            print(f"Failed to generate review summary: {e}")
    
    return BookSummary(
        book=book,
        summary=review_summary,
        average_rating=stats["average_rating"],
        total_reviews=stats["total_reviews"],
        recent_reviews=recent_reviews
    )


@router.get("/genre/{genre}", response_model=List[BookSchema])
async def get_books_by_genre(
    genre: str,
    limit: int = Query(10, ge=1, le=50, description="Number of books to return"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get books by genre.
    """
    book_service = BookService(db)
    books = await book_service.get_books_by_genre(genre, limit)
    return books




@router.get("/author/{author}", response_model=List[BookSchema])
async def get_books_by_author(
    author: str,
    limit: int = Query(10, ge=1, le=50, description="Number of books to return"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get books by author.
    """
    book_service = BookService(db)
    books = await book_service.get_books_by_author(author, limit)
    return books


@router.get("/recommendations/highly-rated", response_model=List[BookSchema])
async def get_highly_rated_books(
    min_rating: float = Query(4.0, ge=1.0, le=5.0, description="Minimum average rating"),
    limit: int = Query(10, ge=1, le=50, description="Number of books to return"),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get highly rated books.
    """
    book_service = BookService(db)
    books = await book_service.get_highly_rated_books(min_rating, limit)
    return books


@router.post("/{book_id}/reviews", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review_for_book(
    book_id: int,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new review for a book (alias under books router for tests).
    """
    # Ensure book exists
    book_service = BookService(db)
    book = await book_service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    review_service = ReviewService(db)
    review = await review_service.create_review(review_data, book_id, current_user.id)
    return review


@router.get("/{book_id}/reviews", response_model=List[ReviewSchema])
async def get_reviews_for_book(
    book_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get reviews for a book (alias under books router for tests).
    """
    book_service = BookService(db)
    book = await book_service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    review_service = ReviewService(db)
    return await review_service.get_reviews_by_book(book_id, skip, limit)