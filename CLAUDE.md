# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a German-language RPG Character Manager web application built with Flask and PostgreSQL. It allows users to create and manage RPG characters with attributes, health/stress tracking, image uploads, and state management.

## Development Commands

### Running the Application
```bash
# Development server (with debug mode) - runs on localhost:4000
python app.py

# Production with Gunicorn
gunicorn wsgi:app
```

### Database Management
```bash
# Initialize database (automatic on first run)
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app import db; db.create_all()"

# Access database shell
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app import db; from models import User, Character"
```

### Docker Commands
```bash
# Build container
docker build -t rpg-character-manager .

# Run container
docker run -d --name rpg-manager -p 5000:5000 --env-file .env rpg-character-manager
```

### Testing and Code Quality
```bash
# Note: No formal testing framework is currently configured
# The following commands are not yet implemented but represent intended workflow:

# Install development dependencies (when available)
# pip install pytest pytest-cov black flake8

# Run tests (when test files are created)
# python -m pytest

# Code formatting (when configured)
# black .

# Linting (when configured)
# flake8 .

# Manual testing
python app.py  # Start development server for manual testing
```

## Architecture Overview

### Application Factory Pattern
- `app.py`: Main Flask application using factory pattern with `create_app()`
- `config.py`: Configuration classes for development/production environments
- `wsgi.py`: Production WSGI entry point

### Database Architecture
- **SQLAlchemy ORM** with two main models:
  - `User`: Authentication with Werkzeug password hashing and Flask-Login integration
  - `Character`: RPG character data with JSON fields for complex data and binary image storage
- **Database agnostic**: SQLite for development (`instance/app.db`), PostgreSQL for production
- **Automatic derived value calculation**: Leben (health) and stress limits calculated from attributes
- **Database initialization**: Automatic on app startup, no manual migration needed

### Character System
- **Base Attributes**: Stärke, Geschicklichkeit, Wahrnehmung, Willenskraft (1-10 scale)
- **Derived Values**:
  - Leben (Health) = (Stärke + Willenskraft) × 2 + 10
  - Max Stress = Willenskraft × 3
- **Dice Rolling System**:
  - W20 + Effective Attribute Value = Total Result
  - W20=1 always Critical Failure (red)
  - W20=20 always Critical Success (gold)
  - Normal rolls 2-19 show "Erfolg" in blue
- **Image Storage**: Base64 encoded in database with drag-and-drop upload
- **States & Effects**: JSON arrays stored as text fields

### API Design
- **RESTful API** with JSON responses
- **Authentication**: Flask-Login session-based
- **Error Handling**: Consistent JSON error responses with German messages
- **Endpoints**:
  - `/api/register`, `/api/login` - Authentication
  - `/api/characters` - CRUD operations for characters
  - `/api/user/info` - User information

### Frontend Architecture
- **Server-side rendered** with Jinja2 templates and embedded JavaScript
- **Single-page application** interface with tab-based character management
- **Templates**:
  - `base.html`: Common layout with flash messages and resource loading
  - `login.html`: Authentication forms with toggle between login/register
  - `dashboard.html`: Main application interface (850+ lines with embedded JS)
- **CSS**: Dark tech theme with custom properties, grid-based responsive layout
- **JavaScript**: Tab management, real-time calculations, drag-drop uploads, dice rolling system

## Key Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string for production
- `SECRET_KEY`: Flask session secret
- `FLASK_ENV`: development/production mode

### Database Connection
- Development uses SQLite (`app.db`)
- Production automatically detects and uses PostgreSQL from `DATABASE_URL`
- Handles Heroku-style `postgres://` to `postgresql://` URL conversion

## Important Implementation Details

### Image Handling
- Images stored as binary data in database (`image_data` BLOB field)
- Base64 encoding/decoding handled in `Character` model methods
- Drag-and-drop upload in frontend with size limits (16MB)

### German Language Interface
- All user-facing text in German
- Error messages and API responses in German
- Character attributes use German names (Stärke, Geschicklichkeit, etc.)

