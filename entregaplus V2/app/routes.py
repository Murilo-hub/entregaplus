from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from .models import User, TentativaLogin
from . import db
from .utils import get_user_ip
from .detectors import verificar_anomalia
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

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
        resultado_final_tentativa = 'Credencial Inválida'

        if user:
            if check_password_hash(user.senha, senha):
                login_user(user)

                try:
                    resultado_final_tentativa = verificar_anomalia(user.email, ip)
                    current_app.logger.info(f"Login bem-sucedido para {user.email} (IP: {ip}), resultado ML: {resultado_final_tentativa}")
                except Exception as e:
                    current_app.logger.error(f"Erro ao chamar verificar_anomalia para {user.email} (IP: {ip}): {e}")
                    resultado_final_tentativa = 'Normal'

                if resultado_final_tentativa == 'Suspeito':
                    flash('Atividade de login suspeita detectada para sua conta!', 'warning')
                elif resultado_final_tentativa == 'Tentativa de Invasão':
                    flash('Tentativa de invasão detectada! Sua conta pode estar em risco. Contate o suporte.', 'danger')
                    current_app.logger.critical(f"TENTATIVA DE INVASÃO DETECTADA para usuário: {user.email} do IP: {ip}")
                else:
                    flash('Login realizado com sucesso.', 'success')

                tentativa_obj = TentativaLogin(usuario=user.email, ip=ip, resultado=resultado_final_tentativa)
                db.session.add(tentativa_obj)
                db.session.commit()

                return redirect(url_for('main.dashboard'))

            else:
                # Senha errada: registra como credencial inválida
                resultado_final_tentativa = 'Credencial Inválida'
                current_app.logger.warning(f"Falha de login (senha incorreta) para usuário: {email} do IP: {ip}")
                flash('Email ou senha inválidos. Tente novamente.', 'danger')

        else:
            resultado_final_tentativa = 'Credencial Inválida'
            current_app.logger.warning(f"Falha de login (usuário não encontrado): {email} do IP: {ip}")
            flash('Email ou senha inválidos. Tente novamente.', 'danger')

        tentativa_obj = TentativaLogin(usuario=email if email else "não informado", ip=ip, resultado=resultado_final_tentativa)
        db.session.add(tentativa_obj)
        db.session.commit()

        return redirect(url_for('main.login'))

    return render_template('login.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user_name=current_user.nome)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('main.login'))

@main.route('/cadastro', methods=['GET', 'POST'])
def cadastro():

    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        email = request.form.get('email')
        senha = request.form.get('senha')

        if email:
            email = email.lower().strip()
        
        if not all([nome, email, senha]):
            flash('Todos os campos obrigatórios (nome, email, senha) devem ser preenchidos.', 'danger')
            return redirect(url_for('main.cadastro'))
        
        if User.query.filter_by(email=email).first():
            flash('Este email já está cadastrado. Tente fazer login.', 'warning')
            return redirect(url_for('main.cadastro'))
        
        senha_hash = generate_password_hash(senha, method='pbkdf2:sha256')
        novo_user = User(nome=nome, cpf=cpf, email=email, senha=senha_hash)

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
    tentativas_paginadas = TentativaLogin.query.order_by(TentativaLogin.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template("tentativas.html", tentativas_paginadas=tentativas_paginadas)
