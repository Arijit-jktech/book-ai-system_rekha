# AI Coding Agent Instructions for Book AI System

## Project Overview
This is a FastAPI-based book management system with PostgreSQL database, Llama3 AI integration for summaries and recommendations, JWT authentication, and async operations. The system provides RESTful APIs for book CRUD operations, reviews, and AI-powered features.

## Architecture
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy[asyncio] and asyncpg
- **AI Model**: Llama3 (local instance via Ollama/OpenRouter/HuggingFace/Groq)
- **Authentication**: JWT-based with role-based access control
- **Structure**: Modular design with separate packages for API, core, DB, models, schemas, services, and tests

## Key Components
- `APP/api/`: FastAPI routers and endpoints
- `APP/core/`: Configuration, dependencies, security (JWT, auth)
- `APP/db/`: Database models, session management, initialization
- `APP/models/`: Pydantic schemas for request/response validation
- `APP/schemas/`: Additional schema definitions if needed
- `APP/services/`: Business logic, AI integration, recommendation engine
- `APP/tests/`: Unit and integration tests

## Development Patterns
- Use async/await for all database operations and AI calls
- Implement dependency injection via FastAPI's Depends
- Structure endpoints with proper HTTP status codes and error handling
- Use Pydantic models for all data validation
- Separate business logic into service classes
- Implement comprehensive unit tests for all modules

## Database Schema
- **books**: id, title, author, genre, year_published, summary
- **reviews**: id, book_id (FK), user_id, review_text, rating
- Use Alembic for migrations (future enhancement)

## AI Integration Patterns
- Use OpenRouter or local Ollama for Llama3 access
- Implement summary generation for books and aggregated reviews
- Build recommendation system based on user preferences and ratings
- Cache recommendations if using AWS ElastiCache

## Authentication Flow
- JWT tokens for API access
- Role-based permissions (user, admin)
- Secure endpoints with dependency injection
- Hash passwords, validate tokens on each request

## Testing Strategy
- Unit tests for services, models, and utilities
- Integration tests for API endpoints
- Mock external AI services for testing
- Use pytest with async support

## Deployment
- Docker containerization with docker-compose
- Environment-based configuration
- Cloud-ready with AWS EC2/RDS or similar
- Include health checks and monitoring

## Code Quality Standards
- Type hints on all functions
- Docstrings for modules and complex functions
- Consistent naming: snake_case for variables/functions, PascalCase for classes
- Error handling with custom exceptions
- Logging for debugging and monitoring

## Common Commands
- `uvicorn APP.main:app --reload` - Run development server
- `pytest APP/tests/` - Run tests
- `alembic upgrade head` - Apply DB migrations (when implemented)

## File Examples
- Models: `APP/db/models.py` with SQLAlchemy declarative base
- Schemas: `APP/models/schemas.py` with Pydantic BaseModel subclasses
- Services: `APP/services/book_service.py` with async methods
- API: `APP/api/books.py` with FastAPI router and endpoints