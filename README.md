# Intelligent Book Management System

A modern, scalable book management system built with FastAPI, PostgreSQL, and AI-powered features using Llama3 for intelligent book summaries and recommendations.

## 🚀 Features

- **Complete CRUD Operations**: Add, retrieve, update, and delete books
- **AI-Powered Summaries**: Automatic book summary generation using Llama3
- **Intelligent Recommendations**: Personalized book recommendations based on user preferences
- **Review System**: User reviews and ratings with aggregated statistics
- **Authentication & Authorization**: JWT-based auth with role-based access control
- **Async Operations**: High-performance async database and AI operations
- **RESTful API**: Well-structured REST API with comprehensive documentation
- **Docker Support**: Production-ready containerization
- **Comprehensive Testing**: Unit and integration tests with high coverage
- **Cloud-Ready**: Designed for easy deployment to cloud platforms

## 🏗️ Architecture

```
intelligent-book-management/
├── app/
│   ├── api/          # API endpoints
│   ├── auth/         # Authentication logic
│   ├── core/         # Configuration and settings
│   ├── database/     # Database session and connection
│   ├── models/       # SQLAlchemy models and Pydantic schemas
│   └── services/     # Business logic layer
├── tests/
│   ├── unit/         # Unit tests
│   └── integration/  # Integration tests
├── Dockerfile        # Container definition
├── docker-compose.yml # Multi-service orchestration
└── main.py          # Application entry point
```

## 📋 Prerequisites

- **Python 3.11+**
- **PostgreSQL 12+**
- **Docker & Docker Compose** (for containerized deployment)
- **Git**

## 🛠️ Quick Start

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
```bash
git clone <your-repository-url>
cd intelligent-book-management
```

2. **Set up environment variables**
```bash
cp env.example .env
# Edit .env with your configuration
```

3. **Start all services**
```bash
# For development
docker-compose -f docker-compose.dev.yml up -d

# For production
docker-compose up -d
```

4. **Initialize the AI model**
```bash
# Pull the Llama3 model (first time setup)
docker exec book_management_ai ollama pull llama3
```

5. **Access the application**
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### Option 2: Local Development Setup

1. **Clone and setup**
```bash
git clone <your-repository-url>
cd intelligent-book-management
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup PostgreSQL database**
```sql
CREATE DATABASE book_management;
CREATE USER book_admin WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE book_management TO book_admin;
```

5. **Configure environment**
```bash
cp env.example .env
# Edit .env with your database credentials and settings
```

6. **Run database migrations**
```bash
# The app will automatically create tables on first run
python main.py
```

7. **Start the application**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/book_management

# JWT Security
SECRET_KEY=your-super-secret-key-min-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Service
AI_SERVICE_URL=http://localhost:11434
AI_MODEL_NAME=llama3

# Application
DEBUG=false
ENVIRONMENT=production
APP_NAME=Intelligent Book Management System
```

### AI Service Setup

The system supports multiple AI providers:

1. **Ollama (Local)**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Llama3 model
ollama pull llama3

# Start Ollama server
ollama serve
```

2. **Groq API**
```env
AI_SERVICE_URL=https://api.groq.com/openai/v1
AI_API_KEY=your-groq-api-key
AI_MODEL_NAME=llama3-8b-8192
```

3. **Hugging Face**
```env
AI_SERVICE_URL=https://api-inference.huggingface.co
AI_API_KEY=your-hf-api-key
AI_MODEL_NAME=meta-llama/Llama-2-7b-chat-hf
```

## 🧪 Testing

### Run All Tests
```bash
# Using pytest directly
pytest tests/ -v --cov=app --cov-report=html

# Using the test runner
python tests/run_tests.py all
```

### Run Specific Test Types
```bash
# Unit tests only
python tests/run_tests.py unit

# Integration tests only
python tests/run_tests.py integration
```

### Test Coverage
```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## 📚 API Documentation

### Authentication

1. **Register a new user**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword",
    "role": "user"
  }'
```

2. **Login**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=securepassword"
```

### Book Management

1. **Create a book** (Admin/Moderator only)
```bash
curl -X POST "http://localhost:8000/books/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Great Book",
    "author": "Famous Author",
    "genre": "Fiction",
    "year_published": 2023,
    "isbn": "978-0123456789",
    "content": "Full book content for AI summary generation..."
  }'
```

2. **Get all books**
```bash
curl -X GET "http://localhost:8000/books/?page=1&size=10&genre=Fiction"
```

3. **Get book by ID**
```bash
curl -X GET "http://localhost:8000/books/1"
```

### Reviews

1. **Add a review**
```bash
curl -X POST "http://localhost:8000/books/1/reviews" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "review_text": "Excellent book!",
    "rating": 4.5
  }'
```

