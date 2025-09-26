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
python -c "from app import app, db; db.create_all()"
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
# Run tests
python -m pytest

# Coverage report
python -m pytest --cov=app

# Code formatting
black .

# Linting
flake8 .
```

## Architecture Overview

### Application Factory Pattern
- `app.py`: Main Flask application using factory pattern with `create_app()`
- `config.py`: Configuration classes for development/production environments
- `wsgi.py`: Production WSGI entry point

### Database Architecture
- **SQLAlchemy ORM** with two main models:
  - `User`: Authentication with bcrypt password hashing
  - `Character`: RPG character data with JSON fields for complex data
- **Database agnostic**: SQLite for development, PostgreSQL for production
- **Automatic derived value calculation**: Leben (health) and stress limits calculated from attributes

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
- **Server-side rendered** with Jinja2 templates
- **Vanilla JavaScript** for dynamic interactions
- **Templates**: `base.html`, `login.html`, `dashboard.html`
- **Static assets**: CSS, JS, and image uploads in `/static`

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
- Password hashing with Werkzeug
- User isolation (users can only access their own characters)
- CSRF protection via Flask-WTF
- File upload security with secure filename handling

### Performance Considerations
- Database indexes on frequently queried fields (user_id, username)
- Lazy loading for character relationships
- JSON fields for flexible state/effect storage

## Development Patterns

When working with this codebase:
- Follow the existing German naming conventions for character attributes
- Use the `to_dict()` methods for JSON serialization
- Handle database transactions with proper rollback on errors
- Test both SQLite (development) and PostgreSQL (production) compatibility
- Maintain the automatic derived value calculation when updating character attributes

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
├── app.py              # Main Flask application
├── models.py           # Database models (User, Character)
├── config.py           # Environment configuration
├── wsgi.py             # Production WSGI entry point
├── Procfile            # DigitalOcean deployment config
├── requirements.txt    # Python dependencies
├── .python-version     # Python 3.11
├── templates/
│   ├── base.html       # Base template
│   └── dashboard.html  # Main application interface
├── static/
│   ├── css/style.css   # All styling
│   └── js/app.js       # JavaScript functionality
└── CLAUDE.md           # This documentation
```

### Deployment Notes:
- Uses Python 3.11 for compatibility
- Procfile configured for Gunicorn
- Environment variables required: DATABASE_URL, SECRET_KEY
- .buildpacks file ensures Python-only buildpack
- .gitignore excludes development files (*.db, __pycache__)

The application is fully functional and ready for users!