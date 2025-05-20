import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
# Importa o algoritmo de machine learning RandomForestClassifier, a função de divisão dos dados train_test_splito gerador de relatório de desempenho
# classification_report, e a biblioteca joblib, usada para salvar o modelo treinado em disco.

# Carregar dados
df = pd.read_csv('logs_login.csv')

# Pré-processar IP (transformar IP em número)
def ip_para_int(ip):
    try:
        partes = list(map(int, ip.split('.')))
        return (partes[0] << 24) + (partes[1] << 16) + (partes[2] << 8) + partes[3]
    except:
        return 0

df['ip_num'] = df['ip'].apply(ip_para_int)

# Codificar o usuário
usuario_encoder = LabelEncoder()
df['usuario_cod'] = usuario_encoder.fit_transform(df['usuario'])

# Codificar o resultado (alvo)
resultado_encoder = LabelEncoder()
df['resultado_cod'] = resultado_encoder.fit_transform(df['resultado'])

# Selecionar features e alvo
X = df[['ip_num', 'usuario_cod']]
y = df['resultado_cod']

# Dividir treino/teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Treinar modelo
modelo = RandomForestClassifier(n_estimators=100, random_state=42)
modelo.fit(X_train, y_train)

# Avaliar acurácia
acc = modelo.score(X_test, y_test)
print(f'Acurácia: {acc:.2f}')

# Salvar modelo e encoders
os.makedirs('app/ml_model/modelos', exist_ok=True)
joblib.dump(modelo, 'app/ml_model/modelos/modelo_random_forest.pkl')
joblib.dump(usuario_encoder, 'app/ml_model/modelos/usuario_encoder.pkl')
joblib.dump(resultado_encoder, 'app/ml_model/modelos/resultado_encoder.pkl')
