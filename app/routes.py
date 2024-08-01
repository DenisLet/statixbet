from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from sqlalchemy import text
from urllib.parse import urlsplit
from app import app, db
from app.forms import LoginForm, RegistrationForm, ResendConfirmationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.email import send_email, send_password_reset_email
from itsdangerous import URLSafeTimedSerializer
import os
@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home Page')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        if not user.is_confirmed:
            flash('Your account is not confirmed. Please check your email or request a new confirmation link.')
            return redirect(url_for('resend_confirmation'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign in', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        token = generate_confirmation_token(user.email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(subject, app.config['ADMINS'][0], [user.email], html, html)
        flash('A confirmation email has been sent via email.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form)

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('index'))
    user = User.query.filter_by(email=email).first_or_404()
    if user.is_confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.is_confirmed = True
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('index'))

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
    except:
        return False
    return email


@app.route('/resend_confirmation', methods=['GET', 'POST'])
def resend_confirmation():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResendConfirmationForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user and not user.is_confirmed:
            token = generate_confirmation_token(user.email)
            confirm_url = url_for('confirm_email', token=token, _external=True)
            html = render_template('activate.html', confirm_url=confirm_url)
            subject = "Please confirm your email"
            send_email(subject, app.config['ADMINS'][0], [user.email], html, html)
            flash('A new confirmation email has been sent.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid email or account already confirmed.', 'danger')
    return render_template('resend_confirmation.html', form=form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/test_request')
@login_required
def test_request():
    if current_user.available_requests > 0:
        current_user.available_requests -= 1
        db.session.commit()
        flash('Request made successfully. Remaining requests: {}'.format(current_user.available_requests))
    else:
        flash('No available requests left.')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/add_requests/<int:user_id>', methods=['POST'])
@login_required
def add_requests(user_id):
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    user = User.query.get(user_id)
    if user:
        user.available_requests += int(request.form['requests'])
        db.session.commit()
        flash('Requests added successfully.')
    return redirect(url_for('admin_panel'))


@app.route('/equalizer')
def unity_index():
    return render_template('unity.html')

@app.route('/static/unity/Build/<path:filename>')
def send_build(filename):
    file_path = os.path.join('static', 'unity', 'Build', filename)
    if filename.endswith('.gz'):
        response = send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))
        response.headers['Content-Encoding'] = 'gzip'
        return response
    return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))

@app.route('/static/unity/TemplateData/<path:filename>')
def send_template_data(filename):
    return send_from_directory(os.path.join('static', 'unity', 'TemplateData'), filename)

@app.route('/get_cube_count')
def get_cube_count():
    # Замените это значение на логику получения количества кубиков
    cube_count = 1
    return jsonify({'cube_count': cube_count})


@app.route('/soccer')
def soccer():
    return render_template('soccer.html', active_page='soccer')

@app.route('/odds_scan_content')
def odds_scan_content():
    return render_template('soccer/soccer_odds_scan.html')


@app.route('/under_construction')
def under_construction():
    return render_template('under_construction.html')

@app.route('/api/countries', methods=['GET'])
def get_countries_endpoint():
    countries = get_countries()  # Функция для получения стран из базы данных
    return jsonify(countries)