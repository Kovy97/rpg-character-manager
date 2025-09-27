from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Chat settings stored as JSON (nullable for existing users)
    chat_settings = db.Column(db.Text, nullable=True, default='{"normalColor": "#e9eef3", "quoteColor": "#4ec9b0", "fontSize": 14, "fontFamily": "Inter, \'Segoe UI\', Arial, sans-serif"}')

    # Relationship to characters
    characters = db.relationship('Character', backref='owner', lazy=True, cascade='all, delete-orphan')

    # Chat relationships
    chat_rooms = db.relationship('ChatRoom', backref='creator', lazy='dynamic')
    room_memberships = db.relationship('RoomMember', backref='user', lazy='dynamic')
    messages = db.relationship('ChatMessage', backref='author', lazy='dynamic')

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def get_chat_settings(self):
        """Get chat settings as Python dict"""
        try:
            # Handle case where chat_settings column doesn't exist yet
            settings = getattr(self, 'chat_settings', None)
            return json.loads(settings) if settings else self._default_chat_settings()
        except (json.JSONDecodeError, AttributeError):
            return self._default_chat_settings()

    def _default_chat_settings(self):
        """Default chat settings"""
        return {
            "normalColor": "#e9eef3",
            "quoteColor": "#4ec9b0",
            "fontSize": 14,
            "fontFamily": "Inter, 'Segoe UI', Arial, sans-serif"
        }

    def set_chat_settings(self, settings):
        """Set chat settings from Python dict"""
        self.chat_settings = json.dumps(settings) if settings else None

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'chat_settings': self.get_chat_settings()
        }

    def __repr__(self):
        return f'<User {self.username}>'


