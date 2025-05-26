from datetime import datetime, timedelta
from .models import TentativaLogin
from . import db
import pandas as pd
import joblib
import os

base_path = os.path.dirname(__file__)
modelo_path = os.path.join(base_path, 'ml_model', 'modelos', 'modelo_random_forest.pkl')
usuario_encoder_path = os.path.join(base_path, 'ml_model', 'modelos', 'usuario_encoder.pkl')
resultado_encoder_path = os.path.join(base_path, 'ml_model', 'modelos', 'resultado_encoder.pkl')

# Carrega o modelo e os encoders
modelo = joblib.load(modelo_path)
usuario_encoder = joblib.load(usuario_encoder_path)
resultado_encoder = joblib.load(resultado_encoder_path)

def ip_para_int(ip):
    try:
        partes = list(map(int, ip.split('.')))
        return (partes[0] << 24) + (partes[1] << 16) + (partes[2] << 8) + partes[3]
    except:
        return 0

def verificar_anomalia(usuario, ip):
    ip_num = ip_para_int(ip)

    try:
        usuario_cod = usuario_encoder.transform([usuario])[0]
    except ValueError:
        usuario_cod = 0

    # Calcula tentativas inválidas nos últimos 2 minutos
    agora = datetime.utcnow()
    dois_minutos_atras = agora - timedelta(minutes=2)

    tentativas_invalidas = TentativaLogin.query.filter(
        TentativaLogin.usuario == usuario,
        TentativaLogin.ip == ip,
        TentativaLogin.resultado == 'Credencial Inválida',
        TentativaLogin.horario >= dois_minutos_atras,
        TentativaLogin.horario < agora
    ).count()

    entrada_df = pd.DataFrame(
        [[ip_num, usuario_cod, tentativas_invalidas]],
        columns=['ip_num', 'usuario_cod', 'tentativas_invalidas']
    )

    predicao = modelo.predict(entrada_df)
    resultado = resultado_encoder.inverse_transform(predicao)[0]

    return resultado
