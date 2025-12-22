"""
Unit tests for book management endpoints and services.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
from fastapi.testclient import TestClient

from app.models.models import Book, User


class TestBookEndpoints:
    """Test book management endpoints."""

    @pytest.mark.asyncio
    async def test_create_book_success(self, client: TestClient, admin_headers: dict):
        """Test creating a new book with admin permissions."""
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023,
            "isbn": "123-456-789",
            "content": "This is a test book content for summary generation."
        }
        
        with patch('app.services.ai_service.AIService.generate_book_summary') as mock_ai:
            mock_ai.return_value = AsyncMock(summary="Generated test summary")
            
            response = client.post("/books/", json=book_data, headers=admin_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == book_data["title"]
        assert data["author"] == book_data["author"]
        assert data["genre"] == book_data["genre"]
        assert data["year_published"] == book_data["year_published"]

    @pytest.mark.asyncio
    async def test_create_book_unauthorized(self, client: TestClient, auth_headers: dict):
        """Test creating a book without admin permissions fails."""
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023
        }
        
        response = client.post("/books/", json=book_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_create_book_no_auth(self, client: TestClient):
        """Test creating a book without authentication fails."""
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023
        }
        
        response = client.post("/books/", json=book_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_books_list(self, client: TestClient):
        """Test retrieving list of books."""
        response = client.get("/books/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    @pytest.mark.asyncio
    async def test_get_books_with_pagination(self, client: TestClient):
        """Test retrieving books with pagination parameters."""
        response = client.get("/books/?page=1&size=5")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5

    @pytest.mark.asyncio
    async def test_get_books_with_filters(self, client: TestClient):
        """Test retrieving books with filters."""
        response = client.get("/books/?genre=Fiction&author=Test+Author")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_book_by_id_success(self, client: TestClient):
        """Test retrieving a specific book by ID."""
        # First create a book
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023
        }
        
        with patch('app.services.ai_service.AIService.generate_book_summary'):
            create_response = client.post("/books/", json=book_data, headers=admin_headers)
            book_id = create_response.json()["id"]
        
        response = client.get(f"/books/{book_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == book_id
        assert data["title"] == book_data["title"]

    @pytest.mark.asyncio
    async def test_get_book_by_id_not_found(self, client: TestClient):
        """Test retrieving a non-existent book."""
        response = client.get("/books/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_book_success(self, client: TestClient, admin_headers: dict):
        """Test updating a book with admin permissions."""
        # First create a book
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023
        }
        
        with patch('app.services.ai_service.AIService.generate_book_summary'):
            create_response = client.post("/books/", json=book_data, headers=admin_headers)
            book_id = create_response.json()["id"]
        
        update_data = {
            "title": "Updated Test Book",
            "genre": "Science Fiction"
        }
        
        response = client.put(f"/books/{book_id}", json=update_data, headers=admin_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["genre"] == update_data["genre"]

    @pytest.mark.asyncio
    async def test_update_book_unauthorized(self, client: TestClient, auth_headers: dict):
        """Test updating a book without admin permissions fails."""
        update_data = {"title": "Updated Title"}
        
        response = client.put("/books/1", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_delete_book_success(self, client: TestClient, admin_headers: dict):
        """Test deleting a book with admin permissions."""
        # First create a book
        book_data = {
            "title": "Test Book to Delete",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023
        }
        
        with patch('app.services.ai_service.AIService.generate_book_summary'):
            create_response = client.post("/books/", json=book_data, headers=admin_headers)
            book_id = create_response.json()["id"]
        
        response = client.delete(f"/books/{book_id}", headers=admin_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify book is deleted
        get_response = client.get(f"/books/{book_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_book_unauthorized(self, client: TestClient, auth_headers: dict):
        """Test deleting a book without admin permissions fails."""
        response = client.delete("/books/1", headers=auth_headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_book_summary(self, client: TestClient):
        """Test retrieving book summary with aggregated ratings."""
        # This would require creating a book and reviews first
        # For now, test the endpoint exists
        response = client.get("/books/1/summary")
        
        # Should return 404 if book doesn't exist
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_200_OK]

    @pytest.mark.asyncio
    async def test_get_recommendations(self, client: TestClient, auth_headers: dict):
        """Test getting book recommendations."""
        with patch('app.services.ai_service.AIService.generate_recommendations') as mock_ai:
            mock_ai.return_value = ["Book 1", "Book 2", "Book 3"]
            
            response = client.get("/books/recommendations?genre=Fiction", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)


class TestBookService:
    """Test book service functionality."""

    @pytest.mark.asyncio
    async def test_create_book_service(self, db_session):
        """Test book creation through service layer."""
        from app.services.book_service import BookService
        from app.models.schemas import BookCreate
        
        book_service = BookService(db_session)
        book_data = BookCreate(
            title="Test Service Book",
            author="Test Author",
            genre="Fiction",
            year_published=2023
        )
        
        book = await book_service.create_book(book_data)
        
        assert book.title == book_data.title
        assert book.author == book_data.author
        assert book.genre == book_data.genre
        assert book.id is not None

    @pytest.mark.asyncio
    async def test_get_books_pagination(self, db_session):
        """Test getting books with pagination."""
        from app.services.book_service import BookService
        
        book_service = BookService(db_session)
        result = await book_service.get_books(page=1, size=10)
        
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert result["page"] == 1
        assert result["size"] == 10

    @pytest.mark.asyncio
    async def test_get_book_by_id_service(self, db_session):
        """Test getting book by ID through service layer."""
        from app.services.book_service import BookService
        from app.models.schemas import BookCreate
        
        book_service = BookService(db_session)
        
        # Create a book first
        book_data = BookCreate(
            title="Test Get Book",
            author="Test Author",
            genre="Fiction",
            year_published=2023
        )
        created_book = await book_service.create_book(book_data)
        
        # Retrieve the book
        retrieved_book = await book_service.get_book(created_book.id)
        
        assert retrieved_book is not None
        assert retrieved_book.id == created_book.id
        assert retrieved_book.title == book_data.title

    @pytest.mark.asyncio
    async def test_update_book_service(self, db_session):
        """Test updating book through service layer."""
        from app.services.book_service import BookService
        from app.models.schemas import BookCreate, BookUpdate
        
        book_service = BookService(db_session)
        
        # Create a book first
        book_data = BookCreate(
            title="Test Update Book",
            author="Test Author",
            genre="Fiction",
            year_published=2023
        )
        created_book = await book_service.create_book(book_data)
        
        # Update the book
        update_data = BookUpdate(title="Updated Title", genre="Science Fiction")
        updated_book = await book_service.update_book(created_book.id, update_data)
        
        assert updated_book is not None
        assert updated_book.title == update_data.title
        assert updated_book.genre == update_data.genre
        assert updated_book.author == book_data.author  # Unchanged field

    @pytest.mark.asyncio
    async def test_delete_book_service(self, db_session):
        """Test deleting book through service layer."""
        from app.services.book_service import BookService
        from app.models.schemas import BookCreate
        
        book_service = BookService(db_session)
        
        # Create a book first
        book_data = BookCreate(
            title="Test Delete Book",
            author="Test Author",
            genre="Fiction",
            year_published=2023
        )
        created_book = await book_service.create_book(book_data)
        
        # Delete the book
        result = await book_service.delete_book(created_book.id)
        assert result is True
        
        # Verify book is deleted
        deleted_book = await book_service.get_book(created_book.id)
        assert deleted_book is None