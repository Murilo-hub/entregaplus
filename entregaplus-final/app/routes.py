# app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from .models import User, TentativaLogin
from . import db
from .utils import get_user_ip
from .detectors import verificar_anomalia
from .detectors import modelo, resultado_encoder, usuario_encoder, model_loaded_successfully # Importa os modelos e encoders
from flask_login import login_user, logout_user, login_required, current_user
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz # Importar pytz
import os
import logging
import pandas as pd
import joblib
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report # <-- Necessário para as métricas ML
from sklearn.preprocessing import LabelEncoder # <-- Necessário se seus encoders não foram salvos diretamente e precisar refazer o LabelEncoder

main = Blueprint('main', __name__)

# Define a rota, que renderiza o arquivo HTML index.html (ex: uma página de boas-vindas ou login).
@main.route('/')
def home():
    return redirect(url_for('main.public_home'))

# Define a rota /login para aceitar apenas requisições POST, geralmente de formulários de login.
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        ip = get_user_ip()

        if email:
            email = email.lower().strip()

        user = User.query.filter_by(email=email).first()
        resultado_final_para_log = 'Credencial Inválida' # Valor padrão para o log e histórico

        if user:
            # Usuário encontrado
            if check_password_hash(user.senha, senha):
                # Login bem-sucedido
                login_user(user)
                resultado_final_para_log = 'Normal'
                flash('Login realizado com sucesso!', 'success')
                current_app.logger.info(f"Login bem-sucedido para usuário: {email} do IP: {ip}")
                
                # Registra a tentativa de login bem-sucedida
                nova_tentativa = TentativaLogin(
                    usuario=email,
                    ip=ip,
                    resultado='Normal' # Registra como Normal
                )
                # ATENÇÃO: Atribuir usuario_id APÓS a criação do objeto
                nova_tentativa.usuario_id = user.id 
                
                db.session.add(nova_tentativa)
                db.session.commit()
                return redirect(url_for('main.dashboard'))
            else:
                # Senha incorreta para um usuário existente
                current_app.logger.warning(f"Falha de login (senha incorreta) para usuário: {email} do IP: {ip}")

                # --- Lógica para o status "Suspeito" por 3 tentativas falhas ---
                fuso_brasilia = pytz.timezone('America/Sao_Paulo')
                agora = datetime.now(fuso_brasilia)
                # Defina uma janela de tempo para considerar as tentativas falhas (ex: últimos 5 minutos)
                JANELA_TEMPO_MINUTOS = 5 # Consistente com detectors.py e train_model.py
                cinco_minutos_atras = agora - timedelta(minutes=JANELA_TEMPO_MINUTOS)

                tentativas_recentes_falhas = TentativaLogin.query.filter(
                    TentativaLogin.usuario == email,
                    TentativaLogin.resultado == 'Credencial Inválida', # Contamos apenas as falhas de senha
                    TentativaLogin.timestamp >= cinco_minutos_atras
                ).count()

                # Adiciona a tentativa atual (que é uma falha de senha) à contagem
                tentativas_recentes_falhas += 1 
                
                # Se 3 ou mais tentativas falhas (em JANELA_TEMPO_MINUTOS) para um email existente, é Suspeito
                if tentativas_recentes_falhas >= 3:
                    resultado_final_para_log = 'Suspeito'
                    flash('Tentativas de login suspeitas detectadas. Sua conta pode estar sob ataque.', 'danger')
                    current_app.logger.warning(f"Login SUSPEITO para usuário: {email} devido a múltiplas senhas incorretas.")
                else:
                    resultado_final_para_log = 'Credencial Inválida'
                    flash('Credenciais inválidas. Verifique seu e-mail e senha.', 'danger')
                    
                # Aqui você chama o ML para ver se há outras anomalias além da regra das 3 tentativas.
                # O resultado do ML pode reforçar ou encontrar outros tipos de "Suspeito"
                # mas a regra de 3 tentativas tem precedência para esse tipo específico de "Suspeito".
                status_anomalia_ml = verificar_anomalia(user.id, user.email, ip)
                
                # Se a regra das 3 tentativas NÃO classificou como suspeito, mas o ML classificou,
                # podemos considerar a predição do ML.
                if resultado_final_para_log != 'Suspeito' and status_anomalia_ml == 'Suspeito':
                     resultado_final_para_log = 'Suspeito'
                     flash('Tentativas de login anômalas detectadas pelo sistema de segurança. Por favor, verifique seus dados.', 'danger')
                     current_app.logger.warning(f"Login classificado como SUSPEITO pelo ML para usuário: {email}.")

        else:
            # Usuário não encontrado
            current_app.logger.warning(f"Tentativa de login com email inexistente: {email} do IP: {ip}")
            resultado_final_para_log = 'Credencial Inválida'
            flash('Credenciais inválidas. Verifique seu e-mail e senha.', 'danger')
            # Não é necessário chamar verificar_anomalia aqui, pois não há um user.id associado.
            # O status de "email inexistente" é sempre "Credencial Inválida".

        # Registra a tentativa no banco de dados.
        # Se user for None (email inexistente), passe None para usuario_id.
        user_id_for_log = user.id if user else None
        
        nova_tentativa = TentativaLogin(
            usuario=email,
            ip=ip,
            resultado=resultado_final_para_log
        )
        # ATENÇÃO: Atribuir usuario_id APÓS a criação do objeto
        if user_id_for_log is not None:
            nova_tentativa.usuario_id = user_id_for_log 
        
        db.session.add(nova_tentativa)
        db.session.commit()

        return render_template('login.html')

    return render_template('login.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('main.login'))

@main.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        email = request.form['email']
        senha = request.form['senha']

        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado. Por favor, use outro e-mail.', 'danger')
            return redirect(url_for('main.cadastro'))

        hashed_senha = generate_password_hash(senha, method='pbkdf2:sha256')
        novo_user = User(nome=nome, cpf=cpf, email=email, senha=hashed_senha)

        try:
            db.session.add(novo_user)
            db.session.commit()
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            current_app.logger.info(f"Novo usuário cadastrado: {email}")
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao cadastrar usuário {email}: {e}")
            flash('Ocorreu um erro ao realizar o cadastro. Tente novamente.', 'danger')
            return redirect(url_for('main.cadastro'))
        
    return render_template('cadastro.html')

@main.route('/home')
def public_home():
    return render_template('home.html')

@main.route('/servicos')
def servicos():
    return render_template('servicos.html')

@main.route('/contato')
def contato():
    return render_template('contato.html')

# Rota que exibe um HTML com todas as tentativas de login.
@main.route('/tentativas')
@login_required
def ver_tentativas():
    if not current_user.is_admin:
        flash("Acesso restrito a administradores!", "danger")
        return redirect(url_for("main.dashboard"))

    page = request.args.get('page', 1, type=int)
    per_page = 20
    tentativas = TentativaLogin.query.order_by(TentativaLogin.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('tentativas.html', tentativas=tentativas)


# Adicione ou ajuste esta rota para exibir as métricas de ML
@main.route('/metricas_ml')
@login_required
def metricas_ml():
    if not current_user.is_admin:
        flash("Acesso restrito a administradores para visualizar métricas de ML!", "danger")
        return redirect(url_for("main.dashboard"))

    metrics = {}
    try:
        # Caminhos para o modelo e encoders
        base_ml_path = os.path.join(current_app.root_path, 'ml_model') # caminho para a pasta ml_model
        modelo_dir = os.path.join(base_ml_path, 'modelos')

        modelo_path = os.path.join(modelo_dir, 'modelo_random_forest.pkl')
        usuario_encoder_path = os.path.join(modelo_dir, 'usuario_encoder.pkl')
        resultado_encoder_path = os.path.join(modelo_dir, 'resultado_encoder.pkl')
        logs_avaliacao_path = os.path.join(base_ml_path, 'logs_avaliacao.csv')

        # 1. Carregar modelo e encoders
        if not (os.path.exists(modelo_path) and
                os.path.exists(usuario_encoder_path) and
                os.path.exists(resultado_encoder_path)):
            flash("Arquivos de modelo ou encoders não encontrados. Treine o modelo primeiro.", "warning")
            current_app.logger.warning("Tentativa de acessar métricas ML sem arquivos de modelo/encoders.")
            return render_template('metricas_ml.html', metrics=metrics, error_message="Arquivos de modelo ausentes.")

        modelo = joblib.load(modelo_path)
        usuario_encoder = joblib.load(usuario_encoder_path)
        resultado_encoder = joblib.load(resultado_encoder_path)

        # 2. Carregar dados de avaliação
        if not os.path.exists(logs_avaliacao_path):
            flash("Arquivo 'logs_avaliacao.csv' não encontrado.", "warning")
            current_app.logger.warning(f"Arquivo de avaliação não encontrado em: {logs_avaliacao_path}")
            return render_template('metricas_ml.html', metrics=metrics, error_message="CSV de avaliação ausente.")

        df_avaliacao = pd.read_csv(logs_avaliacao_path)

        if df_avaliacao.empty:
            flash("O arquivo 'logs_avaliacao.csv' está vazio. Nenhuma métrica pode ser calculada.", "info")
            current_app.logger.info("CSV de avaliação vazio. Nenhuma métrica calculada.")
            return render_template('metricas_ml.html', metrics=metrics, error_message="CSV de avaliação vazio.")

        if 'horario' not in df_avaliacao.columns or 'usuario' not in df_avaliacao.columns or 'resultado' not in df_avaliacao.columns:
            flash("O CSV de avaliação deve conter as colunas 'usuario', 'horario' e 'resultado'.", "danger")
            current_app.logger.error("CSV de avaliação com colunas faltando.")
            return render_template('metricas_ml.html', metrics=metrics, error_message="Colunas obrigatórias ausentes no CSV de avaliação.")

        # 3. Pré-processar dados de avaliação (MESMA LÓGICA DO TRAIN_MODEL.PY)
        df_avaliacao['horario'] = pd.to_datetime(df_avaliacao['horario'])

        # CÓDIGO CRÍTICO: Garantir que o usuario_encoder pode transformar TODOS os usuários
        # Se um usuário no df_avaliacao não foi visto durante o treino do usuario_encoder, ele falhará.
        # Uma estratégia é adicionar um tratamento de erro, ou re-fitar o encoder com todos os usuários conhecidos (melhor)
        # O train_model.py já foi alterado para fitar com todos os usuários do DB.
        # Aqui, vamos garantir que só tentamos transformar usuários que o encoder "conhece".
        unknown_users = [u for u in df_avaliacao['usuario'].unique() if u not in usuario_encoder.classes_]
        if unknown_users:
            current_app.logger.warning(f"Usuários desconhecidos no logs_avaliacao.csv: {unknown_users}. Estes usuários não serão avaliados.")
            # Remover linhas com usuários desconhecidos para evitar erro no transform
            df_avaliacao = df_avaliacao[~df_avaliacao['usuario'].isin(unknown_users)]
            if df_avaliacao.empty:
                flash("Após remover usuários desconhecidos, o CSV de avaliação ficou vazio. Nenhuma métrica pode ser calculada.", "info")
                return render_template('metricas_ml.html', metrics=metrics, error_message="Nenhum dado de avaliação válido após filtrar usuários desconhecidos.")

        df_avaliacao['usuario_cod'] = usuario_encoder.transform(df_avaliacao['usuario'])


        # Cálculo de tentativas_invalidas_usuario para o df_avaliacao
        tentativas_invalidas_avaliacao_lista = []
        # Ordenar para garantir o cálculo correto
        df_avaliacao = df_avaliacao.sort_values(by=['usuario', 'horario']).reset_index(drop=True)

        for idx, row in df_avaliacao.iterrows():
            usuario_atual = row['usuario']
            horario_atual = row['horario']
            # Contar tentativas inválidas para o mesmo usuário antes do horário atual
            condicoes = (
                (df_avaliacao.loc[:idx-1, 'usuario'] == usuario_atual) &
                (df_avaliacao.loc[:idx-1, 'resultado'] == 'Credencial Inválida') &
                (df_avaliacao.loc[:idx-1, 'horario'] < horario_atual)
            )
            contagem = df_avaliacao.loc[:idx-1][condicoes].shape[0]
            tentativas_invalidas_avaliacao_lista.append(contagem)

        df_avaliacao['tentativas_invalidas_usuario'] = tentativas_invalidas_avaliacao_lista

        X_eval = df_avaliacao[['usuario_cod', 'tentativas_invalidas_usuario']]
        y_true_eval_str = df_avaliacao['resultado']

        # CÓDIGO CRÍTICO: Garantir que o resultado_encoder pode transformar TODOS os resultados
        unknown_results = [r for r in y_true_eval_str.unique() if r not in resultado_encoder.classes_]
        if unknown_results:
            flash(f"Valores de 'resultado' desconhecidos no logs_avaliacao.csv: {unknown_results}. O modelo não consegue avaliar esses casos.", "danger")
            current_app.logger.error(f"Valores de 'resultado' desconhecidos no logs_avaliacao.csv: {unknown_results}")
            # Remover linhas com resultados desconhecidos
            df_avaliacao = df_avaliacao[~df_avaliacao['resultado'].isin(unknown_results)]
            X_eval = df_avaliacao[['usuario_cod', 'tentativas_invalidas_usuario']]
            y_true_eval_str = df_avaliacao['resultado']
            if df_avaliacao.empty:
                flash("Após remover resultados desconhecidos, o CSV de avaliação ficou vazio. Nenhuma métrica pode ser calculada.", "info")
                return render_template('metricas_ml.html', metrics=metrics, error_message="Nenhum dado de avaliação válido após filtrar resultados desconhecidos.")


        y_true_eval = resultado_encoder.transform(y_true_eval_str)

        if X_eval.empty or y_true_eval.size == 0:
            flash("Dados insuficientes para avaliação após pré-processamento. Verifique o CSV de avaliação.", "warning")
            current_app.logger.warning("Dados de avaliação insuficientes após pré-processamento.")
            return render_template('metricas_ml.html', metrics=metrics, error_message="Dados insuficientes para avaliação.")

        # 4. Fazer predições
        y_pred = modelo.predict(X_eval)

        # 5. Calcular métricas
        metrics['accuracy'] = accuracy_score(y_true_eval, y_pred)
        metrics['precision'] = precision_score(y_true_eval, y_pred, average='weighted', zero_division=0)
        metrics['recall'] = recall_score(y_true_eval, y_pred, average='weighted', zero_division=0)
        metrics['f1_score'] = f1_score(y_true_eval, y_pred, average='weighted', zero_division=0)

        # Matriz de Confusão
        cm = confusion_matrix(y_true_eval, y_pred, labels=np.unique(y_true_eval))
        
        # Obter os nomes das classes do encoder para a matriz de confusão
        # Isso garante que a matriz de confusão tenha rótulos legíveis
        unique_true_labels = np.unique(y_true_eval)
        class_names = [resultado_encoder.inverse_transform([label])[0] for label in unique_true_labels]

        metrics['confusion_matrix'] = cm.tolist() # Converter para lista para JSON/template
        metrics['class_names'] = class_names

        current_app.logger.info("Métricas de ML calculadas com sucesso.")
        flash("Métricas do modelo de ML calculadas com sucesso!", "success")

    except Exception as e:
        flash(f"Erro ao calcular as métricas do ML: {e}. Verifique os logs do servidor.", "danger")
        current_app.logger.error(f"Erro inesperado ao calcular métricas do ML: {e}", exc_info=True)
        return render_template('metricas_ml.html', metrics=metrics, error_message=f"Erro: {e}")

    return render_template('metricas_ml.html', metrics=metrics)