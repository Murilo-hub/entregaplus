# app/detectors.py
from datetime import datetime, timedelta
import pytz
from .models import TentativaLogin
from . import db
import pandas as pd
import joblib
import os
import logging

module_logger = logging.getLogger(__name__)

base_path = os.path.dirname(__file__)
# Ajuste o caminho conforme a sua estrutura de pastas se os modelos estiverem em outro lugar
modelo_path = os.path.join(base_path, 'ml_model', 'modelos', 'modelo_random_forest.pkl')
usuario_encoder_path = os.path.join(base_path, 'ml_model', 'modelos', 'usuario_encoder.pkl')
resultado_encoder_path = os.path.join(base_path, 'ml_model', 'modelos', 'resultado_encoder.pkl')

# Carrega o modelo e os encoders
model_loaded_successfully = False
modelo = None
usuario_encoder = None
resultado_encoder = None

try:
    if os.path.exists(modelo_path) and \
       os.path.exists(usuario_encoder_path) and \
       os.path.exists(resultado_encoder_path):
        modelo = joblib.load(modelo_path)
        usuario_encoder = joblib.load(usuario_encoder_path)
        resultado_encoder = joblib.load(resultado_encoder_path)
        model_loaded_successfully = True
        module_logger.info("Modelos de ML carregados com sucesso.")
    else:
        missing_files_msg = "Um ou mais arquivos de modelo não encontrados. Verifique os caminhos:"
        if not os.path.exists(modelo_path): missing_files_msg += f" {modelo_path}"
        if not os.path.exists(usuario_encoder_path): missing_files_msg += f" {usuario_encoder_path}"
        if not os.path.exists(resultado_encoder_path): missing_files_msg += f" {resultado_encoder_path}"
        module_logger.warning(missing_files_msg)
except Exception as e:
    module_logger.error(f"Erro ao carregar modelos de ML: {e}", exc_info=True)


def verificar_anomalia(usuario_id, usuario_email, ip_address_para_registro):
    if not model_loaded_successfully:
        module_logger.warning("Modelo de ML não carregado. Retornando 'Normal' por padrão.")
        return 'Normal' # Retorna 'Normal' se o modelo não puder ser carregado

    usuario_cod = -1 # Valor padrão para usuários não encontrados no encoder
    try:
        # Tenta codificar o e-mail do usuário. Se o e-mail não foi visto durante o treino,
        # o inverse_transform pode falhar. Consideramos isso uma falha de "usuário não reconhecido".
        if usuario_email in usuario_encoder.classes_:
            usuario_cod = usuario_encoder.transform([usuario_email])[0]
        else:
            module_logger.warning(f"Usuário '{usuario_email}' não encontrado no encoder. Pode ser um novo usuário ou um erro.")
            # Você pode decidir como lidar com isso:
            # - Usar um valor default (como -1)
            # - Tentar prever como 'Credencial Inválida' (se o modelo foi treinado para isso)
            # Para este projeto, manteremos -1 e veremos como o modelo se comporta.
    except Exception as e:
        module_logger.error(f"Erro ao codificar o email do usuário '{usuario_email}': {e}", exc_info=True)
        usuario_cod = -1 # Garante que haja um valor caso o encoder falhe

    tentativas_invalidas_usuario = 0
    try:
        fuso_brasilia = pytz.timezone('America/Sao_Paulo') # Certifique-se de que o fuso horário é o mesmo que o do models.py
        agora = datetime.now(fuso_brasilia)
        
        # --- ALTERAÇÃO IMPORTANTE AQUI ---
        # A janela de tempo deve ser a mesma usada no train_model.py para a feature 'tentativas_invalidas_usuario'
        # e a mesma que você usou na regra manual no routes.py para consistência.
        JANELA_TEMPO_MINUTOS = 5 # Ajuste conforme a janela definida no train_model.py e routes.py
        
        tempo_atras = agora - timedelta(minutes=JANELA_TEMPO_MINUTOS)

        # Pega as tentativas de login do USUÁRIO (pelo email) dentro da janela de tempo
        # que tiveram resultado 'Credencial Inválida'
        tentativas_invalidas_usuario = TentativaLogin.query.filter(
            TentativaLogin.usuario == usuario_email,
            TentativaLogin.resultado == 'Credencial Inválida',
            TentativaLogin.timestamp >= tempo_atras,
            TentativaLogin.timestamp < agora # Não inclui a tentativa atual, pois ela ainda não foi persistida
                                             # ou se você chamar APÓS a persistência, ela será incluída.
                                             # Com a lógica do routes.py, é chamada ANTES.
        ).count()
    except Exception as e:
        module_logger.error(f"Erro ao consultar TentativasLogin para {usuario_email}: {e}", exc_info=True)
        tentativas_invalidas_usuario = 0

    entrada_features = pd.DataFrame(
        [[usuario_cod, tentativas_invalidas_usuario]],
        columns=['usuario_cod', 'tentativas_invalidas_usuario']
    )

    resultado_final = 'Normal' # Padrão
    try:
        predicao_codificada = modelo.predict(entrada_features)
        resultado_final = resultado_encoder.inverse_transform(predicao_codificada)[0]
        
        # Log mais detalhado para depuração
        if 'current_app' in globals() and current_app: # Verifica se está no contexto Flask
             current_app.logger.info(f"Predição ML para {usuario_email} (IP: {ip_address_para_registro}): {resultado_final} (Features: {entrada_features.to_dict('records')})")
        else:
            module_logger.info(f"Predição ML para {usuario_email} (IP: {ip_address_para_registro}): {resultado_final} (Features: {entrada_features.to_dict('records')})")

    except Exception as e:
        # Se ocorrer um erro na predição, loga e retorna 'Normal' ou um fallback seguro.
        if 'current_app' in globals() and current_app: # Verifica se está no contexto Flask
            current_app.logger.error(f"Erro durante a predição do modelo para {usuario_email}: {e}. Features: {entrada_features.to_dict('records')}", exc_info=True)
        else:
            module_logger.error(f"Erro durante a predição do modelo para {usuario_email}: {e}. Features: {entrada_features.to_dict('records')}", exc_info=True)
        resultado_final = 'Normal' # Falha segura

    return resultado_final