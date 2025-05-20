import joblib
import os
import numpy as np
import pandas as pd
from app.models import TentativaLogin
from datetime import datetime, timedelta

# Caminhos dos arquivos
BASE_DIR = os.path.dirname(__file__)
MODELOS_DIR = os.path.join(BASE_DIR, 'ml_model', 'modelos')

modelo = joblib.load(os.path.join(MODELOS_DIR, 'modelo_random_forest.pkl'))
usuario_encoder = joblib.load(os.path.join(MODELOS_DIR, 'usuario_encoder.pkl'))
resultado_encoder = joblib.load(os.path.join(MODELOS_DIR, 'resultado_encoder.pkl'))

# IP -> número
def ip_para_int(ip):
    try:
        partes = list(map(int, ip.split('.')))
        return (partes[0] << 24) + (partes[1] << 16) + (partes[2] << 8) + partes[3]
    except:
        return 0

# Define a função principal verificar_anomalia, que recebe dois parâmetros: email e ip, representando a tentativa atual de login.
def verificar_anomalia(email, ip):
    ip_num = ip_para_int(ip)
    usuario_cod = usuario_encoder.transform([email])[0] if email in usuario_encoder.classes_ else 0

    X = pd.DataFrame([[ip_num, usuario_cod]], columns=['ip', 'usuario_cod'])
    pred = modelo.predict(X)[0]
    resultado = resultado_encoder.inverse_transform([pred])[0]

    return resultado
