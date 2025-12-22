"""
Book service for book management operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.models import Book, Review, User
from app.models.schemas import BookCreate, BookUpdate


class BookService:
    """Service class for book operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_book(self, book_data: BookCreate) -> Book:
        """Create a new book."""
        # Check if ISBN already exists
        if book_data.isbn:
            stmt = select(Book).where(Book.isbn == book_data.isbn)
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("Book with this ISBN already exists")
        
        # Create book
        db_book = Book(
            title=book_data.title,
            author=book_data.author,
            genre=book_data.genre,
            year_published=book_data.year_published,
            isbn=book_data.isbn,
            content=book_data.content
        )
        
        self.db.add(db_book)
        await self.db.commit()
        await self.db.refresh(db_book)
        
        return db_book
    
    async def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """Get book by ID."""
        stmt = select(Book).where(Book.id == book_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_book_with_reviews(self, book_id: int) -> Optional[Book]:
        """Get book with reviews and user information."""
        stmt = (
            select(Book)
            .options(
                selectinload(Book.reviews).selectinload(Review.user)
            )
            .where(Book.id == book_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_books(
        self, 
        skip: int = 0, 
        limit: int = 100,
        genre: Optional[str] = None,
        author: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        search: Optional[str] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
    ) -> Any:
        """Get list of books with filtering and pagination.

        If `page` and `size` are provided, returns a pagination dict:
        { items: [...], total: int, page: int, size: int }.
        Otherwise returns a list of books.
        """
        stmt = select(Book)
        
        # Apply filters
        conditions = []
        
        if genre:
            conditions.append(Book.genre.ilike(f"%{genre}%"))
        
        if author:
            conditions.append(Book.author.ilike(f"%{author}%"))
        
        if year_from:
            conditions.append(Book.year_published >= year_from)
        
        if year_to:
            conditions.append(Book.year_published <= year_to)
        
        if search:
            search_conditions = or_(
                Book.title.ilike(f"%{search}%"),
                Book.author.ilike(f"%{search}%"),
                Book.summary.ilike(f"%{search}%")
            )
            conditions.append(search_conditions)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Pagination handling
        if page is not None and size is not None:
            page = max(1, int(page))
            size = max(1, int(size))
            offset = (page - 1) * size
            data_stmt = stmt.offset(offset).limit(size)
            data_result = await self.db.execute(data_stmt)
            items = data_result.scalars().all()

            # total count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = (await self.db.execute(count_stmt)).scalar_one()
            return {
                "items": items,
                "total": int(total),
                "page": page,
                "size": size,
            }
        else:
            stmt = stmt.offset(skip).limit(limit)
            result = await self.db.execute(stmt)
            return result.scalars().all()
    
    async def update_book(self, book_id: int, book_update: BookUpdate) -> Optional[Book]:
        """Update book information."""
        # Check if book exists
        book = await self.get_book_by_id(book_id)
        if not book:
            return None
        
        # Check ISBN uniqueness if being updated
        if book_update.isbn and book_update.isbn != book.isbn:
            stmt = select(Book).where(Book.isbn == book_update.isbn)
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("Book with this ISBN already exists")
        
        # Update fields
        update_data = book_update.model_dump(exclude_unset=True)
        if update_data:
            stmt = update(Book).where(Book.id == book_id).values(**update_data)
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(book)
        
        return book
    
    async def delete_book(self, book_id: int) -> bool:
        """Delete book by ID."""
        book = await self.get_book_by_id(book_id)
        if not book:
            return False
        
        await self.db.delete(book)
        await self.db.commit()
        return True

    async def get_book(self, book_id: int) -> Optional[Book]:
        """Alias to get book by ID (tests convenience)."""
        return await self.get_book_by_id(book_id)
    
    async def update_book_summary(self, book_id: int, summary: str) -> Optional[Book]:
        """Update book summary."""
        stmt = update(Book).where(Book.id == book_id).values(summary=summary)
        await self.db.execute(stmt)
        await self.db.commit()
        
        return await self.get_book_by_id(book_id)
    
    async def get_book_statistics(self, book_id: int) -> Dict[str, Any]:
        """Get book statistics including average rating and review count."""
        # Get average rating and review count
        stmt = (
            select(
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("review_count")
            )
            .where(Review.book_id == book_id)
        )
        
        result = await self.db.execute(stmt)
        stats = result.first()
        
        return {
            "average_rating": float(stats.avg_rating) if stats.avg_rating else None,
            "total_reviews": stats.review_count,
        }
    
    async def get_books_by_genre(self, genre: str, limit: int = 10) -> List[Book]:
        """Get books by genre."""
        stmt = (
            select(Book)
            .where(Book.genre.ilike(f"%{genre}%"))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_books_by_author(self, author: str, limit: int = 10) -> List[Book]:
        """Get books by author."""
        stmt = (
            select(Book)
            .where(Book.author.ilike(f"%{author}%"))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_highly_rated_books(self, min_rating: float = 4.0, limit: int = 10) -> List[Book]:
        """Get highly rated books."""
        stmt = (
            select(
                Book,
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("review_count")
            )
            .join(Review, Book.id == Review.book_id)
            .group_by(Book.id)
            .having(func.avg(Review.rating) >= min_rating)
            .having(func.count(Review.id) >= 3)  # At least 3 reviews
            .order_by(func.avg(Review.rating).desc())
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        books_with_ratings = result.all()
        
        return [book for book, _, _ in books_with_ratings]