### Security Features
- **Password hashing** with Werkzeug (imported as `werkzeug.security`)
- **Session management** via Flask-Login with user isolation
- **User data isolation**: Users can only access their own characters via database queries
- **File upload security**: Base64 encoding with size limits, secure filename handling
- **CSRF protection**: Flask-WTF imported and ready for form protection

### Performance Considerations
- Database indexes on frequently queried fields (user_id, username)
- Lazy loading for character relationships
- JSON fields for flexible state/effect storage

## Development Patterns

When working with this codebase:
- **German conventions**: Follow existing German naming for attributes (Stärke, Geschicklichkeit, Wahrnehmung, Willenskraft)
- **Model methods**: Use `to_dict()` and `get_image_base64()` methods for consistent serialization
- **Database transactions**: Handle with proper rollback on errors, use Flask application context
- **Database compatibility**: Test both SQLite (development) and PostgreSQL (production) behavior
- **Derived calculations**: Maintain automatic Leben/Stress calculation when updating character attributes
- **Image handling**: Store as binary data with Base64 conversion methods in Character model
- **API responses**: Return consistent JSON format with German error messages

### Code Architecture Notes
- `dashboard.html` contains significant embedded JavaScript (850+ lines) - consider extracting to separate files for maintenance
- Configuration classes in `config.py` support multiple environments but app currently uses simple environment detection
- Database models use JSON fields for flexible state storage (zustaende, effekte arrays)
- Tab-based UI system manages multiple characters simultaneously with local state persistence

## Current Status (September 2025)

### Deployment Status: ✅ LIVE IN PRODUCTION
- **Successfully deployed** on DigitalOcean App Platform
- **Production URL**: Accessible via configured domain
- **Database**: PostgreSQL in production, SQLite for local development
- **Multi-user ready**: Users can register and manage their own characters

### Core Features Implemented:
✅ **User Authentication System**
- Registration and login with secure password hashing
- Session-based authentication with Flask-Login
- User isolation (each user sees only their own characters)

✅ **Character Management**
- Create, edit, delete characters
- Character loading into new tabs
- Image upload and display (drag & drop)
- Attribute system with progress bars (1-10 scale)
- Automatic health/stress calculation

✅ **Dice Rolling System**
- W20 + Attribute modifier system
- Critical success (20) = Gold display
- Critical failure (1) = Red display
- Normal results = Blue display
- Roll history tracking

✅ **User Interface**
- German language interface
- Dark tech theme with CSS custom properties
- Responsive design
- Tab-based character interface
- Flash message system for user feedback

### Technical Implementation:
- **Backend**: Flask with SQLAlchemy ORM
- **Frontend**: Server-side rendered Jinja2 with vanilla JavaScript
- **Database**: SQLite (dev) → PostgreSQL (prod) automatic switching
- **Image Storage**: Base64 encoded in database
- **Deployment**: Gunicorn WSGI server on DigitalOcean

### File Structure:
```
├── app.py              # Main Flask application (342 lines, factory pattern)
├── models.py           # Database models (172 lines: User, Character)
├── config.py           # Environment configuration classes
├── wsgi.py             # Production WSGI entry point
├── Procfile            # DigitalOcean deployment config
├── Dockerfile          # Multi-stage container build
├── requirements.txt    # Python 3.11 compatible dependencies
├── .python-version     # Python 3.11 specification
├── .buildpacks         # Heroku Python buildpack configuration
├── templates/
│   ├── base.html       # Base template with flash messages
│   ├── login.html      # Authentication forms
│   └── dashboard.html  # Main SPA interface (850+ lines with embedded JS)
├── static/
│   ├── css/style.css   # Dark theme with CSS custom properties (1200+ lines)
│   └── js/app.js       # API helpers and shared functionality
├── instance/
│   └── app.db          # SQLite development database (auto-created)
└── CLAUDE.md           # This documentation
```

### Deployment Notes:
- Uses Python 3.11 for compatibility
- Procfile configured for Gunicorn
- Environment variables required: DATABASE_URL, SECRET_KEY
- .buildpacks file ensures Python-only buildpack
- .gitignore excludes development files (*.db, __pycache__)

The application is fully functional and ready for users!