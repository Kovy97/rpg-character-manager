# RPG Character Manager

Ein moderner, webbasierter Charakter-Manager für Rollenspiele, gebaut mit Python Flask und PostgreSQL.

## Features

- 🔐 **Benutzer-Authentifizierung**: Sichere Registrierung und Anmeldung
- 👤 **Charakterverwaltung**: Erstellen, bearbeiten und löschen von Charakteren
- 📊 **Attributsystem**: Stärke, Geschicklichkeit, Wahrnehmung, Willenskraft
- ❤️ **Lebenspunkte & Stress**: Automatische Berechnung basierend auf Attributen
- 🖼️ **Bildupload**: Charakterporträts mit Drag & Drop
- 📝 **Zustände & Effekte**: Verwalten von temporären Charakterzuständen
- 🎨 **Modernes Design**: Dark Theme mit responsivem Layout
- ☁️ **Cloud-Ready**: Vorbereitet für DigitalOcean Deployment

## Technologie-Stack

- **Backend**: Python Flask 3.0
- **Database**: PostgreSQL mit SQLAlchemy ORM
- **Frontend**: Vanilla JavaScript mit modernem CSS
- **Authentication**: Flask-Login mit bcrypt Hashing
- **Deployment**: Docker + Gunicorn

## Installation

### Lokale Entwicklung

1. **Repository klonen**
   ```bash
   git clone <repository-url>
   cd rpg-character-manager-flask
   ```

2. **Virtual Environment erstellen**
   ```bash
   python -m venv venv
   venv\\Scripts\\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Dependencies installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment-Variablen konfigurieren**
   ```bash
   cp .env.example .env
   # .env-Datei mit deinen Datenbank-Zugangsdaten bearbeiten
   ```

5. **Anwendung starten**
   ```bash
   python app.py
   ```

   Die Anwendung ist dann unter `http://localhost:5000` erreichbar.

### Docker Deployment

1. **Docker Image bauen**
   ```bash
   docker build -t rpg-character-manager .
   ```

2. **Container starten**
   ```bash
   docker run -d \\
     --name rpg-manager \\
     -p 5000:5000 \\
     --env-file .env \\
     rpg-character-manager
   ```

## Konfiguration

### Umgebungsvariablen

Erstelle eine `.env`-Datei basierend auf `.env.example`:

```env
# Database (DigitalOcean PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# Security
SECRET_KEY=your-secret-key-here

# App Settings
FLASK_ENV=production
```

### DigitalOcean Deployment

1. **Database Setup**: PostgreSQL Managed Database erstellen
2. **App Platform**: Neue App erstellen und Repository verbinden
3. **Environment Variables**: In der App Platform Konsole setzen
4. **Deploy**: Automatisches Deployment bei Git Push

## Verwendung

### Erste Schritte

1. **Registrierung**: Neuen Account erstellen
2. **Login**: Mit Benutzerdaten anmelden
3. **Charakter erstellen**: "Neuer Charakter" Button klicken
4. **Attribute setzen**: Grundattribute eingeben (1-20)
5. **Bild hochladen**: Charakterportrait hinzufügen
6. **Speichern**: Änderungen mit Ctrl+S speichern

### Charaktersystem

#### Grundattribute (1-20)
- **Stärke**: Physische Kraft
- **Geschicklichkeit**: Beweglichkeit und Feinmotorik
- **Wahrnehmung**: Aufmerksamkeit und Sinne
- **Willenskraft**: Mentale Stärke und Fokus

#### Abgeleitete Werte
- **Leben**: (Stärke + Willenskraft) × 2 + 10
- **Max. Stress**: Willenskraft × 3
- **Aktuelles Leben**: Variable, max = Leben
- **Aktueller Stress**: Variable, sollte unter Max. Stress bleiben

### Keyboard Shortcuts

- `Ctrl+S` / `Cmd+S`: Charakter speichern
- `Escape`: Modal schließen

## API Endpoints

### Authentifizierung
- `POST /api/register` - Benutzer registrieren
- `POST /api/login` - Benutzer anmelden
- `GET /api/user/info` - Benutzer-Info abrufen

### Charaktere
- `GET /api/characters` - Alle Charaktere abrufen
- `POST /api/characters` - Neuen Charakter erstellen
- `PUT /api/characters/<id>` - Charakter aktualisieren
- `DELETE /api/characters/<id>` - Charakter löschen

## Entwicklung

### Projektstruktur

```
rpg-character-manager-flask/
├── app.py                 # Flask Hauptanwendung
├── models.py              # Database Models
├── config.py              # Konfiguration
├── wsgi.py               # Production WSGI Entry Point
├── requirements.txt       # Python Dependencies
├── Dockerfile            # Container Definition
├── .env                  # Environment Variables
├── templates/            # Jinja2 Templates
│   ├── base.html
│   ├── login.html
│   └── dashboard.html
├── static/               # Static Assets
│   ├── css/style.css
│   ├── js/app.js
│   └── images/           # Uploaded Images
└── migrations/           # Database Migrations
```

### Datenbank-Schema

#### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Characters Table
```sql
CREATE TABLE characters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    staerke INTEGER DEFAULT 1,
    geschicklichkeit INTEGER DEFAULT 1,
    wahrnehmung INTEGER DEFAULT 1,
    willenskraft INTEGER DEFAULT 1,
    leben INTEGER DEFAULT 20,
    stress INTEGER DEFAULT 0,
    aktuelles_leben INTEGER DEFAULT 20,
    aktueller_stress INTEGER DEFAULT 0,
    zustaende TEXT DEFAULT '[]',
    effekte TEXT DEFAULT '[]',
    image_data BYTEA,
    image_filename VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Testing

```bash
# Unit Tests ausführen
python -m pytest

# Coverage Report
python -m pytest --cov=app
```

### Code Style

```bash
# Code formatieren
black .

# Linting
flake8 .
```

## Deployment

### DigitalOcean App Platform

1. Repository mit App Platform verbinden
2. Build Command: `pip install -r requirements.txt`
3. Run Command: `gunicorn wsgi:app`
4. Environment Variables in der Konsole setzen

### Heroku

1. `heroku create app-name`
2. `heroku addons:create heroku-postgresql:hobby-dev`
3. Environment Variables setzen
4. `git push heroku main`

## Troubleshooting

### Häufige Probleme

**Database Connection Error**
- Database URL in .env prüfen
- Firewall/Security Groups prüfen
- SSL-Konfiguration überprüfen

**Image Upload Fails**
- Upload-Verzeichnis Berechtigung prüfen
- MAX_CONTENT_LENGTH in config.py anpassen
- Disk Space überprüfen

**Login nicht möglich**
- Passwort-Hash-Kompatibilität prüfen
- Session-Konfiguration überprüfen
- Browser Cookies löschen

## Support

Bei Fragen oder Problemen:

1. **Issues**: GitHub Issues verwenden
2. **Documentation**: README.md und Code-Kommentare
3. **Logs**: Application Logs in `/var/log/` prüfen

## Lizenz

MIT License - siehe LICENSE Datei für Details.

## Changelog

### v1.0.0 (2024)
- ✨ Initial Release
- 🔐 User Authentication System
- 👤 Character Management
- 📊 Attribute System
- 🖼️ Image Upload
- 🎨 Modern UI Design
- ☁️ DigitalOcean Ready