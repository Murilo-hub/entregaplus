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
        module_logger.info("Modelos de ML carregados com sucesso.") # <<< ALTERADO para module_logger
    else:
        missing_files_msg = "Um ou mais arquivos de modelo não encontrados. Verifique os caminhos:"
        if not os.path.exists(modelo_path):
            missing_files_msg += f"\n - Modelo: {modelo_path} (NÃO ENCONTRADO)"
        if not os.path.exists(usuario_encoder_path):
            missing_files_msg += f"\n - Usuario Encoder: {usuario_encoder_path} (NÃO ENCONTRADO)"
        if not os.path.exists(resultado_encoder_path):
            missing_files_msg += f"\n - Resultado Encoder: {resultado_encoder_path} (NÃO ENCONTRADO)"
        module_logger.error(missing_files_msg) # <<< ALTERADO para module_logger
except Exception as e:
    # Adicionar exc_info=True para logar o traceback completo do erro
    module_logger.error(f"Erro crítico ao carregar modelo de ML ou encoders: {e}", exc_info=True) # <<< ALTERADO para module_logger

def verificar_anomalia(usuario_email, ip_address_para_registro):
    if not model_loaded_successfully:
        module_logger.warning("Modelo de ML não carregado. Classificando tentativa como 'Normal' por padrão.")
        return 'Normal'
    
    try:
        if usuario_email in usuario_encoder.classes_:
            usuario_cod = usuario_encoder.transform([usuario_email])[0]
        else:
            usuario_cod = -1
            module_logger.info(f"Usuário '{usuario_email}' não visto no treino do encoder. Usando código {usuario_cod}.")
    except Exception as e:
        module_logger.error(f"Erro ao codificar usuário '{usuario_email}': {e}", exc_info=True)
        usuario_cod = -1

    # Calcula tentativas inválidas nos últimos 2 minutos
    agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
    dois_minutos_atras = agora - timedelta(minutes=2)

    try:
        tentativas_invalidas_usuario = TentativaLogin.query.filter(
            TentativaLogin.usuario == usuario_email,
            TentativaLogin.resultado == 'Credencial Inválida',
            TentativaLogin.timestamp >= dois_minutos_atras,
            TentativaLogin.timestamp < agora
        ).count()
    except Exception as e:
        module_logger.error(f"Erro ao consultar TentativasLogin para {usuario_email}: {e}", exc_info=True)
        tentativas_invalidas_usuario = 0

    entrada_features = pd.DataFrame(
        [[usuario_cod, tentativas_invalidas_usuario]],
        columns=['usuario_cod', 'tentativas_invalidas_usuario']
    )

    try:
        predicao_codificada = modelo.predict(entrada_features)
        resultado_final = resultado_encoder.inverse_transform(predicao_codificada)[0]
        from flask import current_app 
        if current_app:
             current_app.logger.info(f"Predição ML para {usuario_email} (IP: {ip_address_para_registro}): {resultado_final} (Features: {entrada_features.to_dict('records')})")
        else:
            module_logger.info(f"Predição ML para {usuario_email} (IP: {ip_address_para_registro}): {resultado_final} (Features: {entrada_features.to_dict('records')})")

    except Exception as e:
        from flask import current_app 
        if current_app:
            current_app.logger.error(f"Erro durante a predição do modelo para {usuario_email}: {e}. Features: {entrada_features.to_dict('records')}", exc_info=True)
        else:
            module_logger.error(f"Erro durante a predição do modelo para {usuario_email}: {e}. Features: {entrada_features.to_dict('records')}", exc_info=True)
        resultado_final = 'Normal'

    return resultado_final