2. **Get book reviews**
```bash
curl -X GET "http://localhost:8000/books/1/reviews"
```

### AI Services

1. **Generate book summary**
```bash
curl -X POST "http://localhost:8000/ai/generate-summary" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Book Title",
    "author": "Author Name",
    "content": "Full book content..."
  }'
```

2. **Get recommendations**
```bash
curl -X GET "http://localhost:8000/ai/recommendations?genre=Fiction&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🚀 Deployment

### Step-by-Step Deployment Guide

This section provides detailed, step-by-step instructions for deploying the Intelligent Book Management System in various environments.

#### Option 1: Docker Production Deployment (Recommended)

**Step 1: Prepare Your Environment**
```bash
# Ensure Docker and Docker Compose are installed
docker --version
docker-compose --version

# Clone the repository
git clone <your-repository-url>
cd intelligent-book-management
```

**Step 2: Configure Environment Variables**
```bash
# Copy the environment template
cp .env.example .env

# Edit the .env file with your production settings
nano .env  # or use your preferred editor

# Required variables:
# DATABASE_URL=postgresql+asyncpg://user:password@db:5432/book_management
# SECRET_KEY=your-32-character-or-longer-secret-key
# AI_SERVICE_URL=http://ai:11434
# AI_MODEL_NAME=llama3
```

**Step 3: Build and Start Services**
```bash
# Build all services
docker-compose build

# Start services in detached mode
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Step 4: Initialize Database**
```bash
# Wait for database to be ready (usually 30-60 seconds)
docker-compose logs db | tail -20

# Run database initialization (if needed)
docker-compose exec web python -c "from app.database.session import init_db; import asyncio; asyncio.run(init_db())"
```

**Step 5: Setup AI Model**
```bash
# Access the AI container
docker-compose exec ai bash

# Pull the Llama3 model (this may take several minutes)
ollama pull llama3

# Verify model is available
ollama list

# Exit the container
exit
```

**Step 6: Verify Deployment**
```bash
# Check application health
curl http://localhost:8000/health

# Check API documentation
curl http://localhost:8000/docs

# Test a simple endpoint
curl http://localhost:8000/books/
```

**Step 7: Configure Reverse Proxy (Optional)**
```bash
# If using nginx, ensure it's properly configured
docker-compose logs nginx

# Test nginx configuration
docker-compose exec nginx nginx -t
```

#### Option 2: Local Development Deployment

**Step 1: System Prerequisites**
```bash
# Install Python 3.11+
python --version

# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Install Ollama for AI
curl -fsSL https://ollama.ai/install.sh | sh
```

**Step 2: Database Setup**
```bash
# Create database and user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE book_management;
CREATE USER book_admin WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE book_management TO book_admin;
\q
```

**Step 3: Application Setup**
```bash
# Clone repository
git clone <your-repository-url>
cd intelligent-book-management

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Step 4: Environment Configuration**
```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your local settings
```

**Step 5: Initialize Database Schema**
```bash
# Run the application once to create tables
python main.py
# Or use Alembic if migrations are set up
alembic upgrade head
```

**Step 6: Start AI Service**
```bash
# In a separate terminal
ollama serve

# Pull the model
ollama pull llama3
```

**Step 7: Start Application**
```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Verify it's running
curl http://localhost:8000/health
```

#### Option 3: Cloud Deployment - AWS EC2

**Step 1: Launch EC2 Instance**
```bash
# Choose Ubuntu 22.04 LTS, t3.medium or larger
# Configure security groups (ports 22, 80, 443, 8000)
# Launch instance and connect via SSH
ssh -i your-key.pem ubuntu@your-instance-ip
```

**Step 2: Install Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install PostgreSQL client (optional)
sudo apt install postgresql-client -y
```

**Step 3: Deploy Application**
```bash
# Clone repository
git clone <your-repository-url>
cd intelligent-book-management

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Start services
sudo docker-compose up -d --build
```

**Step 4: Configure Domain and SSL**
```bash
# Install nginx
sudo apt install nginx -y

# Configure nginx as reverse proxy
sudo nano /etc/nginx/sites-available/book-management

# Add configuration:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/book-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Install certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

**Step 5: Setup Monitoring**
```bash
# Install monitoring tools
sudo apt install htop iotop -y

# Configure log rotation
sudo nano /etc/logrotate.d/book-management
```

#### Option 4: Cloud Deployment - Heroku

**Step 1: Prepare Application**
```bash
# Ensure Procfile exists
echo "web: uvicorn app.main:app --host=0.0.0.0 --port=$PORT" > Procfile

# Ensure requirements.txt is complete
pip freeze > requirements.txt
```

**Step 2: Create Heroku App**
```bash
# Install Heroku CLI
# Create app
heroku create your-book-management-app

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set AI_SERVICE_URL=https://api.groq.com/openai/v1
heroku config:set AI_API_KEY=your-groq-key
```

**Step 3: Deploy**
```bash
# Add heroku remote
git remote add heroku https://git.heroku.com/your-book-management-app.git

