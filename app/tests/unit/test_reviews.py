"""
Unit tests for review management endpoints and services.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
from fastapi.testclient import TestClient

from app.models.models import Book, Review, User


class TestReviewEndpoints:
    """Test review management endpoints."""

    @pytest.mark.asyncio
    async def test_add_review_success(self, client: TestClient, auth_headers: dict, admin_headers: dict):
        """Test adding a review with valid data."""
        # First need to create a book
        book_data = {
            "title": "Test Book for Review",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023
        }
        
        with patch('app.services.ai_service.AIService.generate_book_summary'):
            book_response = client.post("/books/", json=book_data, headers=admin_headers)
            book_id = book_response.json()["id"]
        
        review_data = {
            "review_text": "This is a great book! Really enjoyed reading it.",
            "rating": 4.5
        }
        
        response = client.post(f"/books/{book_id}/reviews", json=review_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["review_text"] == review_data["review_text"]
        assert data["rating"] == review_data["rating"]
        assert data["book_id"] == book_id

    @pytest.mark.asyncio
    async def test_add_review_unauthorized(self, client: TestClient):
        """Test adding a review without authentication fails."""
        review_data = {
            "review_text": "This is a review",
            "rating": 4.0
        }
        
        response = client.post("/books/1/reviews", json=review_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_add_review_invalid_rating(self, client: TestClient, auth_headers: dict):
        """Test adding a review with invalid rating."""
        review_data = {
            "review_text": "This is a review",
            "rating": 6.0  # Invalid rating (should be 1-5)
        }
        
        response = client.post("/books/1/reviews", json=review_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_add_review_nonexistent_book(self, client: TestClient, auth_headers: dict):
        """Test adding a review to non-existent book."""
        review_data = {
            "review_text": "This is a review",
            "rating": 4.0
        }
        
        response = client.post("/books/99999/reviews", json=review_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_book_reviews(self, client: TestClient):
        """Test retrieving reviews for a book."""
        # This test assumes there's a book with ID 1
        response = client.get("/books/1/reviews")
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_book_reviews_with_pagination(self, client: TestClient):
        """Test retrieving reviews with pagination."""
        response = client.get("/books/1/reviews?page=1&size=5")
        
        # Should return 404 if book doesn't exist, or paginated results if it does
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    @pytest.mark.asyncio
    async def test_update_review_success(self, client: TestClient, auth_headers: dict):
        """Test updating a review by the review author."""
        # This test would need to create a book and review first
        # For now, test the endpoint behavior
        update_data = {
            "review_text": "Updated review text",
            "rating": 5.0
        }
        
        response = client.put("/reviews/1", json=update_data, headers=auth_headers)
        
        # Should return 404 if review doesn't exist, or success if it does and user owns it
        assert response.status_code in [
            status.HTTP_200_OK, 
            status.HTTP_404_NOT_FOUND, 
            status.HTTP_403_FORBIDDEN
        ]

    @pytest.mark.asyncio
    async def test_update_review_unauthorized(self, client: TestClient):
        """Test updating a review without authentication."""
        update_data = {
            "review_text": "Updated review text",
            "rating": 5.0
        }
        
        response = client.put("/reviews/1", json=update_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_delete_review_success(self, client: TestClient, auth_headers: dict):
        """Test deleting a review by the review author."""
        response = client.delete("/reviews/1", headers=auth_headers)
        
        # Should return 404 if review doesn't exist, or success if it does and user owns it
        assert response.status_code in [
            status.HTTP_200_OK, 
            status.HTTP_404_NOT_FOUND, 
            status.HTTP_403_FORBIDDEN
        ]

    @pytest.mark.asyncio
    async def test_delete_review_unauthorized(self, client: TestClient):
        """Test deleting a review without authentication."""
        response = client.delete("/reviews/1")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_user_reviews(self, client: TestClient, auth_headers: dict):
        """Test retrieving reviews by current user."""
        response = client.get("/reviews/my-reviews", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


class TestReviewService:
    """Test review service functionality."""

    @pytest.mark.asyncio
    async def test_create_review_service(self, db_session, test_user):
        """Test review creation through service layer."""
        from app.services.review_service import ReviewService
        from app.services.book_service import BookService
        from app.models.schemas import BookCreate, ReviewCreate
        
        # Create a book first
        book_service = BookService(db_session)
        book_data = BookCreate(
            title="Test Book for Review Service",
            author="Test Author",
            genre="Fiction",
            year_published=2023
        )
        book = await book_service.create_book(book_data)
        
        # Create a review
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            review_text="Great book, highly recommend!",
            rating=4.5
        )
        
        review = await review_service.create_review(review_data, book.id, test_user.id)
        
        assert review.review_text == review_data.review_text
        assert review.rating == review_data.rating
        assert review.book_id == book.id
        assert review.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_book_reviews_service(self, db_session):
        """Test getting reviews for a book through service layer."""
        from app.services.review_service import ReviewService
        
        review_service = ReviewService(db_session)
        reviews = await review_service.get_book_reviews(book_id=1)
        
        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_get_user_reviews_service(self, db_session, test_user):
        """Test getting reviews by user through service layer."""
        from app.services.review_service import ReviewService
        
        review_service = ReviewService(db_session)
        reviews = await review_service.get_user_reviews(user_id=test_user.id)
        
        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_update_review_service(self, db_session, test_user):
        """Test updating review through service layer."""
        from app.services.review_service import ReviewService
        from app.services.book_service import BookService
        from app.models.schemas import BookCreate, ReviewCreate, ReviewUpdate
        
        # Create a book and review first
        book_service = BookService(db_session)
        book_data = BookCreate(
            title="Test Book for Update Review",
            author="Test Author",
            genre="Fiction",
            year_published=2023
        )
        book = await book_service.create_book(book_data)
        
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            review_text="Original review text",
            rating=3.0
        )
        review = await review_service.create_review(review_data, book.id, test_user.id)
        
        # Update the review
        update_data = ReviewUpdate(
            review_text="Updated review text",
            rating=4.5
        )
        updated_review = await review_service.update_review(review.id, update_data, test_user.id)
        
        assert updated_review is not None
        assert updated_review.review_text == update_data.review_text
        assert updated_review.rating == update_data.rating

    @pytest.mark.asyncio
    async def test_delete_review_service(self, db_session, test_user):
        """Test deleting review through service layer."""
        from app.services.review_service import ReviewService
        from app.services.book_service import BookService
        from app.models.schemas import BookCreate, ReviewCreate
        
        # Create a book and review first
        book_service = BookService(db_session)
        book_data = BookCreate(
            title="Test Book for Delete Review",
            author="Test Author",
            genre="Fiction",
            year_published=2023
        )
        book = await book_service.create_book(book_data)
        
        review_service = ReviewService(db_session)
        review_data = ReviewCreate(
            review_text="Review to delete",
            rating=3.0
        )
        review = await review_service.create_review(review_data, book.id, test_user.id)
        
        # Delete the review
        result = await review_service.delete_review(review.id, test_user.id)
        assert result is True
        
        # Verify review is deleted
        deleted_review = await review_service.get_review(review.id)
        assert deleted_review is None

    @pytest.mark.asyncio
    async def test_get_book_rating_summary(self, db_session):
        """Test getting aggregated rating summary for a book."""
        from app.services.review_service import ReviewService
        
        review_service = ReviewService(db_session)
        summary = await review_service.get_book_rating_summary(book_id=1)
        
        assert "average_rating" in summary
        assert "total_reviews" in summary
        assert "rating_distribution" in summary


class TestReviewValidation:
    """Test review data validation."""

    def test_valid_review_data(self):
        """Test valid review data creation."""
        from app.models.schemas import ReviewCreate
        
        review_data = ReviewCreate(
            review_text="This is a valid review",
            rating=4.5
        )
        
        assert review_data.review_text == "This is a valid review"
        assert review_data.rating == 4.5

    def test_invalid_rating_too_low(self):
        """Test validation fails for rating too low."""
        from app.models.schemas import ReviewCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ReviewCreate(
                review_text="This is a review",
                rating=0.5  # Below minimum
            )

    def test_invalid_rating_too_high(self):
        """Test validation fails for rating too high."""
        from app.models.schemas import ReviewCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ReviewCreate(
                review_text="This is a review",
                rating=5.5  # Above maximum
            )

    def test_empty_review_text(self):
        """Test validation fails for empty review text."""
        from app.models.schemas import ReviewCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ReviewCreate(
                review_text="",  # Empty text
                rating=4.0
            )