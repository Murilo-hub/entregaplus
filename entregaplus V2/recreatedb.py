# recreatedb.py
import os
import logging
from app import create_app, db
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
db_uri = Config.SQLALCHEMY_DATABASE_URI

if not db_uri.startswith('sqlite:///'):
    logging.error("Este script é configurado apenas para recriar bancos de dados SQLite.")
    exit(1)

if db_uri.startswith('sqlite:///./') or db_uri.startswith('sqlite:///..'):
    db_path = db_uri.replace('sqlite:///', '')
    if not os.path.isabs(db_path):
        project_root = os.path.dirname(os.path.abspath(Config.__file__)) if hasattr(Config, '__file__') else os.getcwd()
        db_path = os.path.join(project_root, db_path)

else:
    db_path = db_uri.replace('sqlite:///', '')

db_dir = os.path.dirname(db_path)

if not os.path.exists(db_dir):
    try:
        os.makedirs(db_dir)
        logging.info(f"Diretório {db_dir} criado.")
    except Exception as e:
        logging.error(f"Erro ao criar o diretório {db_dir}: {e}")
        exit(1)

if os.path.exists(db_path):
    try:
        os.remove(db_path)
        logging.info(f"Banco de dados antigo '{db_path}' removido com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao remover o banco de dados '{db_path}': {e}")
else:
    logging.info(f"Nenhum banco de dados antigo encontrado em '{db_path}'. Criando novo banco...")

app = create_app(Config)

with app.app_context():
    try:
        db.create_all()
        logging.info(f"Novo banco de dados '{db_path}' criado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao criar o banco de dados '{db_path}': {e}")