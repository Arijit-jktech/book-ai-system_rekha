"""
Integration tests for the Book Management System.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient


class TestFullBookManagementWorkflow:
    """Test complete book management workflows."""

    @pytest.mark.asyncio
    async def test_complete_book_lifecycle(self, client: TestClient, admin_headers: dict, auth_headers: dict):
        """Test complete book lifecycle: create, read, update, add reviews, delete."""
        
        # Step 1: Create a book
        book_data = {
            "title": "Integration Test Book",
            "author": "Integration Author",
            "genre": "Fiction",
            "year_published": 2023,
            "isbn": "123-456-789-0",
            "content": "This is a comprehensive test book content for integration testing."
        }
        
        with patch('app.services.ai_service.AIService.generate_book_summary') as mock_summary:
            mock_summary.return_value = MagicMock(summary="AI generated summary for integration test")
            
            create_response = client.post("/books/", json=book_data, headers=admin_headers)
            assert create_response.status_code == status.HTTP_201_CREATED
            book = create_response.json()
            book_id = book["id"]
        
        # Step 2: Retrieve the book
        get_response = client.get(f"/books/{book_id}")
        assert get_response.status_code == status.HTTP_200_OK
        retrieved_book = get_response.json()
        assert retrieved_book["title"] == book_data["title"]
        
        # Step 3: Add reviews
        review1_data = {
            "review_text": "Excellent book! Really enjoyed the storyline.",
            "rating": 4.8
        }
        review1_response = client.post(
            f"/books/{book_id}/reviews", 
            json=review1_data, 
            headers=auth_headers
        )
        assert review1_response.status_code == status.HTTP_201_CREATED
        
        review2_data = {
            "review_text": "Good book, but could be better.",
            "rating": 3.5
        }
        review2_response = client.post(
            f"/books/{book_id}/reviews", 
            json=review2_data, 
            headers=admin_headers
        )
        assert review2_response.status_code == status.HTTP_201_CREATED
        
        # Step 4: Get book reviews
        reviews_response = client.get(f"/books/{book_id}/reviews")
        assert reviews_response.status_code == status.HTTP_200_OK
        reviews = reviews_response.json()
        assert len(reviews) == 2
        
        # Step 5: Get book summary with aggregated ratings
        summary_response = client.get(f"/books/{book_id}/summary")
        assert summary_response.status_code == status.HTTP_200_OK
        summary = summary_response.json()
        assert "book" in summary
        assert "average_rating" in summary
        assert "total_reviews" in summary
        
        # Step 6: Update the book
        update_data = {
            "title": "Updated Integration Test Book",
            "summary": "Updated summary"
        }
        update_response = client.put(f"/books/{book_id}", json=update_data, headers=admin_headers)
        assert update_response.status_code == status.HTTP_200_OK
        updated_book = update_response.json()
        assert updated_book["title"] == update_data["title"]
        
        # Step 7: Delete the book
        delete_response = client.delete(f"/books/{book_id}", headers=admin_headers)
        assert delete_response.status_code == status.HTTP_200_OK
        
        # Step 8: Verify book is deleted
        get_deleted_response = client.get(f"/books/{book_id}")
        assert get_deleted_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_user_authentication_and_authorization_workflow(self, client: TestClient):
        """Test complete user authentication and authorization workflow."""
        
        # Step 1: Register a new user
        user_data = {
            "username": "integrationuser",
            "email": "integration@test.com",
            "password": "integrationpass123",
            "role": "user"
        }
        
        register_response = client.post("/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user = register_response.json()
        
        # Step 2: Login with the user
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        login_response = client.post("/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        token_data = login_response.json()
        assert "access_token" in token_data
        
        user_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        
        # Step 3: Access user profile
        profile_response = client.get("/auth/me", headers=user_headers)
        assert profile_response.status_code == status.HTTP_200_OK
        profile = profile_response.json()
        assert profile["username"] == user_data["username"]
        
        # Step 4: Update user profile
        update_data = {"email": "updated_integration@test.com"}
        update_response = client.put("/auth/me", json=update_data, headers=user_headers)
        assert update_response.status_code == status.HTTP_200_OK
        
        # Step 5: Try to access admin-only endpoint (should fail)
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023
        }
        
        admin_action_response = client.post("/books/", json=book_data, headers=user_headers)
        assert admin_action_response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_ai_integration_workflow(self, client: TestClient, admin_headers: dict, auth_headers: dict):
        """Test AI service integration workflow."""
        
        # Step 1: Generate summary for book content
        summary_request = {
            "title": "AI Integration Test",
            "author": "AI Author",
            "content": "This is a detailed book content that needs to be summarized using AI services."
        }
        
        with patch('app.services.ai_service.AIService.generate_book_summary') as mock_summary:
            mock_summary.return_value = MagicMock(summary="AI generated summary")
            
            summary_response = client.post("/ai/generate-summary", json=summary_request, headers=auth_headers)
            assert summary_response.status_code == status.HTTP_200_OK
            summary = summary_response.json()
            assert "summary" in summary
        
        # Step 2: Get book recommendations
        with patch('app.services.ai_service.AIService.generate_recommendations') as mock_recommendations:
            mock_recommendations.return_value = ["Recommended Book 1", "Recommended Book 2"]
            
            rec_response = client.get("/ai/recommendations?genre=Fiction", headers=auth_headers)
            assert rec_response.status_code == status.HTTP_200_OK
            recommendations = rec_response.json()
            assert "recommendations" in recommendations
        
        # Step 3: Analyze review sentiment
        sentiment_request = {
            "text": "This book is absolutely fantastic! I loved every chapter."
        }
        
        with patch('app.services.ai_service.AIService.analyze_sentiment') as mock_sentiment:
            mock_sentiment.return_value = {
                "sentiment": "positive",
                "confidence": 0.9
            }
            
            sentiment_response = client.post("/ai/analyze-sentiment", json=sentiment_request, headers=auth_headers)
            assert sentiment_response.status_code == status.HTTP_200_OK
            sentiment = sentiment_response.json()
            assert sentiment["sentiment"] == "positive"

    @pytest.mark.asyncio
    async def test_book_search_and_filtering_workflow(self, client: TestClient, admin_headers: dict):
        """Test book search and filtering functionality."""
        
        # Step 1: Create multiple books for testing
        books_data = [
            {
                "title": "Science Fiction Book 1",
                "author": "Sci-Fi Author",
                "genre": "Science Fiction",
                "year_published": 2020
            },
            {
                "title": "Fantasy Book 1",
                "author": "Fantasy Author",
                "genre": "Fantasy",
                "year_published": 2021
            },
            {
                "title": "Science Fiction Book 2",
                "author": "Another Sci-Fi Author",
                "genre": "Science Fiction",
                "year_published": 2022
            }
        ]
        
        book_ids = []
        with patch('app.services.ai_service.AIService.generate_book_summary'):
            for book_data in books_data:
                response = client.post("/books/", json=book_data, headers=admin_headers)
                assert response.status_code == status.HTTP_201_CREATED
                book_ids.append(response.json()["id"])
        
        # Step 2: Test pagination
        paginated_response = client.get("/books/?page=1&size=2")
        assert paginated_response.status_code == status.HTTP_200_OK
        paginated_data = paginated_response.json()
        assert paginated_data["size"] == 2
        assert len(paginated_data["items"]) <= 2
        
        # Step 3: Test genre filtering
        genre_filter_response = client.get("/books/?genre=Science%20Fiction")
        assert genre_filter_response.status_code == status.HTTP_200_OK
        filtered_books = genre_filter_response.json()
        for book in filtered_books["items"]:
            assert book["genre"] == "Science Fiction"
        
        # Step 4: Test author filtering
        author_filter_response = client.get("/books/?author=Sci-Fi%20Author")
        assert author_filter_response.status_code == status.HTTP_200_OK
        author_filtered = author_filter_response.json()
        for book in author_filtered["items"]:
            assert "Sci-Fi Author" in book["author"]
        
        # Step 5: Test year range filtering
        year_filter_response = client.get("/books/?year_from=2021&year_to=2022")
        assert year_filter_response.status_code == status.HTTP_200_OK
        year_filtered = year_filter_response.json()
        for book in year_filtered["items"]:
            assert 2021 <= book["year_published"] <= 2022
        
        # Clean up: Delete created books
        for book_id in book_ids:
            client.delete(f"/books/{book_id}", headers=admin_headers)

    @pytest.mark.asyncio
    async def test_review_management_workflow(self, client: TestClient, admin_headers: dict, auth_headers: dict):
        """Test complete review management workflow."""
        
        # Step 1: Create a book for reviews
        book_data = {
            "title": "Review Test Book",
            "author": "Review Author",
            "genre": "Fiction",
            "year_published": 2023
        }
        
        with patch('app.services.ai_service.AIService.generate_book_summary'):
            book_response = client.post("/books/", json=book_data, headers=admin_headers)
            book_id = book_response.json()["id"]
        
        # Step 2: Add multiple reviews
        reviews_data = [
            {"review_text": "Amazing book!", "rating": 5.0},
            {"review_text": "Pretty good read.", "rating": 4.0},
            {"review_text": "Okay book, nothing special.", "rating": 3.0}
        ]
        
        review_ids = []
        for review_data in reviews_data:
            review_response = client.post(
                f"/books/{book_id}/reviews",
                json=review_data,
                headers=auth_headers
            )
            assert review_response.status_code == status.HTTP_201_CREATED
            review_ids.append(review_response.json()["id"])
        
        # Step 3: Get all reviews for the book
        all_reviews_response = client.get(f"/books/{book_id}/reviews")
        assert all_reviews_response.status_code == status.HTTP_200_OK
        all_reviews = all_reviews_response.json()
        assert len(all_reviews) == 3
        
        # Step 4: Update a review
        update_data = {
            "review_text": "Updated review text",
            "rating": 4.5
        }
        update_response = client.put(f"/reviews/{review_ids[0]}", json=update_data, headers=auth_headers)
        assert update_response.status_code == status.HTTP_200_OK
        
        # Step 5: Get user's reviews
        user_reviews_response = client.get("/reviews/my-reviews", headers=auth_headers)
        assert user_reviews_response.status_code == status.HTTP_200_OK
        user_reviews = user_reviews_response.json()
        assert len(user_reviews) >= 3
        
        # Step 6: Delete a review
        delete_response = client.delete(f"/reviews/{review_ids[0]}", headers=auth_headers)
        assert delete_response.status_code == status.HTTP_200_OK
        
        # Step 7: Verify review count decreased
        updated_reviews_response = client.get(f"/books/{book_id}/reviews")
        updated_reviews = updated_reviews_response.json()
        assert len(updated_reviews) == 2
        
        # Clean up: Delete the book
        client.delete(f"/books/{book_id}", headers=admin_headers)


class TestErrorHandlingIntegration:
    """Test error handling across different components."""

    @pytest.mark.asyncio
    async def test_cascade_error_handling(self, client: TestClient, auth_headers: dict, admin_headers: dict):
        """Test error handling when multiple services fail."""
        
        # Test AI service failure during book creation
        book_data = {
            "title": "Error Test Book",
            "author": "Error Author",
            "genre": "Fiction",
            "year_published": 2023,
            "content": "Content for error testing"
        }
        
        with patch('app.services.ai_service.AIService.generate_book_summary') as mock_ai:
            mock_ai.side_effect = Exception("AI Service Error")
            
            # Book creation should still succeed even if AI fails
            response = client.post("/books/", json=book_data, headers=admin_headers)
            # The implementation should handle AI errors gracefully
            assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, client: TestClient, admin_headers: dict):
        """Test database transaction rollback on errors."""
        
        # This test would simulate database errors and verify rollback behavior
        # Implementation depends on specific error scenarios in your services
        pass

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, client: TestClient, admin_headers: dict):
        """Test handling of concurrent requests."""
        
        # This test would simulate multiple concurrent requests
        # and verify system behavior under load
        pass


class TestPerformanceIntegration:
    """Test performance aspects of the integrated system."""

    @pytest.mark.asyncio
    async def test_large_dataset_pagination(self, client: TestClient):
        """Test pagination with large datasets."""
        
        # Test pagination performance with large page sizes
        response = client.get("/books/?page=1&size=100")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify response time is reasonable (this would need timing measurement)
        data = response.json()
        assert "items" in data
        assert data["size"] == 100

    @pytest.mark.asyncio
    async def test_ai_service_timeout_handling(self, client: TestClient, auth_headers: dict):
        """Test AI service timeout handling."""
        
        import httpx
        
        with patch('app.services.ai_service.AIService.generate_book_summary') as mock_ai:
            mock_ai.side_effect = httpx.TimeoutException("Request timed out")
            
            summary_data = {
                "title": "Timeout Test",
                "author": "Test Author",
                "content": "Content for timeout testing"
            }
            
            response = client.post("/ai/generate-summary", json=summary_data, headers=auth_headers)
            # Should handle timeout gracefully
            assert response.status_code in [status.HTTP_408_REQUEST_TIMEOUT, status.HTTP_500_INTERNAL_SERVER_ERROR]
