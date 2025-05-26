import pandas as pd
import joblib
import os
import sqlite3
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from datetime import datetime, timedelta

# Caminhos
base_path = os.path.dirname(__file__)  # .../app/ml_model
db_path = os.path.join(base_path, '..', 'database', 'entregaplus.db')
db_path = os.path.abspath(db_path)  # transforma em caminho absoluto
modelo_dir = os.path.join(base_path, 'ml_model', 'modelos')
os.makedirs(modelo_dir, exist_ok=True)

# Conecta ao banco de dados
# conn = sqlite3.connect(db_path)
# df = pd.read_sql_query("SELECT * FROM tentativas_login", conn)
# conn.close()

# Arquivo CSV de entrada
df = pd.read_csv('logs_treino.csv')
df['horario'] = pd.to_datetime(df['horario'])

# Conversões e pré-processamento
df['horario'] = pd.to_datetime(df['horario'])

def ip_para_int(ip):
    try:
        partes = list(map(int, ip.split('.')))
        return (partes[0] << 24) + (partes[1] << 16) + (partes[2] << 8) + partes[3]
    except:
        return 0

df['ip_num'] = df['ip'].apply(ip_para_int)

# Codificação de usuário
usuario_encoder = LabelEncoder()
df['usuario_cod'] = usuario_encoder.fit_transform(df['usuario'])

# Calcula tentativas inválidas nos últimos 2 minutos por (usuario + ip)
df = df.sort_values(by='horario')

tentativas_invalidas = []
for idx, row in df.iterrows():
    usuario = row['usuario']
    ip = row['ip']
    horario = row['horario']

    intervalo_inicio = horario - timedelta(minutes=2)
    cond = (
        (df['usuario'] == usuario) &
        (df['ip'] == ip) &
        (df['resultado'] == 'Credencial Inválida') &
        (df['horario'] >= intervalo_inicio) &
        (df['horario'] < horario)
    )
    tentativas_invalidas.append(df[cond].shape[0])

df['tentativas_invalidas'] = tentativas_invalidas

# Define a variável target
X = df[['ip_num', 'usuario_cod', 'tentativas_invalidas']]
y = df['resultado']

# Codifica o resultado
resultado_encoder = LabelEncoder()
y_encoded = resultado_encoder.fit_transform(y)

# Treina o modelo
modelo = RandomForestClassifier(n_estimators=100, random_state=42)
modelo.fit(X, y_encoded)

# Salva o modelo e os encoders
joblib.dump(modelo, os.path.join(modelo_dir, 'modelo_random_forest.pkl'))
joblib.dump(usuario_encoder, os.path.join(modelo_dir, 'usuario_encoder.pkl'))
joblib.dump(resultado_encoder, os.path.join(modelo_dir, 'resultado_encoder.pkl'))

print("Modelo treinado e salvo com sucesso!")
