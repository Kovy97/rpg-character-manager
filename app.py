from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import base64
import json
import io

from config import config
from models import db, User, Character, ChatRoom, ChatMessage, RoomMember, init_db

def create_app(config_name=None):
    app = Flask(__name__)

    # Configuration - Auto-detect environment
    if config_name is None:
        # DigitalOcean sets DATABASE_URL, use that as production indicator
        if os.environ.get('DATABASE_URL') or os.environ.get('PORT'):
            config_name = 'production'
        else:
            config_name = os.environ.get('FLASK_ENV', 'development')

    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

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

    # Initialize database tables
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully!")
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")

    return app

# Create the app instance
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

    if User.query.filter_by(email=email).first():
        flash('E-Mail-Adresse bereits vergeben', 'error')
        return render_template('dashboard.html', characters=[])

    try:
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registrierung erfolgreich! Sie können sich jetzt anmelden.', 'success')
        return render_template('dashboard.html', characters=[])
    except Exception as e:
        db.session.rollback()
        flash(f'Fehler bei der Registrierung: {str(e)}', 'error')
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

@app.route('/api/user/chat-settings', methods=['GET'])
@login_required
def api_get_chat_settings():
    """Get current user's chat settings"""
    try:
        return jsonify({
            'success': True,
            'settings': current_user.get_chat_settings()
        })
    except Exception as e:
        # Fallback to default settings if column doesn't exist
        default_settings = {
            "normalColor": "#e9eef3",
            "quoteColor": "#4ec9b0",
            "fontSize": 14,
            "fontFamily": "Inter, 'Segoe UI', Arial, sans-serif"
        }
        return jsonify({
            'success': True,
            'settings': default_settings
        })

