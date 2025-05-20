import pickle
import os

modelo_path = os.path.join(os.path.dirname(__file__), 'ml_model', 'modelo_login.pkl')
with open(modelo_path, 'rb') as f:
    modelo = pickle.load(f)

def verificar_anomalia(email, ip, senha):
    # Aqui simplificamos: usamos apenas IP como dado numérico
    ip_convertido = sum([int(x) for x in ip.split('.')])  # Exemplo simples
    senha_len = len(senha)

    entrada = [[ip_convertido, senha_len]]
    predicao = modelo.predict(entrada)

    return 'Normal' if predicao[0] == 0 else 'Suspeito'
