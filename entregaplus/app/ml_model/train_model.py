# train_model.py
import random
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Função para converter IP string para número simples
def ip_para_numero(ip):
    return sum([int(x) for x in ip.split('.')])

# Gerar dados fictícios
X = []
y = []

for _ in range(500):
    ip = f"{random.randint(100, 200)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    senha = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=random.randint(6, 12)))
    
    ip_convertido = ip_para_numero(ip)
    senha_len = len(senha)

    # Regra fictícia: se IP > 600 e senha curta, marcar como suspeito
    rotulo = 1 if ip_convertido > 600 and senha_len <= 7 else 0

    X.append([ip_convertido, senha_len])
    y.append(rotulo)

# Dividir e treinar
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

modelo = RandomForestClassifier(n_estimators=100)
modelo.fit(X_train, y_train)

# Salvar o modelo
with open('app/ml_model/modelo_login.pkl', 'wb') as f:
    pickle.dump(modelo, f)

print("Modelo treinado e salvo com sucesso.")
