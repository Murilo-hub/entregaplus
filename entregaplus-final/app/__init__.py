import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime

db = SQLAlchemy() # Cria uma instância global do SQLAlchemy, que será usada em toda a aplicação para acessar o banco de dados.
login_manager = LoginManager() # Cria uma instância do LoginManager, que será usada para controlar o login dos usuários.
login_manager.login_view = 'main.login'  # Define a função create_app, usada para criar e configurar a aplicação Flask. Essa abordagem é chamada de Application Factory.
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

# Cria e configura a aplicação com banco de dados, login, e rotas.
def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)  # Carrega as configurações da classe de configuração passada como argumento.

    db.init_app(app)  # Inicializa o SQLAlchemy com a aplicação Flask.
    login_manager.init_app(app)  # Inicializa o LoginManager com a aplicação Flask.

    from .models import User  # Importa o modelo User para o gerenciamento de usuários.

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.utcnow().year}

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/entregaplus.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('EntregaPlus startup')

    return app