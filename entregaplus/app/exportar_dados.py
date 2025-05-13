from app import create_app, db
from app.models import LoginAttempt

# Cria a aplicação com o contexto apropriado
app = create_app()

with app.app_context():
    # Consulta todas as tentativas de login
    tentativas = LoginAttempt.query.all()

    # Abre o arquivo de saída
    with open('tentativas_login.txt', 'w', encoding='utf-8') as f:
        for tentativa in tentativas:
            f.write(f"ID: {tentativa.id}, User ID: {tentativa.usuario_id}, IP: {tentativa.ip}, Resultado: {tentativa.resultado}\n")

print("Dados exportados com sucesso para 'tentativas_login.txt'")