class Character(db.Model):
    __tablename__ = 'characters'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)

    # Basic attributes
    staerke = db.Column(db.Integer, default=1)
    geschicklichkeit = db.Column(db.Integer, default=1)
    wahrnehmung = db.Column(db.Integer, default=1)
    willenskraft = db.Column(db.Integer, default=1)

    # Calculated values
    leben = db.Column(db.Integer, default=20)
    stress = db.Column(db.Integer, default=0)
    aktuelles_leben = db.Column(db.Integer, default=20)
    aktueller_stress = db.Column(db.Integer, default=0)

    # JSON fields for complex data
    zustaende = db.Column(db.Text, default='[]')  # JSON array of states
    effekte = db.Column(db.Text, default='[]')    # JSON array of effects

    # Image storage
    image_data = db.Column(db.LargeBinary)  # Binary image data
    image_filename = db.Column(db.String(255))

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_zustaende(self):
        """Get states as Python list"""
        try:
            return json.loads(self.zustaende) if self.zustaende else []
        except json.JSONDecodeError:
            return []

    def set_zustaende(self, states):
        """Set states from Python list"""
        self.zustaende = json.dumps(states) if states else '[]'

    def get_effekte(self):
        """Get effects as Python list"""
        try:
            return json.loads(self.effekte) if self.effekte else []
        except json.JSONDecodeError:
            return []

    def set_effekte(self, effects):
        """Set effects from Python list"""
        self.effekte = json.dumps(effects) if effects else '[]'

    def get_image_base64(self):
        """Get image as base64 string for HTML display"""
        if self.image_data:
            import base64
            return base64.b64encode(self.image_data).decode('utf-8')
        return None

    def set_image_from_base64(self, base64_data):
        """Set image from base64 string"""
        if base64_data:
            import base64
            # Remove data URL prefix if present
            if base64_data.startswith('data:image/'):
                base64_data = base64_data.split(',')[1]
            self.image_data = base64.b64decode(base64_data)

    def calculate_derived_values(self):
        """Calculate derived values from basic attributes"""
        # Ensure attributes are not None
        self.staerke = self.staerke or 1
        self.geschicklichkeit = self.geschicklichkeit or 1
        self.wahrnehmung = self.wahrnehmung or 1
        self.willenskraft = self.willenskraft or 1

        # Leben = (Stärke + Willenskraft) * 2 + 10
        self.leben = (self.staerke + self.willenskraft) * 2 + 10

        # If current health is not set or exceeds max, set to max
        if self.aktuelles_leben is None or self.aktuelles_leben > self.leben:
            self.aktuelles_leben = self.leben

        # Stress maximum = Willenskraft * 3
        max_stress = self.willenskraft * 3
        if self.aktueller_stress is None:
            self.aktueller_stress = 0
        elif self.aktueller_stress > max_stress:
            self.aktueller_stress = max_stress

    def to_dict(self):
        """Convert character to dictionary for JSON responses"""
        return {
            'id': self.id,
            'name': self.name,
            'staerke': self.staerke,
            'geschicklichkeit': self.geschicklichkeit,
            'wahrnehmung': self.wahrnehmung,
            'willenskraft': self.willenskraft,
            'leben': self.leben,
            'stress': self.stress,
            'aktuelles_leben': self.aktuelles_leben,
            'aktueller_stress': self.aktueller_stress,
            'zustaende': self.get_zustaende(),
            'effekte': self.get_effekte(),
            'image_base64': self.get_image_base64(),
            'image_filename': self.image_filename,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Character {self.name} (User: {self.user_id})>'


def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)

    with app.app_context():
        # Create all tables
        db.create_all()

        # Create indexes for better performance
        try:
            # These might already exist, so we wrap in try/except
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name)')
            # Chat indexes
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_chat_rooms_created_by ON chat_rooms(created_by)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_room_id ON chat_messages(room_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_room_members_room_id ON room_members(room_id)')
            db.engine.execute('CREATE INDEX IF NOT EXISTS idx_room_members_user_id ON room_members(user_id)')
        except Exception as e:
            print(f"Index creation note: {e}")

        # Create default "Allgemein" room if it doesn't exist
        if not ChatRoom.query.filter_by(name='Allgemein').first():
            default_room = ChatRoom(
                name='Allgemein',
                description='Öffentlicher Hauptraum für alle Spieler',
                created_by=1,  # Will be created by first user
                is_public=True
            )
            db.session.add(default_room)
            db.session.commit()
            print("Default 'Allgemein' room created!")

        print("Database initialized successfully!")


class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    password_hash = db.Column(db.String(255))  # Optional for private rooms
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)
    max_members = db.Column(db.Integer, default=50)

    # Relationships
    messages = db.relationship('ChatMessage', backref='room', lazy='dynamic', cascade='all, delete-orphan')
    members = db.relationship('RoomMember', backref='room', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Set password hash for private room"""
        if password:
            self.password_hash = generate_password_hash(password)
            self.is_public = False
        else:
            self.password_hash = None
            self.is_public = True

    def check_password(self, password):
        """Check password for private room"""
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return True  # Public room

    def get_member_count(self):
        """Get number of members in room"""
        return self.members.count()

    def is_member(self, user_id):
        """Check if user is member of room"""
        return self.members.filter_by(user_id=user_id).first() is not None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_public': self.is_public,
            'has_password': self.password_hash is not None,
            'member_count': self.get_member_count(),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<ChatRoom {self.name}>'


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message_type = db.Column(db.String(20), default='text')  # text, system, character_share
    message_data = db.Column(db.Text, nullable=True)  # JSON data for special message types

    def to_dict(self):
        result = {
            'id': self.id,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'username': self.author.username if self.author else 'Unknown',
            'message': self.message,
            'message_type': self.message_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

        # Parse message_data if available
        if self.message_data:
            try:
                import json
                parsed_data = json.loads(self.message_data)
                result.update(parsed_data)
            except (json.JSONDecodeError, TypeError):
                pass

        return result

    def __repr__(self):
        return f'<ChatMessage {self.id} in Room {self.room_id}>'


class RoomMember(db.Model):
    __tablename__ = 'room_members'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default='member')  # admin, moderator, member

    # Unique constraint to prevent duplicate memberships
    __table_args__ = (db.UniqueConstraint('room_id', 'user_id', name='unique_room_member'),)

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }

    def __repr__(self):
        return f'<RoomMember User {self.user_id} in Room {self.room_id}>'