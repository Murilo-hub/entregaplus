# recreatedb.py
import os
import logging
from app import create_app, db # Certifique-se de que 'app' é o pacote Flask e tem create_app e db
from config import Config
from app.models import User # Importe o modelo User
from werkzeug.security import generate_password_hash # Para hashear senhas

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
db_uri = Config.SQLALCHEMY_DATABASE_URI

if not db_uri.startswith('sqlite:///'):
    logging.error("Este script é configurado apenas para recriar bancos de dados SQLite.")
    exit(1)

# Extrai o caminho do arquivo do banco de dados
if db_uri.startswith('sqlite:///./') or db_uri.startswith('sqlite:///..'):
    db_path = db_uri.replace('sqlite:///', '')
    if not os.path.isabs(db_path):
        # Tenta obter o caminho raiz do projeto de forma mais robusta
        try:
            # Assumimos que o config.py está na raiz ou em um lugar previsível
            project_root = os.path.dirname(os.path.abspath(__file__))
            # Subir um nível se este script estiver em 'V2/'
            if os.path.basename(project_root) == 'V2':
                project_root = os.path.dirname(project_root)
            # Reajustar o caminho do DB com base na raiz do projeto
            db_path = os.path.join(project_root, db_path)
        except Exception as e:
            logging.warning(f"Não foi possível determinar o project_root de forma robusta: {e}. Usando os.getcwd().")
            project_root = os.getcwd()
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
        logging.error(f"Erro ao remover o banco de dados: {e}")
        exit(1)

# Cria a aplicação Flask no contexto para que o SQLAlchemy funcione
app = create_app(Config)
with app.app_context():
    db.create_all()
    logging.info("Tabelas do banco de dados recriadas com sucesso.")

    # --- Criação de Usuários ---

    # Usuário Administrador
    admin_email = os.environ.get('ADMIN_EMAIL') or 'admin@admin.com'
    admin_senha = os.environ.get('ADMIN_PASSWORD') or 'admin123' # Mude para uma senha forte em produção!
    admin_nome = os.environ.get('ADMIN_NAME') or 'Administrador'

    # Verifica se o admin já existe (para evitar duplicidade em execuções múltiplas)
    if not User.query.filter_by(email=admin_email).first():
        hashed_admin_senha = generate_password_hash(admin_senha, method='pbkdf2:sha256')
        admin_user = User(
            nome=admin_nome,
            cpf='000.000.000-00', # CPF fictício para o admin
            email=admin_email,
            senha=hashed_admin_senha,
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        logging.info(f"Usuário administrador '{admin_email}' criado com sucesso.")
    else:
        logging.info(f"Usuário administrador '{admin_email}' já existe. Ignorando a criação.")

    # Usuário Comum (Exemplo)
    common_email = os.environ.get('COMMON_EMAIL') or 'user@user.com'
    common_senha = os.environ.get('COMMON_PASSWORD') or 'user123' # Mude para uma senha forte em produção!
    common_nome = os.environ.get('COMMON_NAME') or 'Usuário Comum'

    if not User.query.filter_by(email=common_email).first():
        hashed_common_senha = generate_password_hash(common_senha, method='pbkdf2:sha256')
        common_user = User(
            nome=common_nome,
            cpf='111.111.111-11', # CPF fictício
            email=common_email,
            senha=hashed_common_senha,
            is_admin=False
        )
        db.session.add(common_user)
        db.session.commit()
        logging.info(f"Usuário comum '{common_email}' criado com sucesso.")
    else:
        logging.info(f"Usuário comum '{common_email}' já existe. Ignorando a criação.")

logging.info("Processo de recriação do banco de dados e criação de usuários concluído.")