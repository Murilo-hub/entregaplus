import joblib
import os
from datetime import datetime, timedelta
from .models import TentativaLogin
from . import db

base_path = os.path.dirname(__file__)
modelo_path = os.path.join(base_path, 'ml_model', 'modelos', 'modelo_random_forest.pkl')
usuario_encoder_path = os.path.join(base_path, 'ml_model', 'modelos', 'usuario_encoder.pkl')
resultado_encoder_path = os.path.join(base_path, 'ml_model', 'modelos', 'resultado_encoder.pkl')

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

    # Codificar usuário
    try:
        usuario_cod = usuario_encoder.transform([usuario])[0]
    except ValueError:
        usuario_cod = 0  # Caso seja um usuário novo não visto no treino

    # Hora atual
    hora = datetime.utcnow().hour

    # Contar tentativas inválidas nos últimos 2 minutos para o mesmo IP e usuário
    dois_minutos_atras = datetime.utcnow() - timedelta(minutes=2)
    tentativas_invalidas = TentativaLogin.query.filter_by(
        usuario=usuario,
        ip=ip,
        resultado='Credencial Inválida'
    ).filter(TentativaLogin.horario >= dois_minutos_atras).count()

    # Montar entrada
    entrada = [[ip_num, usuario_cod, hora, tentativas_invalidas]]

    # Fazer predição
    predicao = modelo.predict(entrada)
    resultado = resultado_encoder.inverse_transform(predicao)[0]

    return resultado  # Ex: 'Normal', 'Suspeito', 'Tentativa de Invasão', etc.
