import os
from flask import Flask # Importa a classe principal Flask, que é usada para criar a aplicação.
from flask_sqlalchemy import SQLAlchemy # Importa a extensão SQLAlchemy, que facilita a conexão com o banco de dados usando ORM (Object Relational Mapping).
from flask_login import LoginManager # Importa o LoginManager, que gerencia a autenticação de usuários, sessões e redirecionamentos.

db = SQLAlchemy() # Cria uma instância global do SQLAlchemy, que será usada em toda a aplicação para acessar o banco de dados.
login_manager = LoginManager() # Cria uma instância do LoginManager, que será usada para controlar o login dos usuários.
login_manager.login_view = 'main.login'  # Define a função create_app, usada para criar e configurar a aplicação Flask. Essa abordagem é chamada de Application Factory.

# Cria e configura a aplicação com banco de dados, login, e rotas.
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'sua_chave_secreta' # Define a chave secreta da aplicação

    # Caminho absoluto para o banco de dados
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'entregaplus.db') # Configura o caminho do banco de dados SQLite

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main
    app.register_blueprint(main)

    # Entrega a aplicação pronta para ser usada.
    return app
