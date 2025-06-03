# app/ml_model/train_model.py
import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from datetime import datetime, timedelta

base_ml_path = os.path.dirname(__file__)  # .../app/ml_model


modelo_dir = os.path.join(base_ml_path, 'modelos')
os.makedirs(modelo_dir, exist_ok=True)

# ---- Carregamento de Dados ----

csv_path = os.path.join(base_ml_path, 'logs_treino.csv')
try:
    df = pd.read_csv(csv_path)
except FileNotFoundError:
    print(f"Erro: Arquivo 'logs_treino.csv' não encontrado em {base_ml_path}.")
    print("Certifique-se de que o arquivo de treino existe e o caminho está correto.")
    exit(1)


if 'horario' not in df.columns:
    print("Erro: A coluna 'horario' é necessária no CSV para calcular 'tentativas_invalidas_usuario'.")
    exit(1)
try:
    df['horario'] = pd.to_datetime(df['horario'])
except Exception as e:
    print(f"Erro ao converter a coluna 'horario' para datetime: {e}")
    exit(1)

# ---- Engenharia de Features ----

usuario_encoder = LabelEncoder()
df['usuario_cod'] = usuario_encoder.fit_transform(df['usuario'])


df = df.sort_values(by='horario').reset_index(drop=True)

tentativas_invalidas_lista = []
for idx, row in df.iterrows():
    usuario_atual = row['usuario']
    horario_atual = row['horario']
    
    
    intervalo_inicio = horario_atual - timedelta(minutes=2)
    

    condicoes = (
        (df.loc[:idx-1, 'usuario'] == usuario_atual) &
        (df.loc[:idx-1, 'resultado'] == 'Credencial Inválida') & 
        (df.loc[:idx-1, 'horario'] >= intervalo_inicio) &
        (df.loc[:idx-1, 'horario'] < horario_atual) 
    )
    contagem = df.loc[:idx-1][condicoes].shape[0]
    tentativas_invalidas_lista.append(contagem)

df['tentativas_invalidas_usuario'] = tentativas_invalidas_lista

# ---- Preparação para Treinamento ----

X = df[['usuario_cod', 'tentativas_invalidas_usuario']]
y = df['resultado']


resultado_encoder = LabelEncoder()
y_encoded = resultado_encoder.fit_transform(y)

# ---- Treinamento do Modelo ----

print(f"Classes encontradas no 'resultado' para o encoder: {resultado_encoder.classes_}")
print(f"Shape de X: {X.shape}, Shape de y_encoded: {y_encoded.shape}")
if X.empty:
    print("Erro: DataFrame de features X está vazio. Verifique o pré-processamento e o CSV.")
    exit(1)

modelo = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced') # Adicionado class_weight
try:
    modelo.fit(X, y_encoded)
    print("Modelo treinado com sucesso!")
except Exception as e:
    print(f"Erro durante o treinamento do modelo: {e}")
    exit(1)

# ---- Salvando o Modelo e Encoders ----

try:
    joblib.dump(modelo, os.path.join(modelo_dir, 'modelo_random_forest.pkl'))
    joblib.dump(usuario_encoder, os.path.join(modelo_dir, 'usuario_encoder.pkl'))
    joblib.dump(resultado_encoder, os.path.join(modelo_dir, 'resultado_encoder.pkl'))
    print(f"Modelo e encoders salvos com sucesso em '{modelo_dir}'.")
except Exception as e:
    print(f"Erro ao salvar modelo ou encoders: {e}")