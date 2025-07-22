# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SuperRAG (Agorix) is a modern intelligent dialogue and knowledge sharing platform built with Flask. It combines AI conversation capabilities, knowledge base management, and community features. The system integrates with DeepSeek-V3 API for AI responses and uses LangChain for context management.

## Development Commands

### Database Management
```bash
# Initialize database with sample data
python manage.py init_db

# Database health check
python manage.py health_check

# Display database information
python manage.py db_info

# Create new user
python manage.py create_user

# List all users
python manage.py list_users

# Reset database (use with caution)
python manage.py reset_db
```

### Application Startup
```bash
# Development mode (runs on port 2727)
python run.py

# Production mode with environment variable
FLASK_ENV=production python run.py
```

### Testing
No specific test framework is configured. Check existing test files:
- `test_admin_system.py`
- `test_langchain_integration.py`
- `test_timezone_only.py`

### Code Quality
The project uses these development tools (from requirements.txt):
- `black` - Code formatting
- `flake8` - Linting
- `isort` - Import sorting
- `pytest` - Testing framework

## Architecture Overview

### Core Components

**Flask Application Factory** (`app/__init__.py`):
- Multi-environment configuration (development, production, testing)
- Blueprint registration for modular routing
- Error handling (404, 500)
- Custom Jinja2 filters

**Database Layer** (`app/database.py`):
- SQLAlchemy ORM with SQLite (dev) / PostgreSQL (prod)
- UUID-based primary keys for most tables
- Timezone-aware datetime handling (UTC+8)

**Authentication System** (`app/auth/`):
- Flask-Login based user sessions
- Role-based access control (admin, tester, vip, user)
- User registration and profile management

**AI Integration**:
- DeepSeek-V3 API integration (`app/services/deepseek_service.py`)
- LangChain framework for context management (`app/services/langchain_service.py`)
- Conversation summarization and token management

### Key Models

**User System** (`app/models/user.py`):
- UUID primary keys
- Role-based permissions (admin, tester, vip, user)
- User status flags (active, verified, disabled, deleted)
- Timezone-aware timestamps

**Knowledge Base** (`app/models/knowledge_base.py`):
- Document upload and processing (PDF, Word, TXT)
- Vector embeddings with FAISS/ChromaDB
- Document chunking for RAG retrieval
- Conversation history with message threading

**Community Features** (`app/models/community.py`):
- Social posts with AI-generated content
- User interactions (likes, comments, shares)
- User follow system

### Service Layer

**Conversation Service** (`app/services/conversation_service.py`):
- Multi-turn dialogue management
- Context window handling
- Automatic conversation summarization every 5 rounds
- Token counting and optimization

**LangChain Service** (`app/services/langchain_service.py`):
- Memory management (buffer, summary_buffer, sliding_window)
- Context analysis and efficiency evaluation
- Configurable memory types and parameters

**Community Service** (`app/services/community_service.py`):
- Social media functionality
- Post creation and management
- User interaction tracking

### Routing Structure

**Main Routes** (`app/routes/main.py`):
- `/` - Homepage
- `/chat` - AI conversation interface
- `/knowledge` - Knowledge base management
- `/dashboard` - User dashboard

**API Routes** (`app/routes/api.py`):
- `/api/chat` - Chat messaging
- `/api/conversations` - Conversation management
- `/api/upload` - Document upload
- `/api/database_search` - Database queries

**Admin Routes** (`app/routes/admin.py`):
- `/admin/dashboard` - Admin dashboard with analytics
- `/admin/users` - User management
- `/admin/conversations` - Conversation oversight
- `/admin/database_tools` - SQL query interface

## Configuration

### Environment Setup
Configuration is managed through `config/settings.py` with environment-specific classes:
- `DevelopmentConfig` - Debug mode, SQLite database
- `ProductionConfig` - Production settings
- `TestingConfig` - In-memory database for testing

### Key Configuration Options
```python
# DeepSeek API
DEEPSEEK_API_KEY = "your-api-key"
DEEPSEEK_API_BASE = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# LangChain Settings
LANGCHAIN_ENABLED = True
LANGCHAIN_MEMORY_TYPE = "buffer"  # or "summary_buffer", "sliding_window"
LANGCHAIN_MAX_TOKEN_LIMIT = 8000
LANGCHAIN_WINDOW_SIZE = 10

# Conversation Management
CONVERSATION_SUMMARY_ROUNDS = 10
MAX_CONTEXT_MESSAGES = 20
```

## Database Schema

### Primary Tables
- `users` - User accounts with role-based access
- `knowledge_bases` - Document collections per user
- `documents` - Individual files with processing status
- `document_chunks` - Text segments for RAG retrieval
- `conversations` - Chat sessions with metadata
- `messages` - Individual chat messages
- `community_posts` - Social media posts
- `community_interactions` - User engagement data

### Known Issues
The community tables have type mismatches (INTEGER vs VARCHAR(36) for foreign keys) but work due to SQLite's weak typing. See `docs/database_structure.md` for details.

## Development Patterns

### Error Handling
- Custom error pages (`app/templates/errors/`)
- Database session rollback on 500 errors
- Comprehensive logging throughout services

### Security
- Role-based access control via decorators
- Input validation on all forms
- CSRF protection with Flask-WTF
- Password hashing with bcrypt

### Frontend Architecture
- Server-side rendered templates with Jinja2
- Bootstrap 5 + custom CSS following GitHub design principles
- WebSocket integration for real-time chat
- Responsive design with mobile-first approach

### File Structure Conventions
- Models in `app/models/` - Database schema definitions
- Services in `app/services/` - Business logic layer
- Routes in `app/routes/` - HTTP endpoint handlers
- Templates in `app/templates/` - HTML templates
- Static assets in `app/static/` - CSS, JS, images

## Testing Strategy

Run existing tests to verify functionality:
```bash
python test_admin_system.py
python test_langchain_integration.py
python test_timezone_only.py
```

For new features, follow the existing test patterns and consider:
- Database transaction rollback in tests
- Mock external API calls (DeepSeek)
- Test role-based access control
- Validate timezone handling

## Common Development Tasks

### Adding New AI Models
1. Create service class in `app/services/`
2. Add configuration options to `config/settings.py`
3. Update conversation service to handle new model
4. Add model selection in chat interface

### Extending User Roles
1. Update `User` model in `app/models/user.py`
2. Modify role permissions in `app/decorators.py`
3. Add role-specific UI elements in templates
4. Update admin user management interface

### Adding Document Types
1. Extend document processing in `app/services/`
2. Update file upload validation
3. Add new MIME type support
4. Test document chunking and vectorization

## Deployment Notes

- Default port: 2727
- Supports both SQLite (dev) and PostgreSQL (prod)
- Redis caching available
- Gunicorn + Nginx recommended for production
- See `docs/deployment_guide.md` for detailed setup

## Security Considerations

- Never commit API keys to repository
- Use environment variables for sensitive configuration
- Implement proper input validation for all user inputs
- Regular security audits of user permissions
- Keep dependencies updated for security patches