# Deploy
git push heroku main

# Run database migrations
heroku run python manage.py migrate
```

**Step 4: Verify Deployment**
```bash
# Check logs
heroku logs --tail

# Open app
heroku open
```

#### Option 5: Cloud Deployment - Digital Ocean

**Step 1: Create Droplet**
```bash
# Create Ubuntu droplet with Docker pre-installed
# SSH into droplet
ssh root@your-droplet-ip
```

**Step 2: Deploy Application**
```bash
# Clone repository
git clone <your-repository-url>
cd intelligent-book-management

# Configure environment
cp .env.example .env
nano .env

# Start services
docker-compose up -d --build
```

**Step 3: Configure Firewall**
```bash
# Configure UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

**Step 4: Setup Domain**
```bash
# Point domain to droplet IP
# Install nginx and configure SSL as in AWS steps
```

### Production Checklist

Before going live, ensure:

- [ ] Environment variables are set correctly
- [ ] Database is initialized and accessible
- [ ] AI model is downloaded and responding
- [ ] SSL certificates are installed
- [ ] Firewall is configured
- [ ] Monitoring is set up
- [ ] Backups are configured
- [ ] Health checks are passing
- [ ] API documentation is accessible

### Troubleshooting Common Deployment Issues

**Database Connection Issues:**
```bash
# Check database logs
docker-compose logs db

# Test connection
docker-compose exec web python -c "from app.database.session import get_db; next(get_db())"
```

**AI Service Issues:**
```bash
# Check AI service status
docker-compose logs ai

# Test AI connectivity
curl http://localhost:11434/api/tags
```

**Application Startup Issues:**
```bash
# Check application logs
docker-compose logs web

# Test application health
curl http://localhost:8000/health
```

**Performance Issues:**
```bash
# Monitor resource usage
docker stats

# Check nginx logs
docker-compose logs nginx
```

This deployment guide covers the most common scenarios. For specific cloud provider optimizations or advanced configurations, refer to the respective platform's documentation.

## 🔍 Monitoring & Logging

### Health Checks

The application provides several health check endpoints:

- `/health` - Basic application health
- `/health/db` - Database connectivity
- `/health/ai` - AI service connectivity

### Logging

Logs are structured and can be configured via environment variables:

```env
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Monitoring

For production monitoring, integrate with:
- **Prometheus** for metrics
- **Grafana** for dashboards
- **Sentry** for error tracking
- **New Relic** or **DataDog** for APM

## 🔐 Security Considerations

1. **JWT Tokens**: Use strong, random secret keys
2. **Password Hashing**: Bcrypt with configurable rounds
3. **Rate Limiting**: Implemented via Nginx
4. **CORS**: Properly configured for your domain
5. **SQL Injection**: Protected via SQLAlchemy ORM
6. **Security Headers**: Implemented in Nginx configuration

## 🧩 Extending the System

### Adding New AI Providers

1. Create a new AI service class inheriting from `BaseAIService`
2. Implement required methods: `generate_summary`, `generate_recommendations`
3. Update configuration to use new provider

### Adding New Features

1. Create new models in `app/models/`
2. Add corresponding schemas in `app/models/schemas.py`
3. Implement service layer in `app/services/`
4. Create API endpoints in `app/api/`
5. Add comprehensive tests

### Performance Optimization

1. **Database**: Add indexes, optimize queries
2. **Caching**: Implement Redis caching for frequent queries
3. **AI**: Use model caching and async processing
4. **API**: Implement response caching

## 🐛 Troubleshooting

### Common Issues

1. **Database connection issues**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# View database logs
docker-compose logs postgres
```

2. **AI service not responding**
```bash
# Check Ollama status
docker-compose ps ollama

# Pull model if missing
docker exec book_management_ai ollama pull llama3
```

3. **Permission errors**
```bash
# Ensure proper file permissions
chmod +x scripts/*
chown -R $USER:$USER .
```

### Performance Issues

1. **Database slow queries**
```sql
-- Enable query logging in PostgreSQL
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();
```

2. **AI service timeouts**
```env
# Increase timeout in .env
AI_SERVICE_TIMEOUT=300
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- SQLAlchemy for robust ORM capabilities
- Ollama for local AI model serving
- PostgreSQL for reliable data storage
- Docker for containerization support

## 📞 Support

For support and questions:

- Create an issue in the repository
- Check the documentation at `/docs`
- Review the test cases for usage examples

---

**Note**: This system is designed as a high-quality prototype demonstrating modern software architecture patterns, comprehensive testing, and cloud-ready deployment strategies.