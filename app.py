from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import base64
import json
import io

from config import config
from models import db, User, Character, init_db

def create_app(config_name=None):
    app = Flask(__name__)

    # Configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Bitte melden Sie sich an, um auf diese Seite zuzugreifen.'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create upload directory
    upload_folder = app.config.get('UPLOAD_FOLDER', 'static/images')
    os.makedirs(upload_folder, exist_ok=True)

    # Initialize database
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

    return app

# Create the app
app = create_app()

# Routes
@app.route('/')
def index():
    """Redirect to login if not authenticated, else to dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handling"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Benutzername und Passwort erforderlich', 'error')
            return render_template('dashboard.html', characters=[])

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Erfolgreich angemeldet!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Ungültiger Benutzername oder Passwort', 'error')
            return render_template('dashboard.html', characters=[])

    # GET request - show dashboard template with login form
    return render_template('dashboard.html', characters=[])

@app.route('/register', methods=['POST'])
def register():
    """Handle registration form submission"""
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not username or not email or not password:
        flash('Alle Felder sind erforderlich', 'error')
        return render_template('dashboard.html', characters=[])

    if password != confirm_password:
        flash('Passwörter stimmen nicht überein', 'error')
        return render_template('dashboard.html', characters=[])

    if User.query.filter_by(username=username).first():
        flash('Benutzername bereits vergeben', 'error')
        return render_template('dashboard.html', characters=[])

    try:
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registrierung erfolgreich! Sie können sich jetzt anmelden.', 'success')
        return render_template('dashboard.html', characters=[])
    except Exception as e:
        db.session.rollback()
        flash('Fehler bei der Registrierung', 'error')
        return render_template('dashboard.html', characters=[])

@app.route('/test_login.html')
def test_login():
    """Test login page"""
    return send_from_directory('.', 'test_login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Main character management dashboard"""
    characters = Character.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', characters=characters)

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('Sie wurden erfolgreich abgemeldet.', 'success')
    return redirect(url_for('login'))

# API Routes
@app.route('/api/register', methods=['POST'])
def api_register():
    """Register new user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Benutzername und Passwort erforderlich'}), 400

        if len(password) < 4:
            return jsonify({'success': False, 'message': 'Passwort muss mindestens 4 Zeichen lang sein'}), 400

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Benutzername bereits vergeben'}), 400

        # Create new user
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Benutzer erfolgreich erstellt'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler beim Erstellen des Benutzers: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    """Login user"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Benutzername und Passwort erforderlich'}), 400

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return jsonify({'success': True, 'userId': user.id, 'username': user.username})
        else:
            return jsonify({'success': False, 'message': 'Ungültiger Benutzername oder Passwort'}), 401

    except Exception as e:
        return jsonify({'success': False, 'message': f'Anmeldefehler: {str(e)}'}), 500

@app.route('/api/characters', methods=['GET'])
@login_required
def api_get_characters():
    """Get all characters for current user"""
    try:
        characters = Character.query.filter_by(user_id=current_user.id).all()
        return jsonify({'success': True, 'characters': [char.to_dict() for char in characters]})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Fehler beim Laden der Charaktere: {str(e)}'}), 500

@app.route('/api/characters/<int:character_id>', methods=['GET'])
@login_required
def api_get_character(character_id):
    """Get single character by ID"""
    try:
        character = Character.query.filter_by(id=character_id, user_id=current_user.id).first()

        if not character:
            return jsonify({'success': False, 'message': 'Charakter nicht gefunden'}), 404

        return jsonify({'success': True, 'character': character.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Fehler beim Laden des Charakters: {str(e)}'}), 500

@app.route('/api/characters', methods=['POST'])
@login_required
def api_create_character():
    """Create new character"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()

        if not name:
            return jsonify({'success': False, 'message': 'Charaktername erforderlich'}), 400

        # Create new character
        character = Character(
            user_id=current_user.id,
            name=name,
            staerke=data.get('staerke', 1),
            geschicklichkeit=data.get('geschicklichkeit', 1),
            wahrnehmung=data.get('wahrnehmung', 1),
            willenskraft=data.get('willenskraft', 1)
        )

        # Calculate derived values
        character.calculate_derived_values()

        # Handle image if provided
        if 'image_base64' in data and data['image_base64']:
            character.set_image_from_base64(data['image_base64'])

        # Handle states and effects
        if 'zustaende' in data:
            character.set_zustaende(data['zustaende'])

        if 'effekte' in data:
            character.set_effekte(data['effekte'])

        db.session.add(character)
        db.session.commit()

        return jsonify({'success': True, 'character': character.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler beim Erstellen des Charakters: {str(e)}'}), 500

@app.route('/api/characters/<int:character_id>', methods=['PUT'])
@login_required
def api_update_character(character_id):
    """Update character"""
    try:
        character = Character.query.filter_by(id=character_id, user_id=current_user.id).first()

        if not character:
            return jsonify({'success': False, 'message': 'Charakter nicht gefunden'}), 404

        data = request.get_json()

        # Update basic attributes
        if 'name' in data:
            character.name = data['name'].strip()

        for attr in ['staerke', 'geschicklichkeit', 'wahrnehmung', 'willenskraft']:
            if attr in data:
                setattr(character, attr, max(1, int(data[attr])))

        for attr in ['aktuelles_leben', 'aktueller_stress']:
            if attr in data:
                setattr(character, attr, max(0, int(data[attr])))

        # Handle image update
        if 'image_base64' in data:
            if data['image_base64']:
                character.set_image_from_base64(data['image_base64'])
            else:
                character.image_data = None
                character.image_filename = None

        # Handle states and effects
        if 'zustaende' in data:
            character.set_zustaende(data['zustaende'])

        if 'effekte' in data:
            character.set_effekte(data['effekte'])

        # Recalculate derived values
        character.calculate_derived_values()

        db.session.commit()

        return jsonify({'success': True, 'character': character.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler beim Aktualisieren des Charakters: {str(e)}'}), 500

@app.route('/api/characters/<int:character_id>', methods=['DELETE'])
@login_required
def api_delete_character(character_id):
    """Delete character"""
    try:
        character = Character.query.filter_by(id=character_id, user_id=current_user.id).first()

        if not character:
            return jsonify({'success': False, 'message': 'Charakter nicht gefunden'}), 404

        db.session.delete(character)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Charakter erfolgreich gelöscht'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler beim Löschen des Charakters: {str(e)}'}), 500

@app.route('/api/user/info')
@login_required
def api_user_info():
    """Get current user information"""
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4000)