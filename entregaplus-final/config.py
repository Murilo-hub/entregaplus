import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Classe de configuração base."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-super-segura-padrao-para-desenvolvimento'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app', 'database', 'entregaplus.db')
    DEBUG = os.environ.get('FLASK_DEBUG') == '1'