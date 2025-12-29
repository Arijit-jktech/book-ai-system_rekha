"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator

from app.models.models import UserRole


# User Schemas
class UserBase(BaseModel):
    """Base user schema with common user fields."""
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        description="Username must be 3-50 characters long",
        example="johndoe"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address",
        example="john.doe@example.com"
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=100,
        description="Password must be at least 8 characters long",
        example="securepassword123"
    )
    role: Optional[UserRole] = Field(
        default=UserRole.USER,
        description="User role (admin, moderator, or user)",
        example="user"
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    username: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=50,
        description="New username (3-50 characters)",
        example="newusername"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="New email address",
        example="newemail@example.com"
    )
    role: Optional[UserRole] = Field(
        None,
        description="New user role",
        example="moderator"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether the user account is active",
        example=True
    )


class User(UserBase):
    """Complete user information schema."""
    id: int = Field(..., description="Unique user identifier", example=1)
    role: UserRole = Field(..., description="User role", example="user")
    is_active: bool = Field(..., description="Account status", example=True)
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john.doe@example.com",
                "role": "user",
                "is_active": True,
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-02T12:00:00Z"
            }
        }


# Authentication Schemas
class Token(BaseModel):
    """JWT authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds", example=86400)
    user: User = Field(..., description="Authenticated user information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": 1,
                    "username": "johndoe",
                    "email": "john.doe@example.com",
                    "role": "user",
                    "is_active": True
                }
            }
        }


class TokenData(BaseModel):
    """JWT token payload data."""
    user_id: Optional[int] = Field(None, description="User ID from token")
    username: Optional[str] = Field(None, description="Username from token")
    role: Optional[str] = Field(None, description="User role from token")


# Book Schemas
class BookBase(BaseModel):
    """Base book schema with common book fields."""
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Book title",
        example="The Great Gatsby"
    )
    author: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Book author",
        example="F. Scott Fitzgerald"
    )
    genre: str = Field(
        ..., 
        min_length=1, 
        max_length=50,
        description="Book genre",
        example="Fiction"
    )
    year_published: int = Field(
        ..., 
        ge=1000, 
        le=2024,
        description="Year the book was published",
        example=1925
    )
    isbn: Optional[str] = Field(
        None, 
        max_length=20,
        description="ISBN number",
        example="978-0-7432-7356-5"
    )


class BookCreate(BookBase):
    """Schema for creating a new book."""
    content: Optional[str] = Field(
        None,
        description="Full book content for AI summary generation",
        example="In my younger and more vulnerable years my father gave me some advice..."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "genre": "Fiction",
                "year_published": 1925,
                "isbn": "978-0-7432-7356-5",
                "content": "In my younger and more vulnerable years..."
            }
        }


class BookUpdate(BaseModel):
    """Schema for updating book information."""
    title: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=200,
        description="New book title",
        example="The Great Gatsby - Revised Edition"
    )
    author: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100,
        description="Updated author name",
        example="F. Scott Fitzgerald"
    )
    genre: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50,
        description="Updated genre",
        example="Classic Literature"
    )
    year_published: Optional[int] = Field(
        None, 
        ge=1000, 
        le=2024,
        description="Updated publication year",
        example=1925
    )
    summary: Optional[str] = Field(
        None,
        description="Updated book summary",
        example="A classic American novel set in the Jazz Age..."
    )
    content: Optional[str] = Field(
        None,
        description="Updated book content",
        example="Updated book content..."
    )
    isbn: Optional[str] = Field(
        None, 
        max_length=20,
        description="Updated ISBN",
        example="978-0-7432-7356-5"
    )


class Book(BookBase):
    """Complete book information schema."""
    id: int = Field(..., description="Unique book identifier", example=1)
    summary: Optional[str] = Field(
        None,
        description="AI-generated or manual book summary",
        example="A classic American novel that explores themes of wealth, love, idealism, and moral decay..."
    )
    created_at: datetime = Field(..., description="Book creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "genre": "Fiction",
                "year_published": 1925,
                "isbn": "978-0-7432-7356-5",
                "summary": "A classic American novel that explores themes of wealth, love, idealism...",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-02T12:00:00Z"
            }
        }


class BookWithReviews(Book):
    """Book information including reviews and ratings."""
    reviews: List["Review"] = Field(default=[], description="Book reviews")
    average_rating: Optional[float] = Field(
        None, 
        description="Average rating from all reviews",
        example=4.5
    )
    total_reviews: int = Field(
        default=0, 
        description="Total number of reviews",
        example=42
    )


# Review Schemas
class ReviewBase(BaseModel):
    """Base review schema."""
    review_text: str = Field(..., min_length=10, max_length=2000)
    rating: float = Field(..., ge=1.0, le=5.0)
    
    @validator('rating')
    def validate_rating(cls, v):
        """Validate rating is between 1 and 5."""
        if not (1.0 <= v <= 5.0):
            raise ValueError('Rating must be between 1.0 and 5.0')
        return round(v, 1)


class ReviewCreate(ReviewBase):
    """Review creation schema."""
    pass


class ReviewUpdate(BaseModel):
    """Review update schema."""
    review_text: Optional[str] = Field(None, min_length=10, max_length=2000)
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    
    @validator('rating')
    def validate_rating(cls, v):
        """Validate rating is between 1 and 5."""
        if v is not None and not (1.0 <= v <= 5.0):
            raise ValueError('Rating must be between 1.0 and 5.0')
        return round(v, 1) if v is not None else v


class Review(ReviewBase):
    """Review response schema."""
    id: int
    book_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[User] = None
    
    class Config:
        from_attributes = True


# Summary Schemas
class BookSummary(BaseModel):
    """Book summary response."""
    book: Book
    summary: str
    average_rating: Optional[float] = None
    total_reviews: int = 0
    recent_reviews: List[Review] = []


class GenerateSummaryRequest(BaseModel):
    """Generate summary request."""
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    max_length: Optional[int] = Field(500, ge=50, le=2000)


class GenerateSummaryResponse(BaseModel):
    """Generate summary response."""
    summary: str
    generated_at: datetime


# Recommendation Schemas
class RecommendationRequest(BaseModel):
    """Book recommendation request."""
    genres: Optional[List[str]] = []
    authors: Optional[List[str]] = []
    min_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    max_results: Optional[int] = Field(10, ge=1, le=50)


class RecommendationResponse(BaseModel):
    """Book recommendation response."""
    books: List[Book]
    total_results: int
    recommendation_reason: str


# Error Schemas
class ErrorDetail(BaseModel):
    """Error detail."""
    message: str
    type: Optional[str] = None
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    errors: Optional[List[ErrorDetail]] = None


# Update forward references
BookWithReviews.model_rebuild()


class PaginatedBooksResponse(BaseModel):
    """Paginated list response for books."""

    items: List[Book]
    total: int
    page: int
    size: int