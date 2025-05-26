import os
import logging
from app import create_app, db

# Configurações de logging
logging.basicConfig(level=logging.INFO)

# Caminho absoluto para o banco de dados
db_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'database')
db_path = os.path.join(db_dir, 'entregaplus.db')

# Verifica se o diretório existe, caso contrário, cria
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
    logging.info(f"Diretório {db_dir} criado.")

# Remove o banco de dados antigo, se existir
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        logging.info("Banco de dados antigo removido com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao remover o banco de dados: {e}")
else:
    logging.info("Nenhum banco de dados antigo encontrado. Criando novo banco...")

# Cria a aplicação e o contexto
app = create_app()

with app.app_context():
    try:
        db.create_all()  # Cria todas as tabelas no banco de dados
        logging.info("Novo banco de dados criado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao criar o banco de dados: {e}")
