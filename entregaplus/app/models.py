from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(11), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    login_attempts = db.relationship('LoginAttempt', backref='user', lazy=True)

class LoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ip = db.Column(db.String(100))
    resultado = db.Column(db.String(20))  # Normal ou Suspeito
