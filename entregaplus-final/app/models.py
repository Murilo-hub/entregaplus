from . import db
from flask_login import UserMixin
from datetime import datetime
import pytz

def horario_brasilia():
    fuso_brasilia = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_brasilia)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    senha = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"

# Armazena logs de tentativas de login, com IP, data, resultado e usuário.
class TentativaLogin(db.Model):
    __tablename__ = 'tentativas_login'
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(150), nullable=False, index=True)
    ip = db.Column(db.String(45)) # Mantém o IP para registro
    timestamp = db.Column(db.DateTime, default=horario_brasilia, nullable=False, index=True)
    resultado = db.Column(db.String(50), nullable=False) # Ex: Normal, Credencial Inválida, Suspeito

    def __repr__(self):
        return f"<TentativaLogin {self.usuario} - {self.resultado} em {self.timestamp}>"