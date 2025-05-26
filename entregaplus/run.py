from app import create_app #Importa a função de criação da app Flask.

app = create_app() # Cria a aplicação usando a configuração padrão.

if __name__ == '__main__': # Define o ponto de entrada do script.
    app.run(debug=True) # Inicia o servidor com modo de depuração ativo.