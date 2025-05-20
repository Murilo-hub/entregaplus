from . import db
from flask_login import UserMixin
from datetime import datetime

# Representa um usuário autenticado no sistema.
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(11), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Armazena logs de tentativas de login, com IP, data, resultado e usuário.
class TentativaLogin(db.Model):
    __tablename__ = 'tentativas_login'

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(100))
    horario = db.Column(db.DateTime, default=datetime.utcnow)
    resultado = db.Column(db.String(30), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)