@app.route('/api/user/chat-settings', methods=['POST'])
@login_required
def api_save_chat_settings():
    """Save current user's chat settings"""
    try:
        data = request.get_json()

        # Validate settings structure
        required_fields = ['normalColor', 'quoteColor', 'fontSize', 'fontFamily']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'Fehlende Settings-Felder'}), 400

        # Validate values
        if not isinstance(data['fontSize'], int) or not (10 <= data['fontSize'] <= 24):
            return jsonify({'success': False, 'message': 'Ungültige Schriftgröße'}), 400

        # Try to save settings, ignore if column doesn't exist
        try:
            current_user.set_chat_settings(data)
            db.session.commit()
            settings = current_user.get_chat_settings()
        except Exception:
            # If chat_settings column doesn't exist, just return success with submitted data
            settings = data

        return jsonify({
            'success': True,
            'message': 'Chat-Settings erfolgreich gespeichert',
            'settings': settings
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler beim Speichern: {str(e)}'}), 500

# Chat API Endpoints
@app.route('/api/chat/rooms', methods=['GET'])
@login_required
def api_get_rooms():
    """Get available chat rooms for user"""
    try:
        # Get ALL rooms (public + private), but private ones show with lock icon
        all_rooms = ChatRoom.query.all()

        return jsonify({
            'success': True,
            'rooms': [room.to_dict() for room in all_rooms]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500

@app.route('/api/chat/rooms', methods=['POST'])
@login_required
def api_create_room():
    """Create new chat room"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        password = data.get('password', '').strip()

        if not name:
            return jsonify({'success': False, 'message': 'Raumname ist erforderlich'}), 400

        # Check if room name already exists
        existing = ChatRoom.query.filter_by(name=name).first()
        if existing:
            return jsonify({'success': False, 'message': 'Raumname bereits vergeben'}), 400

        # Create room
        room = ChatRoom(
            name=name,
            description=description,
            created_by=current_user.id
        )

        if password:
            room.set_password(password)

        db.session.add(room)
        db.session.flush()  # Get room ID

        # Add creator as admin member
        member = RoomMember(
            room_id=room.id,
            user_id=current_user.id,
            role='admin'
        )
        db.session.add(member)

        # Also auto-join public rooms for all users (no membership needed for public)
        # Private rooms require explicit membership

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Raum erfolgreich erstellt',
            'room': room.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500

@app.route('/api/chat/rooms/<int:room_id>/join', methods=['POST'])
@login_required
def api_join_room(room_id):
    """Join chat room"""
    try:
        room = ChatRoom.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'message': 'Raum nicht gefunden'}), 404

        # Check if already member
        if room.is_member(current_user.id):
            return jsonify({'success': False, 'message': 'Bereits Mitglied in diesem Raum'}), 400

        # Check password for private rooms
        if not room.is_public:
            data = request.get_json()
            password = data.get('password', '') if data else ''
            if not room.check_password(password):
                return jsonify({'success': False, 'message': 'Falsches Passwort'}), 401

        # Add member
        member = RoomMember(
            room_id=room_id,
            user_id=current_user.id
        )
        db.session.add(member)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Raum erfolgreich beigetreten'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500

@app.route('/api/chat/rooms/<int:room_id>/leave', methods=['POST'])
@login_required
def api_leave_room(room_id):
    """Leave chat room"""
    try:
        member = RoomMember.query.filter_by(room_id=room_id, user_id=current_user.id).first()
        if not member:
            return jsonify({'success': False, 'message': 'Nicht Mitglied in diesem Raum'}), 400

        db.session.delete(member)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Raum verlassen'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500

@app.route('/api/chat/rooms/<int:room_id>/messages', methods=['GET'])
@login_required
def api_get_messages(room_id):
    """Get messages for room"""
    try:
        room = ChatRoom.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'message': 'Raum nicht gefunden'}), 404

        # Check if user is member (for private rooms) or if room is public
        if not room.is_public and not room.is_member(current_user.id):
            return jsonify({'success': False, 'message': 'Kein Zugriff auf diesen Raum'}), 403

        # Get last 200 messages
        messages = ChatMessage.query.filter_by(room_id=room_id)\
                                  .order_by(ChatMessage.timestamp.desc())\
                                  .limit(200).all()
        messages.reverse()  # Show oldest first

        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in messages]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500

@app.route('/api/chat/rooms/<int:room_id>/messages', methods=['POST'])
@login_required
def api_send_message(room_id):
    """Send message to room"""
    try:
        room = ChatRoom.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'message': 'Raum nicht gefunden'}), 404

        # Check if user is member (for private rooms) or if room is public
        if not room.is_public and not room.is_member(current_user.id):
            return jsonify({'success': False, 'message': 'Kein Zugriff auf diesen Raum'}), 403

        data = request.get_json()
        message_text = data.get('message', '').strip()

        if not message_text:
            return jsonify({'success': False, 'message': 'Nachricht darf nicht leer sein'}), 400

        if len(message_text) > 3000:
            return jsonify({'success': False, 'message': 'Nachricht zu lang (max. 3000 Zeichen)'}), 400

        # Create message
        message = ChatMessage(
            room_id=room_id,
            user_id=current_user.id,
            message=message_text
        )
        db.session.add(message)

        # Clean up old messages if more than 200
        message_count = ChatMessage.query.filter_by(room_id=room_id).count()
        if message_count > 200:
            old_messages = ChatMessage.query.filter_by(room_id=room_id)\
                                         .order_by(ChatMessage.timestamp.asc())\
                                         .limit(message_count - 200).all()
            for old_msg in old_messages:
                db.session.delete(old_msg)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': message.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500

@app.route('/api/chat/rooms/<int:room_id>/dice', methods=['POST'])
@login_required
def api_send_dice_roll(room_id):
    """Send dice roll announcement to chat room"""
    try:
        room = ChatRoom.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'message': 'Raum nicht gefunden'}), 404

        # Check if user is member (for private rooms) or if room is public
        if not room.is_public and not room.is_member(current_user.id):
            return jsonify({'success': False, 'message': 'Kein Zugriff auf diesen Raum'}), 403

        data = request.get_json()
        character_name = data.get('character_name', '').strip()
        attribute = data.get('attribute', '').strip()
        roll_value = int(data.get('roll_value', 0))
        modifier = int(data.get('modifier', 0))
        total = int(data.get('total', 0))

        if not character_name or not attribute:
            return jsonify({'success': False, 'message': 'Charaktername und Attribut erforderlich'}), 400

        # Determine roll result type
        if roll_value == 20:
            result_type = 'critical-success'
            result_text = 'Kritischer Erfolg!'
        elif roll_value == 1:
            result_type = 'critical-fail'
            result_text = 'Kritischer Fehler!'
        else:
            result_type = 'normal'
            result_text = 'Erfolg'

        # Create formatted dice message
        dice_message = f"""{current_user.username}:
Würfelt für "{character_name}" {attribute}: W20={roll_value}+{modifier}={total}"""

        # Create message with special dice formatting
        message = ChatMessage(
            room_id=room_id,
            user_id=current_user.id,
            message=dice_message,
            message_type='dice'  # Special type for dice rolls
        )
        db.session.add(message)

        # Clean up old messages if more than 200
        message_count = ChatMessage.query.filter_by(room_id=room_id).count()
        if message_count > 200:
            old_messages = ChatMessage.query.filter_by(room_id=room_id)\
                                         .order_by(ChatMessage.timestamp.asc())\
                                         .limit(message_count - 200).all()
            for old_msg in old_messages:
                db.session.delete(old_msg)

        db.session.commit()

        # Return message with dice metadata for frontend formatting
        message_dict = message.to_dict()
        message_dict.update({
            'dice_data': {
                'character_name': character_name,
                'attribute': attribute,
                'roll_value': roll_value,
                'modifier': modifier,
                'total': total,
                'result_type': result_type
            }
        })

        return jsonify({
            'success': True,
            'message': message_dict
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500

@app.route('/api/chat/rooms/<int:room_id>/share-character', methods=['POST'])
@login_required
def api_share_character(room_id):
    """Share character to chat room"""
    try:
        room = ChatRoom.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'message': 'Raum nicht gefunden'}), 404

        # Check if user is member (for private rooms) or if room is public
        if not room.is_public and not room.is_member(current_user.id):
            return jsonify({'success': False, 'message': 'Kein Zugriff auf diesen Raum'}), 403

        data = request.get_json()
        character_data = data.get('character_data')

        if not character_data:
            return jsonify({'success': False, 'message': 'Charakterdaten erforderlich'}), 400

        # Create character share message
        share_message = f"""{current_user.username} teilt Charakter "{character_data['name']}" """

        # Create message with character data
        message = ChatMessage(
            room_id=room_id,
            user_id=current_user.id,
            message=share_message,
            message_type='character_share',  # Special type for character sharing
            message_data=json.dumps({'character_data': character_data})
        )
        db.session.add(message)

        # Clean up old messages if more than 200
        message_count = ChatMessage.query.filter_by(room_id=room_id).count()
        if message_count > 200:
            old_messages = ChatMessage.query.filter_by(room_id=room_id)\
                                         .order_by(ChatMessage.timestamp.asc())\
                                         .limit(message_count - 200).all()
            for old_msg in old_messages:
                db.session.delete(old_msg)

        db.session.commit()

        # Return message with character data for frontend
        message_dict = message.to_dict()
        message_dict['character_data'] = character_data


        return jsonify({
            'success': True,
            'message': message_dict
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500

@app.route('/api/characters/import', methods=['POST'])
@login_required
def api_import_character():
    """Import shared character to user's character list"""
    try:
        data = request.get_json()
        character_data = data.get('character_data')

        if not character_data:
            return jsonify({'success': False, 'message': 'Charakterdaten erforderlich'}), 400

        # Create new character for the current user
        character = Character(
            user_id=current_user.id,
            name=character_data['name'] + ' (Import)',  # Add (Import) to distinguish
            staerke=character_data.get('staerke', 1),
            geschicklichkeit=character_data.get('geschicklichkeit', 1),
            wahrnehmung=character_data.get('wahrnehmung', 1),
            willenskraft=character_data.get('willenskraft', 1),
            aktuelles_leben=character_data.get('aktuelles_leben', 20),
            aktueller_stress=character_data.get('aktueller_stress', 0)
        )

        # Set states and effects if provided
        if 'zustaende' in character_data:
            character.set_zustaende(character_data['zustaende'])

        if 'effekte' in character_data:
            character.set_effekte(character_data['effekte'])

        # Calculate derived values
        character.calculate_derived_values()

        # Handle image if provided
        if character_data.get('image_base64'):
            character.set_image_from_base64(character_data['image_base64'])

        db.session.add(character)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Charakter erfolgreich importiert',
            'character': character.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler beim Importieren: {str(e)}'}), 500

@app.route('/api/chat/rooms/<int:room_id>/members', methods=['GET'])
@login_required
def api_get_members(room_id):
    """Get room members"""
    try:
        room = ChatRoom.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'message': 'Raum nicht gefunden'}), 404

        # Check if user is member (for private rooms) or if room is public
        if not room.is_public and not room.is_member(current_user.id):
            return jsonify({'success': False, 'message': 'Kein Zugriff auf diesen Raum'}), 403

        members = RoomMember.query.filter_by(room_id=room_id).all()

        return jsonify({
            'success': True,
            'members': [member.to_dict() for member in members]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500


@app.route('/api/chat/rooms/<int:room_id>/kick', methods=['POST'])
@login_required
def api_kick_member(room_id):
    """Kick a member from the room (only room creator can do this)"""
    try:
        room = ChatRoom.query.get(room_id)
        if not room:
            return jsonify({'success': False, 'message': 'Raum nicht gefunden'}), 404

        # Check if current user is room creator
        if room.created_by != current_user.id:
            return jsonify({'success': False, 'message': 'Nur der Raum-Ersteller kann Mitglieder entfernen'}), 403

        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'message': 'Benutzer-ID fehlt'}), 400

        # Can't kick yourself
        if user_id == current_user.id:
            return jsonify({'success': False, 'message': 'Sie können sich nicht selbst entfernen'}), 400

        # Find and remove membership
        membership = RoomMember.query.filter_by(room_id=room_id, user_id=user_id).first()
        if not membership:
            return jsonify({'success': False, 'message': 'Benutzer ist nicht Mitglied dieses Raums'}), 404

        db.session.delete(membership)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Mitglied erfolgreich entfernt'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500


@app.route('/api/chat/messages/<int:message_id>', methods=['DELETE'])
@login_required
def api_delete_message(message_id):
    """Delete a message (only message author can do this)"""
    try:
        message = ChatMessage.query.get(message_id)
        if not message:
            return jsonify({'success': False, 'message': 'Nachricht nicht gefunden'}), 404

        # Check if current user is message author
        if message.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Sie können nur Ihre eigenen Nachrichten löschen'}), 403

        db.session.delete(message)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Nachricht erfolgreich gelöscht'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500


@app.route('/api/chat/messages/<int:message_id>', methods=['PUT'])
@login_required
def api_edit_message(message_id):
    """Edit a message (only message author can do this)"""
    try:
        message = ChatMessage.query.get(message_id)
        if not message:
            return jsonify({'success': False, 'message': 'Nachricht nicht gefunden'}), 404

        # Check if current user is message author
        if message.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Sie können nur Ihre eigenen Nachrichten bearbeiten'}), 403

        data = request.get_json()
        new_text = data.get('message', '').strip()

        if not new_text:
            return jsonify({'success': False, 'message': 'Nachricht darf nicht leer sein'}), 400

        if len(new_text) > 3000:
            return jsonify({'success': False, 'message': 'Nachricht ist zu lang (max. 3000 Zeichen)'}), 400

        message.message = new_text
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Nachricht erfolgreich bearbeitet'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)