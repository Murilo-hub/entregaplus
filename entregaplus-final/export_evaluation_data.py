import os
import pandas as pd
import logging
from app import create_app, db # Importa create_app e db do seu pacote 'app'
from app.models import TentativaLogin # Importa o modelo TentativaLogin
from config import Config # Importa sua classe de configuração

# Configuração básica de logging para o script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def export_logs_for_evaluation(output_filename='logs_avaliacao.csv', limit=500):
    """
    Exporta as últimas tentativas de login do banco de dados para um CSV para avaliação do ML.
    
    Args:
        output_filename (str): Nome do arquivo CSV de saída.
        limit (int): Número máximo de registros a exportar.
                     Considere exportar dados que não foram usados no treino do modelo,
                     ou um período de tempo distinto.
    """
    app = create_app(Config) # Cria uma instância da sua aplicação Flask
    with app.app_context(): # Entra no contexto da aplicação para acessar o DB
        logging.info("Conectando ao banco de dados para exportar logs de avaliação...")
        try:
            # Consulta as tentativas de login.
            # Pegaremos os 'limit' últimos registros.
            # Se você tiver um identificador para "dados de treino" vs "dados de avaliação"
            # no seu DB, este seria o lugar para filtrar.
            tentativas = TentativaLogin.query.order_by(TentativaLogin.timestamp.desc()).limit(limit).all()

            if not tentativas:
                logging.warning("Nenhuma tentativa de login encontrada no banco de dados para exportar.")
                return

            # Converte os objetos do SQLAlchemy para uma lista de dicionários
            data_for_df = []
            for t in tentativas:
                data_for_df.append({
                    'usuario': t.usuario,
                    'ip': t.ip,
                    'horario': t.timestamp.strftime('%Y-%m-%d %H:%M:%S'), # Formatar data para consistência
                    'resultado': t.resultado
                    # Inclua quaisquer outras colunas que seu modelo use como features, como 'dispositivo' se você as tiver
                })
            
            # Cria um DataFrame do pandas
            df = pd.DataFrame(data_for_df)

            # Define o caminho completo para o arquivo CSV de saída
            # Ele será salvo em 'app/ml_model/'
            ml_model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'ml_model')
            os.makedirs(ml_model_dir, exist_ok=True) # Garante que o diretório exista
            
            output_path = os.path.join(ml_model_dir, output_filename)
            
            # Salva o DataFrame como CSV
            df.to_csv(output_path, index=False)
            logging.info(f"Dados de avaliação exportados para '{output_path}' com {len(df)} registros.")

        except Exception as e:
            logging.error(f"Erro ao exportar dados para avaliação: {e}", exc_info=True)

if __name__ == '__main__':
    # Você pode ajustar o limite de registros aqui.
    # Ex: exportar os 500 registros mais recentes do seu DB.
    export_logs_for_evaluation(limit=500)