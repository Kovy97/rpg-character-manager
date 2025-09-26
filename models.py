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
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to characters
    characters = db.relationship('Character', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
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
        except Exception as e:
            print(f"Index creation note: {e}")

        print("Database initialized successfully!")