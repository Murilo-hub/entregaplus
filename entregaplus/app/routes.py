from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import User, LoginAttempt
from . import db
from .utils import get_user_ip
from .detectors import verificar_anomalia
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return redirect(url_for('main.public_home'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        ip = get_user_ip()

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.senha, senha):
            login_user(user)
            
            tipo_login = verificar_anomalia(user.email, ip, senha)
            tentativa = LoginAttempt(usuario_id=user.id, ip=ip, resultado=tipo_login)
            db.session.add(tentativa)
            db.session.commit()

            if tipo_login == 'Suspeito':
                flash('Login suspeito detectado!', 'danger')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Credenciais inválidas.', 'danger')

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