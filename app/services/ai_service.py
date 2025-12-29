"""
AI service for integrating with Llama3 model (OpenRouter/Ollama).
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
import json
from datetime import datetime
from urllib.parse import urljoin

from app.core.config import get_settings
from app.models.models import Book
from app.models.schemas import GenerateSummaryResponse, RecommendationResponse

settings = get_settings()
logger = logging.getLogger(__name__)


class AIService:
    """Service for AI model interactions using Llama3."""
    
    def __init__(self):
        self.base_url = settings.ai_service_url
        self.api_key = settings.ai_api_key
        self.model_name = settings.ai_model_name
        self.provider = (settings.ai_provider or "auto").lower()
        self.timeout = float(settings.ai_timeout)
        self.default_max_tokens = int(getattr(settings, "ai_max_tokens", 1024))
        self.temperature = float(getattr(settings, "ai_temperature", 0.7))
        self.top_p = float(getattr(settings, "ai_top_p", 0.9))

        if self.provider == "auto":
            # Heuristic: Ollama defaults to :11434 and uses /api/chat.
            if "11434" in self.base_url or "ollama" in self.base_url.lower():
                self.provider = "ollama"
            else:
                self.provider = "openai_compat"

        logger.info(
            "AIService initialized",
            extra={
                "model": self.model_name,
                "base_url": self.base_url,
                "provider": self.provider,
                "timeout": self.timeout,
            },
        )

    def _url(self, path: str) -> str:
        base = self.base_url.rstrip("/") + "/"
        return urljoin(base, path.lstrip("/"))
    
    async def _make_request(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """Make a request to the configured AI provider."""
        max_tokens = int(max_tokens or self.default_max_tokens)

        timeout = httpx.Timeout(self.timeout)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if self.provider == "ollama":
                    payload = {
                        "model": self.model_name,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": self.temperature,
                            "top_p": self.top_p,
                        },
                    }
                    response = await client.post(
                        self._url("/api/chat"),
                        headers={"Content-Type": "application/json"},
                        json=payload,
                    )
                    response.raise_for_status()
                    result = response.json()
                    content = ((result or {}).get("message") or {}).get("content")
                    if not content:
                        raise ValueError("No response from AI model")
                    return str(content).strip()

                # OpenAI-compatible chat completions
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                # Keep OpenRouter headers if a key is provided (harmless elsewhere)
                headers.setdefault("HTTP-Referer", "http://localhost:8000")
                headers.setdefault("X-Title", settings.app_name)

                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                }
                response = await client.post(
                    self._url("/chat/completions"),
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
                choices = (result or {}).get("choices") or []
                if not choices:
                    raise ValueError("No response from AI model")
                return str(((choices[0] or {}).get("message") or {}).get("content") or "").strip()

            except httpx.TimeoutException as e:
                raise Exception("AI model request timed out") from e
            except httpx.HTTPStatusError as e:
                raise Exception(f"AI model API error: {e.response.status_code} - {e.response.text}") from e
            except Exception as e:
                raise Exception(f"AI model request failed: {str(e)}") from e

    async def _make_ai_request(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> Any:
        """Compatibility wrapper expected by tests to return structured dicts.

        Tries to interpret the model response as JSON. If it's plain text,
        returns a dict with an appropriate key (e.g., 'summary').
        """
        response_text = await self._make_request(messages, max_tokens=max_tokens)
        # Attempt to parse JSON (direct or embedded in a fenced code block)
        try:
            return json.loads(response_text)
        except Exception:
            pass

        if "```" in response_text:
            # Try to extract a JSON code block
            parts = response_text.split("```")
            for i in range(len(parts) - 1):
                candidate = parts[i + 1].strip()
                if candidate.lower().startswith("json"):
                    candidate = candidate[4:].strip()
                try:
                    return json.loads(candidate)
                except Exception:
                    continue

        # Try to extract first JSON object/array substring
        first_obj = response_text.find("{")
        last_obj = response_text.rfind("}")
        first_arr = response_text.find("[")
        last_arr = response_text.rfind("]")
        candidates: List[str] = []
        if first_obj != -1 and last_obj != -1 and last_obj > first_obj:
            candidates.append(response_text[first_obj : last_obj + 1])
        if first_arr != -1 and last_arr != -1 and last_arr > first_arr:
            candidates.append(response_text[first_arr : last_arr + 1])
        for c in candidates:
            try:
                return json.loads(c)
            except Exception:
                continue

        # Fallback: return a summary-like dict
        return {"summary": response_text}
    
    async def generate_book_summary(
        self, 
        title: str, 
        author: str, 
        content: str, 
        max_length: int = 500
    ) -> GenerateSummaryResponse:
        """Generate a summary for a book based on its content."""
        if len(content) < 10:
            raise ValueError("Content too short to generate meaningful summary")
        
        # Truncate content if too long to avoid token limits
        max_content_length = 3000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional book critic and summarizer. Create concise, "
                    "engaging summaries that capture the essence, themes, and key elements "
                    "of books. Focus on plot, characters, writing style, and overall impact."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Please create a {max_length}-word summary for the book '{title}' "
                    f"by {author}. Here's the content:\\n\\n{content}\\n\\n"
                    f"Summary should be engaging, informative, and suitable for potential readers."
                )
            }
        ]
        
        # Use the compatibility wrapper so tests can patch it
        result = await self._make_ai_request(messages, max_tokens=max_length + 100)
        summary = result.get("summary") if isinstance(result, dict) else str(result)
        
        return GenerateSummaryResponse(
            summary=summary,
            generated_at=datetime.utcnow()
        )
    
    async def generate_review_summary(
        self, 
        book_title: str, 
        reviews: List[str], 
        ratings: List[float]
    ) -> str:
        """Generate a summary of reviews for a book."""
        if not reviews:
            return "No reviews available for this book."
        
        # Combine reviews with ratings
        review_data = []
        for review, rating in zip(reviews, ratings):
            review_data.append(f"Rating: {rating}/5 - {review}")
        
        # Truncate if too many reviews
        if len(review_data) > 10:
            review_data = review_data[:10]
            review_text = "\\n\\n".join(review_data) + "\\n\\n[Additional reviews omitted...]"
        else:
            review_text = "\\n\\n".join(review_data)
        
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional book review analyst. Analyze multiple reviews "
                    "to create a comprehensive summary that highlights common themes, "
                    "strengths, weaknesses, and overall reader sentiment."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Analyze these reviews for '{book_title}' (Average rating: {avg_rating:.1f}/5):\\n\\n"
                    f"{review_text}\\n\\n"
                    "Create a balanced summary highlighting key points readers mention, "
                    "both positive and negative aspects, and overall consensus."
                )
            }
        ]
        
        # Return plain text summary of reviews
        result = await self._make_ai_request(messages, max_tokens=600)
        if isinstance(result, dict) and "summary" in result:
            return str(result["summary"])
        return str(result)
    
    async def generate_recommendations(
        self,
        user_preferences: Dict[str, Any],
        available_books: Optional[List[Book]] = None,
        max_recommendations: int = 10,
        limit: Optional[int] = None,
    ) -> Any:
        """Generate book recommendations.

        - If `available_books` is provided, returns a RecommendationResponse matching books.
        - If not, returns a simple list of recommended titles (for unit tests compatibility).
        """
        if limit is not None:
            max_recommendations = limit
        if not available_books:
            # No catalog provided: ask the model for simple title list
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert librarian and recommendation engine. "
                        "Return an array of book titles as JSON under 'recommendations'."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Preferences: {json.dumps(user_preferences)}. "
                        f"Recommend up to {max_recommendations} books."
                    ),
                },
            ]
            result = await self._make_ai_request(messages, max_tokens=200)
            # Expect dict with 'recommendations' or fallback to list parsing
            if isinstance(result, dict) and "recommendations" in result:
                recs = result["recommendations"]
                return list(recs) if isinstance(recs, list) else [str(recs)]
            # Fallback: split lines into list
            text = str(result)
            recs = [line.strip("- ") for line in text.split("\n") if line.strip()]
            return recs[:max_recommendations]
        
        # Prepare book data for the AI model
        book_descriptions = []
        for book in available_books[:50]:  # Limit to avoid token limits
            desc = f"- '{book.title}' by {book.author} ({book.year_published}) - Genre: {book.genre}"
            if book.summary:
                desc += f" | Summary: {book.summary[:200]}..."
            book_descriptions.append(desc)
        
        book_list = "\\n".join(book_descriptions)
        
        # Format user preferences
        pref_text = []
        if user_preferences.get("genres"):
            pref_text.append(f"Preferred genres: {', '.join(user_preferences['genres'])}")
        if user_preferences.get("authors"):
            pref_text.append(f"Liked authors: {', '.join(user_preferences['authors'])}")
        if user_preferences.get("min_rating"):
            pref_text.append(f"Minimum rating: {user_preferences['min_rating']}/5")
        
        preferences_str = "; ".join(pref_text) if pref_text else "Open to all genres and authors"
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert librarian and book recommendation engine. "
                    "Analyze user preferences and available books to provide personalized "
                    "recommendations with clear reasoning."
                )
            },
            {
                "role": "user",
                "content": (
                    f"User preferences: {preferences_str}\\n\\n"
                    f"Available books:\\n{book_list}\\n\\n"
                    f"Please recommend up to {max_recommendations} books that best match "
                    f"the user's preferences. For each recommendation, provide the exact "
                    f"book title and author as listed above, and explain why it's recommended. "
                    f"Format as:\\n"
                    f"1. 'Book Title' by Author - Reason\\n"
                    f"2. 'Another Book' by Author - Reason\\n"
                    f"etc."
                )
            }
        ]
        
        recommendation_text = await self._make_request(messages, max_tokens=800)
        
        # Parse recommendations to match with actual books
        recommended_books = self._parse_recommendations(recommendation_text, available_books)
        
        return RecommendationResponse(
            books=recommended_books[:max_recommendations],
            total_results=len(recommended_books),
            recommendation_reason=recommendation_text,
        )
    
    def _parse_recommendations(self, recommendation_text: str, available_books: List[Book]) -> List[Book]:
        """Parse AI recommendation text and match with actual books."""
        recommended_books = []
        
        # Create a mapping of books by title and author for easier matching
        book_map = {}
        for book in available_books:
            # Create multiple keys for fuzzy matching
            keys = [
                f"{book.title.lower()} {book.author.lower()}",
                book.title.lower(),
                f"{book.author.lower()} {book.title.lower()}"
            ]
            for key in keys:
                book_map[key] = book
        
        # Split recommendation text into lines and try to find matches
        lines = recommendation_text.split('\\n')
        for line in lines:
            line = line.strip()
            if not line or not any(c.isalpha() for c in line):
                continue
            
            # Try to extract book title and author from various formats
            for book in available_books:
                title_lower = book.title.lower()
                author_lower = book.author.lower()
                line_lower = line.lower()
                
                # Check if both title and author are mentioned in the line
                if title_lower in line_lower and author_lower in line_lower:
                    if book not in recommended_books:
                        recommended_books.append(book)
                        break
                # Check if just the title is mentioned and it's unique enough
                elif title_lower in line_lower and len(book.title) > 5:
                    if book not in recommended_books:
                        recommended_books.append(book)
                        break
        
        return recommended_books
    
    async def analyze_book_content(self, title: str, author: str, content: str) -> Dict[str, Any]:
        """Analyze book content for themes, genre classification, and insights."""
        if len(content) < 100:
            raise ValueError("Content too short for meaningful analysis")
        
        # Truncate content if too long
        max_content_length = 2000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a literary analyst. Analyze books for themes, writing style, "
                    "genre, target audience, and key insights. Provide structured analysis."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Analyze '{title}' by {author}:\\n\\n{content}\\n\\n"
                    "Provide analysis in this format:\\n"
                    "Themes: [list main themes]\\n"
                    "Genre: [specific genre classification]\\n"
                    "Writing Style: [description]\\n"
                    "Target Audience: [description]\\n"
                    "Key Insights: [notable elements]"
                )
            }
        ]
        
        analysis = await self._make_request(messages, max_tokens=700)
        
        # Parse the analysis into structured data
        return {
            "raw_analysis": analysis,
            "analyzed_at": datetime.utcnow()
        }

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of a given text and return structured result.

        Returns a dict with keys: 'sentiment', 'confidence', 'emotions'.
        """
        if not text or len(text.strip()) < 3:
            raise ValueError("Text too short for sentiment analysis")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a sentiment analysis model. "
                    "Respond strictly as JSON with keys 'sentiment', 'confidence', 'emotions'."
                ),
            },
            {
                "role": "user",
                "content": f"Analyze the sentiment of this review: {text}",
            },
        ]
        result = await self._make_ai_request(messages, max_tokens=200)
        if isinstance(result, dict):
            return result
        # Fallback if model returned plain text
        return {"sentiment": "neutral", "confidence": 0.5, "emotions": []}