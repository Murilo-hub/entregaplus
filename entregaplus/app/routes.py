from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import User, TentativaLogin
from . import db
from .utils import get_user_ip
from .detectors import verificar_anomalia
from flask_login import login_user, logout_user, login_required, current_user
from .ml_utils import verificar_anomalia
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, flash, redirect, url_for, render_template
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

# Define a rota, que renderiza o arquivo HTML index.html (ex: uma página de boas-vindas ou login).
@main.route('/')
def home():
    return redirect(url_for('main.public_home'))

# Define a rota /login para aceitar apenas requisições POST, geralmente de formulários de login.
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        ip = get_user_ip()

        user = User.query.filter_by(email=email).first()

        if user:
            # LOGIN COM SENHA CORRETA
            if check_password_hash(user.senha, senha):
                login_user(user)

                try:
                    tipo_login = verificar_anomalia(user.email, ip)
                except Exception as e:
                    tipo_login = 'Normal'

                tentativa = TentativaLogin(usuario=user.email, ip=ip, resultado=tipo_login)
                db.session.add(tentativa)
                db.session.commit()

                if tipo_login == 'Suspeito':
                    flash('Login suspeito detectado!', 'danger')
                elif tipo_login == 'Tentativa de Invasão':
                    flash('Tentativa de invasão detectada!', 'danger')

                return redirect(url_for('main.dashboard'))

            # USUÁRIO EXISTE MAS SENHA ERRADA
            else:
                # Verifica tentativas inválidas nos últimos 2 minutos
                dois_minutos_atras = datetime.utcnow() - timedelta(minutes=2)
                tentativas_recentes = TentativaLogin.query.filter_by(
                    usuario=user.email,
                    ip=ip,
                    resultado='Credencial Inválida'
                ).filter(TentativaLogin.horario >= dois_minutos_atras).count()

                if tentativas_recentes >= 3:
                    resultado = 'Suspeito'
                elif tentativas_recentes >= 5:
                    resultado = 'Tentativa de Invasão'
                else:
                    resultado = 'Credencial Inválida'

                tentativa = TentativaLogin(usuario=user.email, ip=ip, resultado=resultado)
                db.session.add(tentativa)
                db.session.commit()

                flash(f'{resultado}. Tente novamente.', 'danger')
                return redirect(url_for('main.login'))

        # USUÁRIO NÃO EXISTE
        else:
            tentativa = TentativaLogin(usuario=email, ip=ip, resultado='Credencial Inválida')
            db.session.add(tentativa)
            db.session.commit()

            flash('Usuário não encontrado.', 'warning')
            return redirect(url_for('main.login'))

    return render_template('login.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('main.login'))

@main.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        email = request.form['email']
        senha = request.form['senha']

        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'danger')
            return redirect(url_for('main.cadastro'))

        senha_hash = generate_password_hash(senha)
        novo_user = User(nome=nome, cpf=cpf, email=email, senha=senha_hash)
        db.session.add(novo_user)
        db.session.commit()
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('main.login'))

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
    # Apenas usuários com email de admin acessam (você pode mudar esse critério)
    if current_user.email != "admin@entregaplus.com":
        flash("Acesso restrito!", "danger")
        return redirect(url_for("main.dashboard"))

    tentativas = TentativaLogin.query.order_by(TentativaLogin.timestamp.desc()).limit(50).all()
    return render_template("tentativas.html", tentativas=tentativas)
