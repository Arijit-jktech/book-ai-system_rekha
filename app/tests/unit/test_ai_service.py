"""
Unit tests for AI service functionality.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient


class TestAIServiceEndpoints:
    """Test AI service endpoints."""

    @pytest.mark.asyncio
    async def test_generate_summary_success(self, client: TestClient, auth_headers: dict):
        """Test generating book summary with valid content."""
        with patch('app.services.ai_service.AIService.generate_book_summary') as mock_ai:
            mock_ai.return_value = MagicMock(summary="This is a generated summary of the book.")
            
            summary_data = {
                "title": "Test Book",
                "author": "Test Author",
                "content": "This is the full content of the book that needs to be summarized. It contains multiple chapters and detailed storylines."
            }
            
            response = client.post("/ai/generate-summary", json=summary_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "summary" in data
        assert data["summary"] == "This is a generated summary of the book."

    @pytest.mark.asyncio
    async def test_generate_summary_unauthorized(self, client: TestClient):
        """Test generating summary without authentication fails."""
        summary_data = {
            "title": "Test Book",
            "author": "Test Author",
            "content": "Book content"
        }
        
        response = client.post("/ai/generate-summary", json=summary_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_generate_summary_empty_content(self, client: TestClient, auth_headers: dict):
        """Test generating summary with empty content."""
        summary_data = {
            "title": "Test Book",
            "author": "Test Author",
            "content": ""
        }
        
        response = client.post("/ai/generate-summary", json=summary_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_generate_summary_missing_fields(self, client: TestClient, auth_headers: dict):
        """Test generating summary with missing required fields."""
        summary_data = {
            "title": "Test Book"
            # Missing author and content
        }
        
        response = client.post("/ai/generate-summary", json=summary_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_recommendations_success(self, client: TestClient, auth_headers: dict):
        """Test getting book recommendations."""
        with patch('app.services.ai_service.AIService.generate_recommendations') as mock_ai:
            mock_ai.return_value = [
                "The Great Gatsby",
                "To Kill a Mockingbird", 
                "1984"
            ]
            
            response = client.get("/ai/recommendations?genre=Fiction&limit=3", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) == 3
        assert "The Great Gatsby" in data["recommendations"]

    @pytest.mark.asyncio
    async def test_get_recommendations_unauthorized(self, client: TestClient):
        """Test getting recommendations without authentication."""
        response = client.get("/ai/recommendations?genre=Fiction")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_recommendations_with_user_preferences(self, client: TestClient, auth_headers: dict):
        """Test getting personalized recommendations based on user preferences."""
        with patch('app.services.ai_service.AIService.generate_recommendations') as mock_ai:
            mock_ai.return_value = [
                "Personalized Book 1",
                "Personalized Book 2"
            ]
            
            response = client.get("/ai/recommendations?personalized=true", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    @pytest.mark.asyncio
    async def test_analyze_review_sentiment(self, client: TestClient, auth_headers: dict):
        """Test analyzing sentiment of reviews."""
        with patch('app.services.ai_service.AIService.analyze_sentiment') as mock_ai:
            mock_ai.return_value = {
                "sentiment": "positive",
                "confidence": 0.85,
                "emotions": ["joy", "satisfaction"]
            }
            
            sentiment_data = {
                "text": "This book is absolutely amazing! I loved every page of it."
            }
            
            response = client.post("/ai/analyze-sentiment", json=sentiment_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sentiment" in data
        assert data["sentiment"] == "positive"
        assert data["confidence"] == 0.85


class TestAIService:
    """Test AI service functionality."""

    @pytest.mark.asyncio
    async def test_generate_book_summary(self):
        """Test book summary generation."""
        from app.services.ai_service import AIService
        
        ai_service = AIService()
        
        # Mock the HTTP client
        with patch.object(ai_service, '_make_ai_request') as mock_request:
            mock_request.return_value = {
                "summary": "This is a test summary generated by AI."
            }
            
            result = await ai_service.generate_book_summary(
                title="Test Book",
                author="Test Author",
                content="This is the book content to summarize."
            )
            
            assert hasattr(result, 'summary')
            assert result.summary == "This is a test summary generated by AI."

    @pytest.mark.asyncio
    async def test_generate_recommendations(self):
        """Test book recommendation generation."""
        from app.services.ai_service import AIService
        
        ai_service = AIService()
        
        with patch.object(ai_service, '_make_ai_request') as mock_request:
            mock_request.return_value = {
                "recommendations": ["Book 1", "Book 2", "Book 3"]
            }
            
            result = await ai_service.generate_recommendations(
                user_preferences={"genre": "Fiction", "author": "Test Author"},
                limit=3
            )
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert "Book 1" in result

    @pytest.mark.asyncio
    async def test_analyze_sentiment(self):
        """Test sentiment analysis of text."""
        from app.services.ai_service import AIService
        
        ai_service = AIService()
        
        with patch.object(ai_service, '_make_ai_request') as mock_request:
            mock_request.return_value = {
                "sentiment": "positive",
                "confidence": 0.9,
                "emotions": ["happiness", "satisfaction"]
            }
            
            result = await ai_service.analyze_sentiment(
                "This book is fantastic! I really enjoyed it."
            )
            
            assert result["sentiment"] == "positive"
            assert result["confidence"] == 0.9
            assert "happiness" in result["emotions"]

    @pytest.mark.asyncio
    async def test_ai_service_error_handling(self):
        """Test AI service error handling."""
        from app.services.ai_service import AIService
        import httpx
        
        ai_service = AIService()
        
        with patch.object(ai_service, '_make_ai_request') as mock_request:
            mock_request.side_effect = httpx.HTTPError("API Error")
            
            with pytest.raises(Exception):
                await ai_service.generate_book_summary(
                    title="Test",
                    author="Test",
                    content="Test content"
                )

    @pytest.mark.asyncio
    async def test_ai_service_timeout_handling(self):
        """Test AI service timeout handling."""
        from app.services.ai_service import AIService
        import httpx
        
        ai_service = AIService()
        
        with patch.object(ai_service, '_make_ai_request') as mock_request:
            mock_request.side_effect = httpx.TimeoutException("Request timed out")
            
            with pytest.raises(Exception):
                await ai_service.generate_book_summary(
                    title="Test",
                    author="Test", 
                    content="Test content"
                )

    def test_ai_service_configuration(self):
        """Test AI service configuration."""
        from app.services.ai_service import AIService
        
        ai_service = AIService()
        
        assert hasattr(ai_service, 'base_url')
        assert hasattr(ai_service, 'api_key')
        assert hasattr(ai_service, 'timeout')

    @pytest.mark.asyncio
    async def test_generate_summary_with_long_content(self):
        """Test summary generation with very long content."""
        from app.services.ai_service import AIService
        
        ai_service = AIService()
        
        long_content = "This is a very long book content. " * 1000  # Simulate long content
        
        with patch.object(ai_service, '_make_ai_request') as mock_request:
            mock_request.return_value = {
                "summary": "Summary of long content"
            }
            
            result = await ai_service.generate_book_summary(
                title="Long Book",
                author="Author",
                content=long_content
            )
            
            assert result.summary == "Summary of long content"

    @pytest.mark.asyncio
    async def test_generate_recommendations_with_filters(self):
        """Test recommendation generation with various filters."""
        from app.services.ai_service import AIService
        
        ai_service = AIService()
        
        with patch.object(ai_service, '_make_ai_request') as mock_request:
            mock_request.return_value = {
                "recommendations": ["Filtered Book 1", "Filtered Book 2"]
            }
            
            preferences = {
                "genre": "Science Fiction",
                "year_range": [2000, 2023],
                "min_rating": 4.0,
                "author_preferences": ["Isaac Asimov", "Philip K. Dick"]
            }
            
            result = await ai_service.generate_recommendations(
                user_preferences=preferences,
                limit=2
            )
            
            assert len(result) == 2
            assert "Filtered Book 1" in result


class TestAIServiceIntegration:
    """Test AI service integration scenarios."""

    @pytest.mark.asyncio
    async def test_book_creation_with_ai_summary(self, client: TestClient, admin_headers: dict):
        """Test creating a book with automatic AI summary generation."""
        book_data = {
            "title": "AI Test Book",
            "author": "AI Test Author",
            "genre": "Fiction",
            "year_published": 2023,
            "content": "This is a comprehensive book content that should trigger AI summary generation."
        }
        
        with patch('app.services.ai_service.AIService.generate_book_summary') as mock_ai:
            mock_ai.return_value = MagicMock(summary="AI generated summary")
            
            response = client.post("/books/", json=book_data, headers=admin_headers)
            
            assert response.status_code == status.HTTP_201_CREATED
            # Verify AI service was called
            mock_ai.assert_called_once()

    @pytest.mark.asyncio
    async def test_recommendation_based_on_user_history(self, client: TestClient, auth_headers: dict):
        """Test getting recommendations based on user's reading history."""
        with patch('app.services.ai_service.AIService.generate_recommendations') as mock_ai:
            mock_ai.return_value = ["Historical Book 1", "Historical Book 2"]
            
            response = client.get("/ai/recommendations?based_on_history=true", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "recommendations" in data