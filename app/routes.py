from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory, session, Response
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from sqlalchemy import func
from urllib.parse import urlsplit
from app import app, db
from app.forms import LoginForm, RegistrationForm, ResendConfirmationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.forms import SoccerLiveInput, SoccerLiveAdditionalInput, SoccerMainOddsInput, CountryLeageTeamBook
from app.models import User, ChampionshipsSoccer, SoccerMain, XbetOdds, Bet365Odds, UnibetOdds, SoccerTimeline
from app.models import SoccerHalf1Stats
from app.email import send_email, send_password_reset_email
from app.spare_func import safe_float, count_odds_diff, calculate_gth1
from itsdangerous import URLSafeTimedSerializer
import os
from datetime import datetime
from app.for_corners_temp import process_corners
from app.for_yellows_cards import process_yellow_cards
from app.for_shots_ongoal import process_shots_ongoal
from app.for_fouls import process_fouls
from app.for_offsides import process_offsides
from app.for_throws_ins import process_throws_ins
import time
from app.matches_ids import get_matches_ids
from app.soccer_timeliner import make_timeline, make_timeline_yc
from functools import wraps
import urllib3
import certifi
import json
import matplotlib.pyplot as plt
import io
from app.graphs import plot_goals, plot_area_chart, plot_yc, plot_area_chart_yc, plot_1goal_distribution, one_more_goal
from app.graphs import plot_1yc_distribution
import ssl
from app.closest_matches import MatchFinder, odds_calc, extract_match_ids
from app.soccer_permatch_queries.goals import get_ind_goals_team, get_ind_goals_opponent, get_ind_goals_vs
from sqlalchemy.orm import aliased
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
            flash('Your account is not confirmed. Please check your email or request a new confirmation link. Check spam from test.testov.run@gmail.com')
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
        flash('A confirmation email has been sent via email. Check spam from test.testov.run@gmail.com', 'success')
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
            flash('A new confirmation email has been sent. Check spam from test.testov.run@gmail.com', 'success')
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
        flash('Check your email for the instructions to reset your password. Check spam from test.testov.run@gmail.com')
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


def decrement_requests(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # Если запрос не является POST, просто вызываем функцию без уменьшения числа запросов
        if request.method == 'POST':
            if current_user.available_requests > 0:
                # Уменьшаем количество запросов только при POST-запросе
                current_user.available_requests -= 1
                db.session.commit()
            else:
                flash('No available requests left.')
                return redirect(url_for('index'))  # Перенаправляем на главную страницу или любую другую
        return func(*args, **kwargs)
    return decorated_function



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

@app.route('/under_construction')
def under_construction():
    return render_template('under_construction.html')

@app.route('/soccer')
@login_required
def soccer():
    return render_template('soccer.html', active_page='soccer')



@app.route('/odds_scan_content')
def odds_scan_content():
    return render_template('soccer/soccer_odds_scan.html')



@app.route('/api/countries', methods=['GET'])
def get_countries():
    try:
        countries = db.session.query(ChampionshipsSoccer.country).join(
            SoccerMain, ChampionshipsSoccer.id == SoccerMain.league_id
        ).distinct().order_by(ChampionshipsSoccer.country).all()

        country_list = [country[0] for country in countries]
        print('Countries:', country_list)  # Отладочная информация
        return jsonify(country_list)
    except Exception as e:
        print('Error fetching countries:', e)
        return jsonify([]), 500



@app.route('/api/leagues', methods=['GET'])
def get_leagues():
    country = request.args.get('country')
    session['country'] = country

    if not country:
        return jsonify({"error": "Country parameter is required"}), 400

    try:
        leagues = db.session.query(ChampionshipsSoccer.league).join(
            SoccerMain, ChampionshipsSoccer.id == SoccerMain.league_id
        ).filter(
            ChampionshipsSoccer.country == country
        ).distinct().order_by(ChampionshipsSoccer.league).all()

        leagues_list = [league[0] for league in leagues]
        return jsonify(leagues_list)
    except Exception as e:
        print('Error fetching leagues:', e)
        return jsonify([]), 500


@app.route('/api/teams', methods=['GET'])
def get_teams():
    league = request.args.get('league')
    country = session.get('country')

    if not league:
        return jsonify({"error": "League parameter is required"}), 400

    if not country:
        return jsonify({"error": "Country parameter is required"}), 400

    try:
        # Получаем id лиги для заданной лиги и страны
        league_info = db.session.query(ChampionshipsSoccer.id).filter(
            ChampionshipsSoccer.league == league,
            ChampionshipsSoccer.country == country
        ).first()

        if not league_info:
            return jsonify({"error": "League not found for the specified country"}), 404

        league_id = league_info[0]

        # Получаем список команд из модели SoccerMain для найденного league_id
        teams = db.session.query(SoccerMain.team_home).filter(
            SoccerMain.league_id == league_id
        ).distinct().union(
            db.session.query(SoccerMain.team_away).filter(
                SoccerMain.league_id == league_id
            ).distinct()
        ).order_by(SoccerMain.team_home).all()

        # Преобразуем результат в список строк
        teams_list = [team[0] for team in teams if team[0] is not None]
        return jsonify(teams_list)
    except Exception as e:
        print('Error fetching teams:', e)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/process-form', methods=['POST'])
@login_required
@decrement_requests
def process_form():
    data = request.get_json()

    country = data.get('country')
    league = data.get('league')
    team = data.get('team')
    opponent = data.get('opponent')
    sportbook = data.get('sportbook')
    date_from = data.get('date_from')
    date_to = data.get('date_to')
    position = data.get('position')

    win_open = safe_float(data.get('team1_win', 0))
    win_open_minus = safe_float(data.get('team1_win_minus', 0))
    win_open_plus = safe_float(data.get('team1_win_plus', 0))

    draw_open = safe_float(data.get('team1_draw', 0))
    draw_open_minus = safe_float(data.get('team1_draw_minus', 0))
    draw_open_plus = safe_float(data.get('team1_draw_plus', 0))

    loss_open = safe_float(data.get('team1_loss', 0))
    loss_open_minus = safe_float(data.get('team1_loss_minus', 0))
    loss_open_plus = safe_float(data.get('team1_loss_plus', 0))

    over_1_5_open = safe_float(data.get('team1_over_15', 0))
    over_1_5_open_minus = safe_float(data.get('team1_over_15_minus', 0))
    over_1_5_open_plus = safe_float(data.get('team1_over_15_plus', 0))

    over_2_5_open = safe_float(data.get('team1_over_25', 0))
    over_2_5_open_minus = safe_float(data.get('team1_over_25_minus', 0))
    over_2_5_open_plus = safe_float(data.get('team1_over_25_plus', 0))
    selected_team = data.get('calculate_team')
    print(selected_team)

    # Convert date strings to datetime.date objects if provided
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date_from format, should be YYYY-MM-DD'}), 400

    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date_to format, should be YYYY-MM-DD'}), 400





    sportbook_models = {
        '1xbet': XbetOdds,
        'bet365': Bet365Odds,
        'unibet': UnibetOdds
    }
    selected_model = sportbook_models.get(sportbook.lower())

    if not selected_model:
        return jsonify({'error': 'Invalid sportbook'}), 400

    query = db.session.query(
        selected_model,
        SoccerMain,
        ChampionshipsSoccer
    ).join(
        SoccerMain, selected_model.match_id == SoccerMain.match_id
    ).join(
        ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
    )

    # Adding filters
    if country:
        query = query.filter(ChampionshipsSoccer.country == country)
    if league:
        query = query.filter(ChampionshipsSoccer.league == league)
    if team and position == "HOME":
        query = query.filter(SoccerMain.team_home == team)
        if opponent:
            query = query.filter(SoccerMain.team_away == opponent)
    if team and position == "AWAY":
        query = query.filter(SoccerMain.team_away == team)
        if opponent:
            query = query.filter(SoccerMain.team_home == opponent)

    if opponent and position == "HOME":
        query = query.filter(SoccerMain.team_away == opponent)
        if team:
            query = query.filter(SoccerMain.team_home == team)
    if opponent and position == "AWAY":
        query = query.filter(SoccerMain.team_home == opponent)
        if team:
            query = query.filter(SoccerMain.team_away == team)



    if date_from:
        query = query.filter(SoccerMain.match_date >= date_from)
    if date_to:
        query = query.filter(SoccerMain.match_date <= date_to)

    if win_open != 0 or win_open_minus != 0 or win_open_plus != 0:
        query = query.filter(selected_model.win_home_open.between(win_open - abs(win_open_minus), win_open + abs(win_open_plus)))

    if draw_open != 0 or draw_open_minus != 0 or draw_open_plus != 0:
        query = query.filter(selected_model.draw_open.between(draw_open - abs(draw_open_minus), draw_open + abs(draw_open_plus)))

    if loss_open != 0 or loss_open_minus != 0 or loss_open_plus != 0:
        query = query.filter(selected_model.win_away_open.between(loss_open - abs(loss_open_minus), loss_open + abs(loss_open_plus)))

    if over_1_5_open != 0 or over_1_5_open_minus != 0 or over_1_5_open_plus != 0:
        query = query.filter(selected_model.odds_1_5_open.between(over_1_5_open - abs(over_1_5_open_minus),
                                                                  over_1_5_open + abs(over_1_5_open_plus)))

    if over_2_5_open != 0 or over_2_5_open_minus != 0 or over_2_5_open_plus != 0:
        query = query.filter(selected_model.odds_2_5_open.between(over_2_5_open - abs(over_2_5_open_minus), over_2_5_open + abs(over_2_5_open_plus)))

    results = query.all()
    response_list = []

    for result in results:
        if result:
            # print(result)
            win_home_diff = f"{count_odds_diff(result[0].win_home_open, result[0].win_home_close)[0]}<br><br>{count_odds_diff(result[0].win_home_open, result[0].win_home_close)[1]}"
            win_away_diff = f"{count_odds_diff(result[0].win_away_open, result[0].win_away_close)[0]}<br><br>{count_odds_diff(result[0].win_away_open, result[0].win_away_close)[1]}"
            total25_diff = f"{count_odds_diff(result[0].odds_2_5_open, result[0].odds_2_5_close)[0]}<br><br>{count_odds_diff(result[0].odds_2_5_open, result[0].odds_2_5_close)[1]}"
            match = {
                'date': result[1].match_date.strftime('%Y-%m-%d'),
                'team_home': result[1].team_home,
                'team_away': result[1].team_away,
                'home_score_ft': result[1].home_score_ft,
                'away_score_ft': result[1].away_score_ft,
                'win_home_open': result[0].win_home_open,
                'win_home_close': result[0].win_home_close,
                'win_home_diff': win_home_diff,
                'win_away_open': result[0].win_away_open,
                'win_away_close': result[0].win_away_close,
                'win_away_diff': win_away_diff,
                'total25_open': result[0].odds_2_5_open,
                'total25_close': result[0].odds_2_5_close,  # Change this line
                'total25_diff': total25_diff
            }
            response_list.append(match)

    if not response_list:
        response = {'error': 'No matching records found'}
    else:
        response = response_list


    match_finder = MatchFinder()
    # Find matches
    home_match = match_finder.find_closest_home_match(team, opponent)
    away_match = match_finder.find_closest_away_match(team, opponent)
    matches_with_opponent = match_finder.find_closest_matches_with_stats(team, opponent, selected_team)
    extracted_match_ids = extract_match_ids(home_match, away_match, matches_with_opponent)
    print()
    print(home_match)
    print()
    print(away_match)
    print()
    print(matches_with_opponent)
    print()
    # print(extracted_match_ids)
    # print(odds_calc(extracted_match_ids, selected_model))
    odds_data = odds_calc(extracted_match_ids, selected_model)

    response_list = sorted(response_list, key=lambda x: x['date'], reverse=True)
    odds_data.append([])

    def expand_odds_data(odds_data, home_match, away_match, matches_with_opponent):
        # Создаем словарь для сопоставления данных по match_id
        match_data = {}

        # Копируем исходные данные и добавляем их в словарь match_data
        if isinstance(odds_data, list):
            for odds in odds_data:
                if isinstance(odds, dict):
                    match_id = odds.get('match_id_e')
                    if match_id:
                        match_data[match_id] = odds.copy()

        # Обработка home_match
        if isinstance(home_match, dict):
            for key in ['team1', 'team2']:
                team_data = home_match.get(key)
                if isinstance(team_data, dict):
                    match_id = team_data.get('match_id')
                    if match_id and match_id in match_data:
                        match_data[match_id].update(team_data)

        # Обработка away_match
        if isinstance(away_match, dict):
            for key in ['team1', 'team2']:
                team_data = away_match.get(key)
                if isinstance(team_data, dict):
                    match_id = team_data.get('match_id')
                    if match_id and match_id in match_data:
                        match_data[match_id].update(team_data)

        # Обработка matches_with_opponent
        if isinstance(matches_with_opponent, dict):
            home_matches = matches_with_opponent.get('home_matches', {})
            away_matches = matches_with_opponent.get('away_matches', {})

            # Проверяем, что home_matches и away_matches - словари
            if isinstance(home_matches, dict):
                for key in ['team1', 'team2']:
                    home_team_data = home_matches.get(key)
                    if isinstance(home_team_data, dict):
                        match_id = home_team_data.get('match_id')
                        if match_id and match_id in match_data:
                            match_data[match_id].update(home_team_data)

            if isinstance(away_matches, dict):
                for key in ['team1', 'team2']:
                    away_team_data = away_matches.get(key)
                    if isinstance(away_team_data, dict):
                        match_id = away_team_data.get('match_id')
                        if match_id and match_id in match_data:
                            match_data[match_id].update(away_team_data)

        # Преобразуем обратно в список
        result = list(match_data.values())

        return result

    # Пример использования
    expanded_odds_data = expand_odds_data(odds_data, home_match, away_match, matches_with_opponent)
    print(expanded_odds_data)
    return jsonify({
        'response_list': response_list,
        'odds_data': expanded_odds_data
    })


@app.route('/soccer_live', methods=['GET', 'POST'])
@login_required
@decrement_requests
def soccer_live():
    form = SoccerLiveInput()
    additional_form = SoccerLiveAdditionalInput()
    odds_form = SoccerMainOddsInput()
    teams_form = CountryLeageTeamBook()
    button = request.form.get('button')
    # Запрос уникальных стран, связанных с матчами
    countries = db.session.query(ChampionshipsSoccer.country).join(
        SoccerMain, ChampionshipsSoccer.id == SoccerMain.league_id
    ).distinct().order_by(ChampionshipsSoccer.country.asc()).all()

    country_choices = [(None, 'All Countries')] + [(country[0], country[0]) for country in countries]


    percentages = []
    team1_percentages = []
    team2_percentages = []
    total_entries = 0  # Инициализация переменной для подсчета матчей
    overall_probability_over0 = 0  # Инициализация переменной для общей вероятности

    if form.validate_on_submit():
        score_t1_form = form.score_t1.data
        score_t2_form = form.score_t2.data

        country = teams_form.country.data
        league = teams_form.league.data
        team1 = teams_form.team_home.data
        team2 = teams_form.team_away.data
        """stats section"""
        xg_t1 = form.xg_t1.data
        xg_t1_plus = form.xg_t1_plus.data
        xg_t1_minus = form.xg_t1_minus.data
        xg_t2 = form.xg_t2.data
        xg_t2_plus = form.xg_t2_plus.data
        xg_t2_minus = form.xg_t2_minus.data

        shots_t1 = form.shots_t1.data
        shots_t1_plus = form.shots_t1_plus.data
        shots_t1_minus = form.shots_t1_minus.data
        shots_t2 = form.shots_t2.data
        shots_t2_plus = form.shots_t2_plus.data
        shots_t2_minus = form.shots_t2_minus.data

        ongoal_t1 = form.on_goal_t1.data
        ongoal_t1_plus = form.on_goal_t1_plus.data
        ongoal_t1_minus = form.on_goal_t1_minus.data
        ongoal_t2 = form.on_goal_t2.data
        ongoal_t2_plus = form.on_goal_t2_plus.data
        ongoal_t2_minus = form.on_goal_t2_minus.data

        poss_t1 = form.possesion_t1.data
        poss_t1_plus = form.possesion_t1_plus.data
        poss_t1_minus = form.possesion_t1_minus.data
        poss_t2 = form.possesion_t2.data
        poss_t2_plus = form.possesion_t2_plus.data
        poss_t2_minus = form.possesion_t2_minus.data

        corners_t1 = form.corners_t1.data
        corners_t1_plus = form.corners_t1_plus.data
        corners_t1_minus = form.corners_t1_minus.data
        corners_t2 = form.corners_t2.data
        corners_t2_plus = form.corners_t2_plus.data
        corners_t2_minus = form.corners_t2_minus.data

        attacks_t1 = form.attacks_t1.data
        attacks_t1_plus = form.attacks_t1_plus.data
        attacks_t1_minus = form.attacks_t1_minus.data
        attacks_t2 = form.attacks_t2.data
        attacks_t2_plus = form.attacks_t2_plus.data
        attacks_t2_minus = form.attacks_t2_minus.data

        fkicks_t1 = additional_form.freekicks_t1.data
        fkicks_t1_plus = additional_form.freekicks_t1_plus.data
        fkicks_t1_minus = additional_form.freekicks_t1_minus.data
        fkicks_t2 = additional_form.freekicks_t2.data
        fkicks_t2_plus = additional_form.freekicks_t2_plus.data
        fkicks_t2_minus = additional_form.freekicks_t2_minus.data

        throwins_t1 = additional_form.throw_ins_t1.data
        throwins_t1_plus = additional_form.throw_ins_t1_plus.data
        throwins_t1_minus = additional_form.throw_ins_t1_minus.data
        throwins_t2 = additional_form.throw_ins_t2.data
        throwins_t2_plus = additional_form.throw_ins_t2_plus.data
        throwins_t2_minus = additional_form.throw_ins_t2_minus.data

        offsides_t1 = additional_form.offsides_t1.data
        offsides_t1_plus = additional_form.offsides_t1_plus.data
        offsides_t1_minus = additional_form.offsides_t1_minus.data
        offsides_t2 = additional_form.offsides_t2.data
        offsides_t2_plus = additional_form.offsides_t2_plus.data
        offsides_t2_minus = additional_form.offsides_t2_minus.data

        fouls_t1 = additional_form.fouls_t1.data
        fouls_t1_plus = additional_form.fouls_t1_plus.data
        fouls_t1_minus = additional_form.fouls_t1_minus.data
        fouls_t2 = additional_form.fouls_t2.data
        fouls_t2_plus = additional_form.fouls_t2_plus.data
        fouls_t2_minus = additional_form.fouls_t2_minus.data

        yellows_t1 = additional_form.yellows_t1.data
        yellows_t1_plus = additional_form.yellows_t1_plus.data
        yellows_t1_minus = additional_form.yellows_t1_minus.data
        yellows_t2 = additional_form.yellows_t2.data
        yellows_t2_plus = additional_form.yellows_t2_plus.data
        yellows_t2_minus = additional_form.yellows_t2_minus.data

        # Фильтрация по коэффициентам закрытия для победы и ничьи и тоталов
        win_close = odds_form.win_t1.data
        win_close_plus = odds_form.win_t1_plus.data
        win_close_minus = odds_form.win_t1_minus.data
        draw_close = odds_form.draw.data
        draw_close_plus = odds_form.draw_plus.data
        draw_close_minus = odds_form.draw_minus.data
        lose_close = odds_form.win_t2.data
        lose_close_plus = odds_form.win_t2_plus.data
        lose_close_minus = odds_form.win_t2_minus.data
        total15_close = odds_form.total_15.data
        total15_close_plus = odds_form.total_15_plus.data
        total15_close_minus = odds_form.total_15_minus.data
        total25_close = odds_form.total_25.data
        total25_close_plus = odds_form.total_25_plus.data
        total25_close_minus = odds_form.total_25_minus.data

        # Фильтрация по коэффициентам открытия для победы и ничьи и тоталов
        win_open = odds_form.win_t1_open.data
        win_open_minus = odds_form.win_t1_open_minus.data
        win_open_plus = odds_form.win_t1_open_plus.data
        draw_open = odds_form.draw_open.data
        draw_open_plus = odds_form.draw_open_plus.data
        draw_open_minus = odds_form.draw_open_minus.data
        lose_open = odds_form.win_t2_open.data
        lose_open_plus = odds_form.win_t2_open_plus.data
        lose_open_minus = odds_form.win_t2_open_minus.data
        total15_open = odds_form.total_15_open.data
        total15_open_plus = odds_form.total_15_open_plus.data
        total15_open_minus = odds_form.total_15_open_minus.data
        total25_open = odds_form.total_25_open.data
        total25_open_plus = odds_form.total_25_open_plus.data
        total25_open_minus = odds_form.total_25_open_minus.data

        since1 = request.form.get('since1')
        till1 = request.form.get('till1')
        team1_group = request.form.get('team1_group')

        since2 = request.form.get('since2')
        till2 = request.form.get('till2')
        team2_group = request.form.get('team2_group')

        since1 = None if since1 == '' else int(since1)
        till1 = None if till1 == '' else int(till1)
        since2 = None if since2 == '' else int(since2)
        till2 = None if till2 == '' else int(till2)

        print(since1, till1, team1_group, since2, till2, team2_group)

        if country == 'None':
            country = team1 = team2 = ''

        sportbook = teams_form.sportsbook.data
        sportbook_models = {
            '1xbet': XbetOdds,
            'bet365': Bet365Odds,
            'unibet': UnibetOdds
        }
        selected_model = sportbook_models.get(sportbook.lower())


        if request.method == 'POST':
            button = request.form.get('button')
            print(button)
            if button == 'corners':


                total_corners_entries,corners_percentages,team1_corners_percentage,team2_corners_percentage  = process_corners(
                    score_t1_form, score_t2_form, country, league, team1, team2,
                    xg_t1, xg_t1_plus, xg_t1_minus, xg_t2, xg_t2_plus, xg_t2_minus,
                    shots_t1, shots_t1_plus, shots_t1_minus, shots_t2, shots_t2_plus, shots_t2_minus,
                    ongoal_t1, ongoal_t1_plus, ongoal_t1_minus, ongoal_t2, ongoal_t2_plus, ongoal_t2_minus,
                    poss_t1, poss_t1_plus, poss_t1_minus, poss_t2, poss_t2_plus, poss_t2_minus,
                    corners_t1, corners_t1_plus, corners_t1_minus, corners_t2, corners_t2_plus, corners_t2_minus,
                    attacks_t1, attacks_t1_plus, attacks_t1_minus, attacks_t2, attacks_t2_plus, attacks_t2_minus,
                    fkicks_t1, fkicks_t1_plus, fkicks_t1_minus, fkicks_t2, fkicks_t2_plus, fkicks_t2_minus,
                    throwins_t1, throwins_t1_plus, throwins_t1_minus, throwins_t2, throwins_t2_plus, throwins_t2_minus,
                    offsides_t1, offsides_t1_plus, offsides_t1_minus, offsides_t2, offsides_t2_plus, offsides_t2_minus,
                    fouls_t1, fouls_t1_plus, fouls_t1_minus, fouls_t2, fouls_t2_plus, fouls_t2_minus,
                    yellows_t1, yellows_t1_plus, yellows_t1_minus, yellows_t2, yellows_t2_plus, yellows_t2_minus,
                    win_close, win_close_plus, win_close_minus, draw_close, draw_close_plus, draw_close_minus,
                    lose_close, lose_close_plus, lose_close_minus, total15_close, total15_close_plus, total15_close_minus,
                    total25_close, total25_close_plus, total25_close_minus,
                    win_open, win_open_minus, win_open_plus, draw_open, draw_open_plus, draw_open_minus,
                    lose_open, lose_open_plus, lose_open_minus, total15_open, total15_open_plus, total15_open_minus,
                    total25_open, total25_open_plus, total25_open_minus, selected_model
                )
                return render_template('soccer/soccer_live.html',
                                       form=form,
                                       additional_form=additional_form,
                                       odds_form=odds_form,
                                       teams_form=teams_form,
                                       country_choices=country_choices,
                                       total_corners_entries=total_corners_entries,
                                       corners_percentages=corners_percentages,
                                       team1_corners_percentages = team1_corners_percentage,
                                       team2_corners_percentages = team2_corners_percentage,
                                       button=button)

            if request.method == 'POST':
                button = request.form.get('button')
                print(button)
                if button == 'yellow_cards':
                    total_yellow_entries, yellow_percentages, team1_yellow_percentage, team2_yellow_percentage = process_yellow_cards(
                        score_t1_form, score_t2_form, country, league, team1, team2,
                        xg_t1, xg_t1_plus, xg_t1_minus, xg_t2, xg_t2_plus, xg_t2_minus,
                        shots_t1, shots_t1_plus, shots_t1_minus, shots_t2, shots_t2_plus, shots_t2_minus,
                        ongoal_t1, ongoal_t1_plus, ongoal_t1_minus, ongoal_t2, ongoal_t2_plus, ongoal_t2_minus,
                        poss_t1, poss_t1_plus, poss_t1_minus, poss_t2, poss_t2_plus, poss_t2_minus,
                        corners_t1, corners_t1_plus, corners_t1_minus, corners_t2, corners_t2_plus, corners_t2_minus,
                        attacks_t1, attacks_t1_plus, attacks_t1_minus, attacks_t2, attacks_t2_plus, attacks_t2_minus,
                        fkicks_t1, fkicks_t1_plus, fkicks_t1_minus, fkicks_t2, fkicks_t2_plus, fkicks_t2_minus,
                        throwins_t1, throwins_t1_plus, throwins_t1_minus, throwins_t2, throwins_t2_plus,
                        throwins_t2_minus,
                        offsides_t1, offsides_t1_plus, offsides_t1_minus, offsides_t2, offsides_t2_plus,
                        offsides_t2_minus,
                        fouls_t1, fouls_t1_plus, fouls_t1_minus, fouls_t2, fouls_t2_plus, fouls_t2_minus,
                        yellows_t1, yellows_t1_plus, yellows_t1_minus, yellows_t2, yellows_t2_plus, yellows_t2_minus,
                        win_close, win_close_plus, win_close_minus, draw_close, draw_close_plus, draw_close_minus,
                        lose_close, lose_close_plus, lose_close_minus, total15_close, total15_close_plus,
                        total15_close_minus,
                        total25_close, total25_close_plus, total25_close_minus,
                        win_open, win_open_minus, win_open_plus, draw_open, draw_open_plus, draw_open_minus,
                        lose_open, lose_open_plus, lose_open_minus, total15_open, total15_open_plus, total15_open_minus,
                        total25_open, total25_open_plus, total25_open_minus, selected_model
                    )
                    print(yellows_t1, yellows_t2)
                    match_ids = get_matches_ids(score_t1_form, score_t2_form, country, league, team1, team2,
                                                xg_t1, xg_t1_plus, xg_t1_minus, xg_t2, xg_t2_plus, xg_t2_minus,
                                                shots_t1, shots_t1_plus, shots_t1_minus, shots_t2, shots_t2_plus,
                                                shots_t2_minus,
                                                ongoal_t1, ongoal_t1_plus, ongoal_t1_minus, ongoal_t2, ongoal_t2_plus,
                                                ongoal_t2_minus,
                                                poss_t1, poss_t1_plus, poss_t1_minus, poss_t2, poss_t2_plus,
                                                poss_t2_minus,
                                                corners_t1, corners_t1_plus, corners_t1_minus, corners_t2,
                                                corners_t2_plus,
                                                corners_t2_minus,
                                                attacks_t1, attacks_t1_plus, attacks_t1_minus, attacks_t2,
                                                attacks_t2_plus,
                                                attacks_t2_minus,
                                                fkicks_t1, fkicks_t1_plus, fkicks_t1_minus, fkicks_t2, fkicks_t2_plus,
                                                fkicks_t2_minus,
                                                throwins_t1, throwins_t1_plus, throwins_t1_minus, throwins_t2,
                                                throwins_t2_plus,
                                                throwins_t2_minus,
                                                offsides_t1, offsides_t1_plus, offsides_t1_minus, offsides_t2,
                                                offsides_t2_plus,
                                                offsides_t2_minus,
                                                fouls_t1, fouls_t1_plus, fouls_t1_minus, fouls_t2, fouls_t2_plus,
                                                fouls_t2_minus,
                                                yellows_t1, yellows_t1_plus, yellows_t1_minus, yellows_t2,
                                                yellows_t2_plus,
                                                yellows_t2_minus,
                                                win_close, win_close_plus, win_close_minus, draw_close, draw_close_plus,
                                                draw_close_minus,
                                                lose_close, lose_close_plus, lose_close_minus, total15_close,
                                                total15_close_plus,
                                                total15_close_minus,
                                                total25_close, total25_close_plus, total25_close_minus,
                                                win_open, win_open_minus, win_open_plus, draw_open, draw_open_plus,
                                                draw_open_minus,
                                                lose_open, lose_open_plus, lose_open_minus, total15_open,
                                                total15_open_plus,
                                                total15_open_minus,
                                                total25_open, total25_open_plus, total25_open_minus, selected_model)


                    timeline_yc = make_timeline_yc(match_ids)
                    # print(match_ids)
                    # print(timeline_yc)
                    if timeline_yc:
                        home_yc_h2 = timeline_yc['home_yc_h2']
                        away_yc_h2 = timeline_yc['away_yc_h2']
                        yc_h2 = timeline_yc['yc_h2']

                        # Generate plots
                        home_yc_img = plot_yc(home_yc_h2, title='Home 1st YC(2 half)')
                        away_yc_img = plot_yc(away_yc_h2, title='Away 1st YC(2 half)')
                        yc_img = plot_yc(yc_h2, title='1st YC(2 half)')
                        yc_area_img = plot_area_chart_yc(yc_h2, home_yc_h2, away_yc_h2)
                        one_yc_between = plot_1yc_distribution(yc_h2)
                        next_yc_img = None

                        # Проверяем, что since1 и till1 являются целыми числами
                        if isinstance(since1, int) and isinstance(till1, int):
                            # Если since2 и till2 не заданы (None), передаем None для их значений
                            if since2 is None or till2 is None:
                                next_yc_img = one_more_goal(yc_h2, home_yc_h2, away_yc_h2, since1, till1,
                                                              team1_group,
                                                              None, None, None)
                            # Если since2 и till2 также являются целыми числами, вызываем функцию с обеими группами параметров
                            elif isinstance(since2, int) and isinstance(till2, int):
                                next_yc_img = one_more_goal(yc_h2, home_yc_h2, away_yc_h2, since1, till1,
                                                              team1_group,
                                                              since2, till2, team2_group)
                    else:
                        print("No data found for the specified match_id.")
                        home_yc_img = away_yc_img = yc_img = yc_area_img = next_yc_img =None

                    return render_template('soccer/soccer_live.html',
                                           form=form,
                                           additional_form=additional_form,
                                           odds_form=odds_form,
                                           teams_form=teams_form,
                                           country_choices=country_choices,
                                           total_yellow_entries=total_yellow_entries,
                                           yellow_percentages=yellow_percentages,
                                           team1_yellow_percentages=team1_yellow_percentage,
                                           team2_yellow_percentages=team2_yellow_percentage,
                                           button=button,
                                           home_yc_img=home_yc_img,
                                           away_yc_img=away_yc_img,
                                           yc_img=yc_img,
                                           yc_area_img=yc_area_img,
                                           one_yc_between=one_yc_between,
                                           next_yc_img=next_yc_img)

                if request.method == 'POST':
                    button = request.form.get('button')
                    print(button)
                    if button == 'shots_on_goal':
                        total_ongoal_entries, ongoal_percentages, team1_ongoal_percentage, team2_ongoal_percentage = process_shots_ongoal(
                            score_t1_form, score_t2_form, country, league, team1, team2,
                            xg_t1, xg_t1_plus, xg_t1_minus, xg_t2, xg_t2_plus, xg_t2_minus,
                            shots_t1, shots_t1_plus, shots_t1_minus, shots_t2, shots_t2_plus, shots_t2_minus,
                            ongoal_t1, ongoal_t1_plus, ongoal_t1_minus, ongoal_t2, ongoal_t2_plus, ongoal_t2_minus,
                            poss_t1, poss_t1_plus, poss_t1_minus, poss_t2, poss_t2_plus, poss_t2_minus,
                            corners_t1, corners_t1_plus, corners_t1_minus, corners_t2, corners_t2_plus,
                            corners_t2_minus,
                            attacks_t1, attacks_t1_plus, attacks_t1_minus, attacks_t2, attacks_t2_plus,
                            attacks_t2_minus,
                            fkicks_t1, fkicks_t1_plus, fkicks_t1_minus, fkicks_t2, fkicks_t2_plus, fkicks_t2_minus,
                            throwins_t1, throwins_t1_plus, throwins_t1_minus, throwins_t2, throwins_t2_plus,
                            throwins_t2_minus,
                            offsides_t1, offsides_t1_plus, offsides_t1_minus, offsides_t2, offsides_t2_plus,
                            offsides_t2_minus,
                            fouls_t1, fouls_t1_plus, fouls_t1_minus, fouls_t2, fouls_t2_plus, fouls_t2_minus,
                            yellows_t1, yellows_t1_plus, yellows_t1_minus, yellows_t2, yellows_t2_plus,
                            yellows_t2_minus,
                            win_close, win_close_plus, win_close_minus, draw_close, draw_close_plus, draw_close_minus,
                            lose_close, lose_close_plus, lose_close_minus, total15_close, total15_close_plus,
                            total15_close_minus,
                            total25_close, total25_close_plus, total25_close_minus,
                            win_open, win_open_minus, win_open_plus, draw_open, draw_open_plus, draw_open_minus,
                            lose_open, lose_open_plus, lose_open_minus, total15_open, total15_open_plus,
                            total15_open_minus,
                            total25_open, total25_open_plus, total25_open_minus, selected_model
                        )
                        return render_template('soccer/soccer_live.html',
                                               form=form,
                                               additional_form=additional_form,
                                               odds_form=odds_form,
                                               teams_form=teams_form,
                                               country_choices=country_choices,
                                               total_ongoal_entries=total_ongoal_entries,
                                               ongoal_percentages=ongoal_percentages,
                                               team1_ongoal_percentages=team1_ongoal_percentage,
                                               team2_ongoal_percentages=team2_ongoal_percentage,
                                               button=button)
                if request.method == 'POST':
                    button = request.form.get('button')
                    print(button)
                    if button == 'fouls':
                        total_fouls_entries, fouls_percentages, team1_fouls_percentage, team2_fouls_percentage = process_fouls(
                            score_t1_form, score_t2_form, country, league, team1, team2,
                            xg_t1, xg_t1_plus, xg_t1_minus, xg_t2, xg_t2_plus, xg_t2_minus,
                            shots_t1, shots_t1_plus, shots_t1_minus, shots_t2, shots_t2_plus, shots_t2_minus,
                            ongoal_t1, ongoal_t1_plus, ongoal_t1_minus, ongoal_t2, ongoal_t2_plus, ongoal_t2_minus,
                            poss_t1, poss_t1_plus, poss_t1_minus, poss_t2, poss_t2_plus, poss_t2_minus,
                            corners_t1, corners_t1_plus, corners_t1_minus, corners_t2, corners_t2_plus,
                            corners_t2_minus,
                            attacks_t1, attacks_t1_plus, attacks_t1_minus, attacks_t2, attacks_t2_plus,
                            attacks_t2_minus,
                            fkicks_t1, fkicks_t1_plus, fkicks_t1_minus, fkicks_t2, fkicks_t2_plus, fkicks_t2_minus,
                            throwins_t1, throwins_t1_plus, throwins_t1_minus, throwins_t2, throwins_t2_plus,
                            throwins_t2_minus,
                            offsides_t1, offsides_t1_plus, offsides_t1_minus, offsides_t2, offsides_t2_plus,
                            offsides_t2_minus,
                            fouls_t1, fouls_t1_plus, fouls_t1_minus, fouls_t2, fouls_t2_plus, fouls_t2_minus,
                            yellows_t1, yellows_t1_plus, yellows_t1_minus, yellows_t2, yellows_t2_plus,
                            yellows_t2_minus,
                            win_close, win_close_plus, win_close_minus, draw_close, draw_close_plus, draw_close_minus,
                            lose_close, lose_close_plus, lose_close_minus, total15_close, total15_close_plus,
                            total15_close_minus,
                            total25_close, total25_close_plus, total25_close_minus,
                            win_open, win_open_minus, win_open_plus, draw_open, draw_open_plus, draw_open_minus,
                            lose_open, lose_open_plus, lose_open_minus, total15_open, total15_open_plus,
                            total15_open_minus,
                            total25_open, total25_open_plus, total25_open_minus, selected_model
                        )
                        return render_template('soccer/soccer_live.html',
                                               form=form,
                                               additional_form=additional_form,
                                               odds_form=odds_form,
                                               teams_form=teams_form,
                                               country_choices=country_choices,
                                               total_fouls_entries=total_fouls_entries,
                                               fouls_percentages=fouls_percentages,
                                               team1_fouls_percentages=team1_fouls_percentage,
                                               team2_fouls_percentages=team2_fouls_percentage,
                                               button=button)
                if request.method == 'POST':
                    button = request.form.get('button')
                    print(button)
                    if button == 'offsides':
                        total_offsides_entries, offsides_percentages, team1_offsides_percentage, team2_offsides_percentage = process_offsides(
                            score_t1_form, score_t2_form, country, league, team1, team2,
                            xg_t1, xg_t1_plus, xg_t1_minus, xg_t2, xg_t2_plus, xg_t2_minus,
                            shots_t1, shots_t1_plus, shots_t1_minus, shots_t2, shots_t2_plus, shots_t2_minus,
                            ongoal_t1, ongoal_t1_plus, ongoal_t1_minus, ongoal_t2, ongoal_t2_plus, ongoal_t2_minus,
                            poss_t1, poss_t1_plus, poss_t1_minus, poss_t2, poss_t2_plus, poss_t2_minus,
                            corners_t1, corners_t1_plus, corners_t1_minus, corners_t2, corners_t2_plus,
                            corners_t2_minus,
                            attacks_t1, attacks_t1_plus, attacks_t1_minus, attacks_t2, attacks_t2_plus,
                            attacks_t2_minus,
                            fkicks_t1, fkicks_t1_plus, fkicks_t1_minus, fkicks_t2, fkicks_t2_plus, fkicks_t2_minus,
                            throwins_t1, throwins_t1_plus, throwins_t1_minus, throwins_t2, throwins_t2_plus,
                            throwins_t2_minus,
                            offsides_t1, offsides_t1_plus, offsides_t1_minus, offsides_t2, offsides_t2_plus,
                            offsides_t2_minus,
                            fouls_t1, fouls_t1_plus, fouls_t1_minus, fouls_t2, fouls_t2_plus, fouls_t2_minus,
                            yellows_t1, yellows_t1_plus, yellows_t1_minus, yellows_t2, yellows_t2_plus,
                            yellows_t2_minus,
                            win_close, win_close_plus, win_close_minus, draw_close, draw_close_plus, draw_close_minus,
                            lose_close, lose_close_plus, lose_close_minus, total15_close, total15_close_plus,
                            total15_close_minus,
                            total25_close, total25_close_plus, total25_close_minus,
                            win_open, win_open_minus, win_open_plus, draw_open, draw_open_plus, draw_open_minus,
                            lose_open, lose_open_plus, lose_open_minus, total15_open, total15_open_plus,
                            total15_open_minus,
                            total25_open, total25_open_plus, total25_open_minus, selected_model
                        )
                        return render_template('soccer/soccer_live.html',
                                               form=form,
                                               additional_form=additional_form,
                                               odds_form=odds_form,
                                               teams_form=teams_form,
                                               country_choices=country_choices,
                                               total_offsides_entries=total_offsides_entries,
                                               offsides_percentages=offsides_percentages,
                                               team1_offsides_percentages=team1_offsides_percentage,
                                               team2_offsides_percentages=team2_offsides_percentage,
                                               button=button)

                    if request.method == 'POST':
                        button = request.form.get('button')
                        print(button)
                        if button == 'throw_ins':
                            total_throws_entries, throws_percentages = process_throws_ins(
                                score_t1_form, score_t2_form, country, league, team1, team2,
                                xg_t1, xg_t1_plus, xg_t1_minus, xg_t2, xg_t2_plus, xg_t2_minus,
                                shots_t1, shots_t1_plus, shots_t1_minus, shots_t2, shots_t2_plus, shots_t2_minus,
                                ongoal_t1, ongoal_t1_plus, ongoal_t1_minus, ongoal_t2, ongoal_t2_plus, ongoal_t2_minus,
                                poss_t1, poss_t1_plus, poss_t1_minus, poss_t2, poss_t2_plus, poss_t2_minus,
                                corners_t1, corners_t1_plus, corners_t1_minus, corners_t2, corners_t2_plus,
                                corners_t2_minus,
                                attacks_t1, attacks_t1_plus, attacks_t1_minus, attacks_t2, attacks_t2_plus,
                                attacks_t2_minus,
                                fkicks_t1, fkicks_t1_plus, fkicks_t1_minus, fkicks_t2, fkicks_t2_plus, fkicks_t2_minus,
                                throwins_t1, throwins_t1_plus, throwins_t1_minus, throwins_t2, throwins_t2_plus,
                                throwins_t2_minus,
                                offsides_t1, offsides_t1_plus, offsides_t1_minus, offsides_t2, offsides_t2_plus,
                                offsides_t2_minus,
                                fouls_t1, fouls_t1_plus, fouls_t1_minus, fouls_t2, fouls_t2_plus, fouls_t2_minus,
                                yellows_t1, yellows_t1_plus, yellows_t1_minus, yellows_t2, yellows_t2_plus,
                                yellows_t2_minus,
                                win_close, win_close_plus, win_close_minus, draw_close, draw_close_plus,
                                draw_close_minus,
                                lose_close, lose_close_plus, lose_close_minus, total15_close, total15_close_plus,
                                total15_close_minus,
                                total25_close, total25_close_plus, total25_close_minus,
                                win_open, win_open_minus, win_open_plus, draw_open, draw_open_plus, draw_open_minus,
                                lose_open, lose_open_plus, lose_open_minus, total15_open, total15_open_plus,
                                total15_open_minus,
                                total25_open, total25_open_plus, total25_open_minus, selected_model
                            )
                            return render_template('soccer/soccer_live.html',
                                                   form=form,
                                                   additional_form=additional_form,
                                                   odds_form=odds_form,
                                                   teams_form=teams_form,
                                                   country_choices=country_choices,
                                                   total_throws_entries=total_throws_entries,
                                                   throws_percentages=throws_percentages,
                                                   button=button)
        SoccerMainAlias = aliased(SoccerMain)

        query = db.session.query(
            (SoccerTimeline.score_t1_h2 + SoccerTimeline.score_t2_h2).label('total_score_h2'),
            func.count().label('count')
        ).filter(
            (SoccerTimeline.score_t1_h1 == score_t1_form) if score_t1_form else True,
            (SoccerTimeline.score_t2_h1 == score_t2_form) if score_t2_form else True
        ).join(
            selected_model, SoccerTimeline.match_id == selected_model.match_id
        ).join(
            SoccerHalf1Stats, SoccerTimeline.match_id == SoccerHalf1Stats.match_id
        ).join(
            SoccerMainAlias, SoccerTimeline.match_id == SoccerMainAlias.match_id  # Используем алиас
        ).filter(
            SoccerMainAlias.final != 'Awarded'  # Фильтруем по полю final через алиас
        )

        if country and country != 'None':
            query = query.join(
                SoccerMain, SoccerTimeline.match_id == SoccerMain.match_id
            ).join(
                ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
            ).filter(
                ChampionshipsSoccer.country == country
            )
        else:
            # Ограничение при отсутствии фильтрации по стране
            query = query.distinct()

        if league and league != 'null':
            query = query.filter(
                SoccerMain.league_id == league
            )

        if team1 and team1 != '':
            query = query.filter(
                SoccerMain.team_home == team1
            )

        if team2 and team2 != '':
            query = query.filter(
                SoccerMain.team_away == team2
            )

        '''stats queries'''
        # Фильтрация по xG для команды 1
        if xg_t1 is not None and xg_t1_minus is not None and xg_t1_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.home_xg.between(xg_t1 - xg_t1_minus, xg_t1 + xg_t1_plus)
            )

        # Фильтрация по xG для команды 2
        if xg_t2 is not None and xg_t2_minus is not None and xg_t2_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.away_xg.between(xg_t2 - xg_t2_minus, xg_t2 + xg_t2_plus)
            )


        if shots_t1 is not None and shots_t1_minus is not None and shots_t1_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.home_attempts.between(shots_t1 - shots_t1_minus, shots_t1 + shots_t1_plus)
            )

        # Фильтрация по xG для команды 2
        if shots_t2 is not None and shots_t2_minus is not None and shots_t2_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.away_attempts.between(shots_t2 - shots_t2_minus, shots_t2 + shots_t2_plus)
            )


        if ongoal_t1 is not None and ongoal_t1_minus is not None and ongoal_t1_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.home_shots.between(ongoal_t1 - ongoal_t1_minus, ongoal_t1 + ongoal_t1_plus)
            )

        if ongoal_t2 is not None and ongoal_t2_minus is not None and ongoal_t2_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.away_shots.between(ongoal_t2 - ongoal_t2_minus, ongoal_t2 + ongoal_t2_plus)
            )


        if poss_t1 is not None and poss_t1_minus is not None and poss_t1_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.home_possession.between(poss_t1 - poss_t1_minus, poss_t1 + poss_t1_plus)
            )

        if poss_t2 is not None and poss_t2_minus is not None and poss_t2_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.away_possession.between(poss_t2 - poss_t2_minus, poss_t2 + poss_t2_plus)
            )


        if corners_t1 is not None and corners_t1_minus is not None and corners_t1_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.home_corners.between(corners_t1 - corners_t1_minus, corners_t1 + corners_t1_plus)
            )

        if corners_t2 is not None and corners_t2_minus is not None and corners_t2_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.away_corners.between(corners_t2 - corners_t2_minus, corners_t2 + corners_t2_plus)
            )


        if attacks_t1 is not None and attacks_t1_minus is not None and attacks_t1_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.home_dangerous_attacks.between(attacks_t1 - attacks_t1_minus, attacks_t1 + attacks_t1_plus)
            )

        if attacks_t2 is not None and attacks_t2_minus is not None and attacks_t2_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.away_dangerous_attacks.between(attacks_t2 - attacks_t2_minus, attacks_t2 + attacks_t2_plus)
            )


        if fkicks_t1 is not None and fkicks_t1_minus is not None and fkicks_t1_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.home_freekicks.between(fkicks_t1 - fkicks_t1_minus, fkicks_t1 + fkicks_t1_plus)
            )

        if fkicks_t2 is not None and fkicks_t2_minus is not None and fkicks_t2_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.away_freekicks.between(fkicks_t2 - fkicks_t2_minus, fkicks_t2 + fkicks_t2_plus)
            )


        if throwins_t1 is not None and throwins_t1_minus is not None and throwins_t1_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.home_throw_ins.between(throwins_t1 - throwins_t1_minus, throwins_t1 + throwins_t1_plus)
            )

        if throwins_t2 is not None and throwins_t2_minus is not None and throwins_t2_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.away_throw_ins.between(throwins_t2 - throwins_t2_minus, throwins_t2 + throwins_t2_plus)
            )

        if offsides_t1 is not None and offsides_t1_minus is not None and offsides_t1_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.home_offsides.between(offsides_t1 - offsides_t1_minus, offsides_t1 + offsides_t1_plus)
            )

        if offsides_t2 is not None and offsides_t2_minus is not None and offsides_t2_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.away_offsides.between(offsides_t2 - offsides_t2_minus, offsides_t2 + offsides_t2_plus)
            )

        if fouls_t1 is not None and fouls_t1_minus is not None and fouls_t1_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.home_fouls.between(fouls_t1 - fouls_t1_minus, fouls_t1 + fouls_t1_plus)
            )

        if fouls_t2 is not None and fouls_t2_minus is not None and fouls_t2_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.away_fouls.between(fouls_t2 - fouls_t2_minus, fouls_t2 + fouls_t2_plus)
            )

        if yellows_t1 is not None and yellows_t1_minus is not None and yellows_t1_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.home_yellow.between(yellows_t1 - yellows_t1_minus, yellows_t1 + yellows_t1_plus)
            )

        if yellows_t2 is not None and yellows_t2_minus is not None and yellows_t2_plus is not None:
            query = query.filter(
                SoccerHalf1Stats.away_yellow.between(yellows_t2 - yellows_t2_minus, yellows_t2 + yellows_t2_plus)
            )




        if win_close is not None and win_close_minus is not None and win_close_plus is not None:
            query = query.filter(
                selected_model.win_home_close.between(win_close - win_close_minus, win_close + win_close_plus)
            )
        if draw_close is not None and draw_close_minus is not None and draw_close_plus is not None:
            query = query.filter(
                selected_model.draw_close.between(draw_close - abs(draw_close_minus), draw_close + abs(draw_close_plus))
            )
        if lose_close is not None and lose_close_minus is not None and lose_close_plus is not None:
            query = query.filter(
                selected_model.win_away_close.between(lose_close - lose_close_minus, lose_close + lose_close_plus)
            )

        if total15_close is not None and total15_close_minus is not None and total15_close_plus is not None:
            query = query.filter(
                selected_model.odds_1_5_close.between(total15_close - total15_close_minus,
                                                      total15_close + total15_close_plus)
            )

        if total25_close is not None and total25_close_minus is not None and total25_close_plus is not None:
            query = query.filter(
                selected_model.odds_2_5_close.between(total25_close - total25_close_minus,
                                                      total25_close + total25_close_plus)
            )



        # Фильтрация по коэффициентам открытия для победы, ничьи и поражения
        if win_open is not None and win_open_minus is not None and win_open_plus is not None:
            query = query.filter(
                selected_model.win_home_open.between(win_open - win_open_minus, win_open + win_open_plus)
            )
        if draw_open is not None and draw_open_minus is not None and draw_open_plus is not None:
            query = query.filter(
                selected_model.draw_open.between(draw_open - abs(draw_open_minus), draw_open + abs(draw_open_plus))
            )
        if lose_open is not None and lose_open_minus is not None and lose_open_plus is not None:
            query = query.filter(
                selected_model.win_away_open.between(lose_open - lose_open_minus, lose_open + lose_open_plus)
            )

        if total15_open is not None and total15_open_minus is not None and total15_open_plus is not None:
            query = query.filter(
                selected_model.odds_1_5_open.between(total15_open - total15_open_minus,
                                                     total15_open + total15_open_plus)
            )

        if total25_open is not None and total25_open_minus is not None and total25_open_plus is not None:
            query = query.filter(
                selected_model.odds_2_5_open.between(total25_open - total25_open_minus,
                                                     total25_open + total25_open_plus)
            )

        # Группировка и сортировка
        soccer_timeline_entries = query.group_by(
            'total_score_h2'
        ).order_by(
            'total_score_h2'
        ).all()

        total_entries = sum(entry.count for entry in soccer_timeline_entries)  # Подсчет всех матчей(угорвых и тд)

        if soccer_timeline_entries:
            percentages = [
                (entry.total_score_h2, entry.count, (entry.count / total_entries) * 100)
                for entry in soccer_timeline_entries
            ]

        # Аналогичная фильтрация и расчеты для команд
        SoccerMainAlias = aliased(SoccerMain)

        # Аналогичная фильтрация и расчеты для команд
        team1_entries = db.session.query(
            SoccerTimeline.score_t1_h2.label('team1_score_h2'),
            func.count().label('count')
        ).join(
            selected_model, SoccerTimeline.match_id == selected_model.match_id
        ).join(
            SoccerHalf1Stats, SoccerTimeline.match_id == SoccerHalf1Stats.match_id
        ).join(
            SoccerMainAlias, SoccerTimeline.match_id == SoccerMainAlias.match_id  # Используем алиас
        ).filter(
            (SoccerTimeline.score_t1_h1 == score_t1_form) if score_t1_form else True,
            (SoccerTimeline.score_t2_h1 == score_t2_form) if score_t2_form else True,
            SoccerMainAlias.final != 'Awarded'  # Фильтруем по полю final через алиас
        )



        if country and country != 'None':
            team1_entries = team1_entries.join(
                SoccerMain, SoccerTimeline.match_id == SoccerMain.match_id
            ).join(
                ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
            ).filter(
                ChampionshipsSoccer.country == country
            )

        else:
            # Ограничение при отсутствии фильтрации по стране
            team1_entries = team1_entries.distinct()

        if league and league != 'null':
            team1_entries = team1_entries.filter(
                SoccerMain.league_id == league
            )

        if team1 and team1 != '':
            team1_entries = team1_entries.filter(
                SoccerMain.team_home == team1
            )

        if team2 and team2 != '':
            team1_entries = team1_entries.filter(
                SoccerMain.team_away == team2
            )

        if xg_t1 is not None and xg_t1_minus is not None and xg_t1_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.home_xg.between(xg_t1 - xg_t1_minus, xg_t1 + xg_t1_plus)
            )

        if xg_t2 is not None and xg_t2_minus is not None and xg_t2_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.away_xg.between(xg_t2 - xg_t2_minus, xg_t2 + xg_t2_plus)
            )

        if shots_t1 is not None and shots_t1_minus is not None and shots_t1_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.home_attempts.between(shots_t1 - shots_t1_minus, shots_t1 + shots_t1_plus)
            )

        # Фильтрация по xG для команды 2
        if shots_t2 is not None and shots_t2_minus is not None and shots_t2_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.away_attempts.between(shots_t2 - shots_t2_minus, shots_t2 + shots_t2_plus)
            )

        if ongoal_t1 is not None and ongoal_t1_minus is not None and ongoal_t1_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.home_shots.between(ongoal_t1 - ongoal_t1_minus, ongoal_t1 + ongoal_t1_plus)
            )

        if ongoal_t2 is not None and ongoal_t2_minus is not None and ongoal_t2_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.away_shots.between(ongoal_t2 - ongoal_t2_minus, ongoal_t2 + ongoal_t2_plus)
            )


        if poss_t1 is not None and poss_t1_minus is not None and poss_t1_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.home_possession.between(poss_t1 - poss_t1_minus, poss_t1 + poss_t1_plus)
            )

        if poss_t2 is not None and poss_t2_minus is not None and poss_t2_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.away_possession.between(poss_t2 - poss_t2_minus, poss_t2 + poss_t2_plus)
            )

        if corners_t1 is not None and corners_t1_minus is not None and corners_t1_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.home_corners.between(corners_t1 - corners_t1_minus, corners_t1 + corners_t1_plus)
            )

        if corners_t2 is not None and corners_t2_minus is not None and corners_t2_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.away_corners.between(corners_t2 - corners_t2_minus, corners_t2 + corners_t2_plus)
            )

        if attacks_t1 is not None and attacks_t1_minus is not None and attacks_t1_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.home_dangerous_attacks.between(attacks_t1 - attacks_t1_minus, attacks_t1 + attacks_t1_plus)
            )

        if attacks_t2 is not None and attacks_t2_minus is not None and attacks_t2_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.away_dangerous_attacks.between(attacks_t2 - attacks_t2_minus, attacks_t2 + attacks_t2_plus)
            )

        if fkicks_t1 is not None and fkicks_t1_minus is not None and fkicks_t1_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.home_freekicks.between(fkicks_t1 - fkicks_t1_minus, fkicks_t1 + fkicks_t1_plus)
            )

        if fkicks_t2 is not None and fkicks_t2_minus is not None and fkicks_t2_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.away_freekicks.between(fkicks_t2 - fkicks_t2_minus, fkicks_t2 + fkicks_t2_plus)
            )

        if throwins_t1 is not None and throwins_t1_minus is not None and throwins_t1_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.home_throw_ins.between(throwins_t1 - throwins_t1_minus, throwins_t1 + throwins_t1_plus)
            )

        if throwins_t2 is not None and throwins_t2_minus is not None and throwins_t2_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.away_throw_ins.between(throwins_t2 - throwins_t2_minus, throwins_t2 + throwins_t2_plus)
            )

        if offsides_t1 is not None and offsides_t1_minus is not None and offsides_t1_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.home_offsides.between(offsides_t1 - offsides_t1_minus, offsides_t1 + offsides_t1_plus)
            )

        if offsides_t2 is not None and offsides_t2_minus is not None and offsides_t2_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.away_offsides.between(offsides_t2 - offsides_t2_minus, offsides_t2 + offsides_t2_plus)
            )

        if fouls_t1 is not None and fouls_t1_minus is not None and fouls_t1_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.home_fouls.between(fouls_t1 - fouls_t1_minus, fouls_t1 + fouls_t1_plus)
            )

        if fouls_t2 is not None and fouls_t2_minus is not None and fouls_t2_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.away_fouls.between(fouls_t2 - fouls_t2_minus, fouls_t2 + fouls_t2_plus)
            )

        if yellows_t1 is not None and yellows_t1_minus is not None and yellows_t1_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.home_yellow.between(yellows_t1 - yellows_t1_minus, yellows_t1 + yellows_t1_plus)
            )

        if yellows_t2 is not None and yellows_t2_minus is not None and yellows_t2_plus is not None:
            team1_entries = team1_entries.filter(
                SoccerHalf1Stats.away_yellow.between(yellows_t2 - yellows_t2_minus, yellows_t2 + yellows_t2_plus)
            )



        # Фильтрация по коэффициентам закрытия для команды 1
        if win_close is not None and win_close_minus is not None and win_close_plus is not None:
            team1_entries = team1_entries.filter(
                selected_model.win_home_close.between(win_close - win_close_minus, win_close + win_close_plus)
            )
        if draw_close is not None and draw_close_minus is not None and draw_close_plus is not None:
            team1_entries = team1_entries.filter(
                selected_model.draw_close.between(draw_close - draw_close_minus, draw_close + draw_close_plus)
            )
        if lose_close is not None and lose_close_minus is not None and lose_close_plus is not None:
            team1_entries = team1_entries.filter(
                selected_model.win_away_close.between(lose_close - lose_close_minus, lose_close + lose_close_plus)
            )

        if total15_close is not None and total15_close_minus is not None and total15_close_plus is not None:
            team1_entries = team1_entries.filter(
                selected_model.odds_1_5_close.between(total15_close - total15_close_minus,
                                                      total15_close + total15_close_plus)
            )

        if total25_close is not None and total25_close_minus is not None and total25_close_plus is not None:
            team1_entries = team1_entries.filter(
                selected_model.odds_2_5_close.between(total25_close - total25_close_minus,
                                                      total25_close + total25_close_plus)
            )

        # Фильтрация по коэффициентам открытия для команды 1
        if win_open is not None and win_open_minus is not None and win_open_plus is not None:
            team1_entries = team1_entries.filter(
                selected_model.win_home_open.between(win_open - win_open_minus, win_open + win_open_plus)
            )
        if draw_open is not None and draw_open_minus is not None and draw_open_plus is not None:
            team1_entries = team1_entries.filter(
                selected_model.draw_open.between(draw_open - draw_open_minus, draw_open + draw_open_plus)
            )
        if lose_open is not None and lose_open_minus is not None and lose_open_plus is not None:
            team1_entries = team1_entries.filter(
                selected_model.win_away_open.between(lose_open - lose_open_minus, lose_open + lose_open_plus)
            )

        if total15_open is not None and total15_open_minus is not None and total15_open_plus is not None:
            team1_entries = team1_entries.filter(
                selected_model.odds_1_5_open.between(total15_open - total15_open_minus,
                                                     total15_open + total15_open_plus)
            )

        if total25_open is not None and total25_open_minus is not None and total25_open_plus is not None:
            team1_entries = team1_entries.filter(
                selected_model.odds_2_5_open.between(total25_open - total25_open_minus,
                                                     total25_open + total25_open_plus)
            )


        team1_entries = team1_entries.group_by(
            'team1_score_h2'
        ).order_by(
            'team1_score_h2'
        ).all()

        if team1_entries:
            total_team1_entries = sum(entry.count for entry in team1_entries)
            team1_percentages = [
                (entry.team1_score_h2, entry.count, (entry.count / total_team1_entries) * 100)
                for entry in team1_entries
            ]

        SoccerMainAlias = aliased(SoccerMain)

        # Аналогичная фильтрация и расчеты для команды 2
        team2_entries = db.session.query(
            SoccerTimeline.score_t2_h2.label('team2_score_h2'),
            func.count().label('count')
        ).join(
            selected_model, SoccerTimeline.match_id == selected_model.match_id
        ).join(
            SoccerHalf1Stats, SoccerTimeline.match_id == SoccerHalf1Stats.match_id
        ).join(
            SoccerMainAlias, SoccerTimeline.match_id == SoccerMainAlias.match_id  # Используем алиас
        ).filter(
            (SoccerTimeline.score_t1_h1 == score_t1_form) if score_t1_form else True,
            (SoccerTimeline.score_t2_h1 == score_t2_form) if score_t2_form else True,
            SoccerMainAlias.final != 'Awarded'  # Фильтруем по полю final через алиас
        )

        if country and country != 'None':
            team2_entries = team2_entries.join(
                SoccerMain, SoccerTimeline.match_id == SoccerMain.match_id
            ).join(
                ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
            ).filter(
                ChampionshipsSoccer.country == country
            )

        else:
            # Ограничение при отсутствии фильтрации по стране
            team2_entries = team2_entries.distinct()

        if league and league != 'null':
            team2_entries = team2_entries.filter(
                SoccerMain.league_id == league
            )

        if team1 and team1 != '':
            team2_entries = team2_entries.filter(
                SoccerMain.team_home == team1
            )

        if team2 and team2 != '':
            team2_entries = team2_entries.filter(
                SoccerMain.team_away == team2
            )


        '''stats section'''

        if xg_t1 is not None and xg_t1_minus is not None and xg_t1_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.home_xg.between(xg_t1 - xg_t1_minus, xg_t1 + xg_t1_plus)
            )

        if xg_t2 is not None and xg_t2_minus is not None and xg_t2_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.away_xg.between(xg_t2 - xg_t2_minus, xg_t2 + xg_t2_plus)
            )


        if shots_t1 is not None and shots_t1_minus is not None and shots_t1_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.home_attempts.between(shots_t1 - shots_t1_minus, shots_t1 + shots_t1_plus)
            )

        # Фильтрация по attempts для команды 2
        if shots_t2 is not None and shots_t2_minus is not None and shots_t2_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.away_attempts.between(shots_t2 - shots_t2_minus, shots_t2 + shots_t2_plus)
            )

        if ongoal_t1 is not None and ongoal_t1_minus is not None and ongoal_t1_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.home_shots.between(ongoal_t1 - ongoal_t1_minus, ongoal_t1 + ongoal_t1_plus)
            )

        if ongoal_t2 is not None and ongoal_t2_minus is not None and ongoal_t2_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.away_shots.between(ongoal_t2 - ongoal_t2_minus, ongoal_t2 + ongoal_t2_plus)
            )

        if poss_t1 is not None and poss_t1_minus is not None and poss_t1_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.home_possession.between(poss_t1 - poss_t1_minus, poss_t1 + poss_t1_plus)
            )

        if poss_t2 is not None and poss_t2_minus is not None and poss_t2_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.away_possession.between(poss_t2 - poss_t2_minus, poss_t2 + poss_t2_plus)
            )

        if corners_t1 is not None and corners_t1_minus is not None and corners_t1_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.home_corners.between(corners_t1 - corners_t1_minus, corners_t1 + corners_t1_plus)
            )

        if corners_t2 is not None and corners_t2_minus is not None and corners_t2_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.away_corners.between(corners_t2 - corners_t2_minus, corners_t2 + corners_t2_plus)
            )

        if attacks_t1 is not None and attacks_t1_minus is not None and attacks_t1_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.home_dangerous_attacks.between(attacks_t1 - attacks_t1_minus, attacks_t1 + attacks_t1_plus)
            )

        if attacks_t2 is not None and attacks_t2_minus is not None and attacks_t2_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.away_dangerous_attacks.between(attacks_t2 - attacks_t2_minus, attacks_t2 + attacks_t2_plus)
            )

        if fkicks_t1 is not None and fkicks_t1_minus is not None and fkicks_t1_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.home_freekicks.between(fkicks_t1 - fkicks_t1_minus, fkicks_t1 + fkicks_t1_plus)
            )

        if fkicks_t2 is not None and fkicks_t2_minus is not None and fkicks_t2_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.away_freekicks.between(fkicks_t2 - fkicks_t2_minus, fkicks_t2 + fkicks_t2_plus)
            )

        if throwins_t1 is not None and throwins_t1_minus is not None and throwins_t1_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.home_throw_ins.between(throwins_t1 - throwins_t1_minus, throwins_t1 + throwins_t1_plus)
            )

        if throwins_t2 is not None and throwins_t2_minus is not None and throwins_t2_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.away_throw_ins.between(throwins_t2 - throwins_t2_minus, throwins_t2 + throwins_t2_plus)
            )

        if offsides_t1 is not None and offsides_t1_minus is not None and offsides_t1_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.home_offsides.between(offsides_t1 - offsides_t1_minus, offsides_t1 + offsides_t1_plus)
            )

        if offsides_t2 is not None and offsides_t2_minus is not None and offsides_t2_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.away_offsides.between(offsides_t2 - offsides_t2_minus, offsides_t2 + offsides_t2_plus)
            )

        if fouls_t1 is not None and fouls_t1_minus is not None and fouls_t1_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.home_fouls.between(fouls_t1 - fouls_t1_minus, fouls_t1 + fouls_t1_plus)
            )

        if fouls_t2 is not None and fouls_t2_minus is not None and fouls_t2_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.away_fouls.between(fouls_t2 - fouls_t2_minus, fouls_t2 + fouls_t2_plus)
            )

        if yellows_t1 is not None and yellows_t1_minus is not None and yellows_t1_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.home_yellow.between(yellows_t1 - yellows_t1_minus, yellows_t1 + yellows_t1_plus)
            )

        if yellows_t2 is not None and yellows_t2_minus is not None and yellows_t2_plus is not None:
            team2_entries = team2_entries.filter(
                SoccerHalf1Stats.away_yellow.between(yellows_t2 - yellows_t2_minus, yellows_t2 + yellows_t2_plus)
            )

        # Фильтрация по коэффициентам закрытия для команды 2
        if win_close is not None and win_close_minus is not None and win_close_plus is not None:
            team2_entries = team2_entries.filter(
                selected_model.win_home_close.between(win_close - win_close_minus, win_close + win_close_plus)
            )
        if draw_close is not None and draw_close_minus is not None and draw_close_plus is not None:
            team2_entries = team2_entries.filter(
                selected_model.draw_close.between(draw_close - draw_close_minus, draw_close + draw_close_plus)
            )
        if lose_close is not None and lose_close_minus is not None and lose_close_plus is not None:
            team2_entries = team2_entries.filter(
                selected_model.win_away_close.between(lose_close - lose_close_minus, lose_close + lose_close_plus)
            )

        if total15_close is not None and total15_close_minus is not None and total15_close_plus is not None:
            team2_entries = team2_entries.filter(
                selected_model.odds_1_5_close.between(total15_close - total15_close_minus,
                                                      total15_close + total15_close_plus)
            )

        if total25_close is not None and total25_close_minus is not None and total25_close_plus is not None:
            team2_entries = team2_entries.filter(
                selected_model.odds_2_5_close.between(total25_close - total25_close_minus,
                                                      total25_close + total25_close_plus)
            )

        # Фильтрация по коэффициентам открытия для команды 2
        if win_open is not None and win_open_minus is not None and win_open_plus is not None:
            team2_entries = team2_entries.filter(
                selected_model.win_home_open.between(win_open - win_open_minus, win_open + win_open_plus)
            )
        if draw_open is not None and draw_open_minus is not None and draw_open_plus is not None:
            team2_entries = team2_entries.filter(
                selected_model.draw_open.between(draw_open - draw_open_minus, draw_open + draw_open_plus)
            )
        if lose_open is not None and lose_open_minus is not None and lose_open_plus is not None:
            team2_entries = team2_entries.filter(
                selected_model.win_away_open.between(lose_open - lose_open_minus, lose_open + lose_open_plus)
            )

        if total15_open is not None and total15_open_minus is not None and total15_open_plus is not None:
            team2_entries = team2_entries.filter(
                selected_model.odds_1_5_open.between(total15_open - total15_open_minus,
                                                     total15_open + total15_open_plus)
            )

        if total25_open is not None and total25_open_minus is not None and total25_open_plus is not None:
            team2_entries = team2_entries.filter(
                selected_model.odds_2_5_open.between(total25_open - total25_open_minus,
                                                     total25_open + total25_open_plus)
            )


        team2_entries = team2_entries.group_by(
            'team2_score_h2'
        ).order_by(
            'team2_score_h2'
        ).all()

        if team2_entries:
            total_team2_entries = sum(entry.count for entry in team2_entries)
            team2_percentages = [
                (entry.team2_score_h2, entry.count, (entry.count / total_team2_entries) * 100)
                for entry in team2_entries
            ]

        eval1, gth1 = calculate_gth1(team1_percentages, team2_percentages)
        print(eval1, gth1)
        # Расчет вероятности того, что хотя бы одна команда забьет гол
        if team1_percentages and team2_percentages:
            # Преобразование процентных данных в вероятности
            team1_goal_over0 = [entry[2] / 100 for entry in team1_percentages if entry[0] == 0]
            team2_goal_over0 = [entry[2] / 100 for entry in team2_percentages if entry[0] == 0]



            try:
                if team1_goal_over0 and team2_goal_over0:
                    overall_probability_over0 = round(1 - team1_goal_over0[0] * team2_goal_over0[0], 4)
                else:
                    overall_probability_over0 = 0.00001
            except Exception as e:
                print(f"Error calculating probability: {e}")
                overall_probability_over0 = 0.00001
        else:
            overall_probability_over0 = 0.00001

        match_ids = get_matches_ids(score_t1_form, score_t2_form, country, league, team1, team2,
                                xg_t1, xg_t1_plus, xg_t1_minus, xg_t2, xg_t2_plus, xg_t2_minus,
                                shots_t1, shots_t1_plus, shots_t1_minus, shots_t2, shots_t2_plus, shots_t2_minus,
                                ongoal_t1, ongoal_t1_plus, ongoal_t1_minus, ongoal_t2, ongoal_t2_plus, ongoal_t2_minus,
                                poss_t1, poss_t1_plus, poss_t1_minus, poss_t2, poss_t2_plus, poss_t2_minus,
                                corners_t1, corners_t1_plus, corners_t1_minus, corners_t2, corners_t2_plus,
                                corners_t2_minus,
                                attacks_t1, attacks_t1_plus, attacks_t1_minus, attacks_t2, attacks_t2_plus,
                                attacks_t2_minus,
                                fkicks_t1, fkicks_t1_plus, fkicks_t1_minus, fkicks_t2, fkicks_t2_plus, fkicks_t2_minus,
                                throwins_t1, throwins_t1_plus, throwins_t1_minus, throwins_t2, throwins_t2_plus,
                                throwins_t2_minus,
                                offsides_t1, offsides_t1_plus, offsides_t1_minus, offsides_t2, offsides_t2_plus,
                                offsides_t2_minus,
                                fouls_t1, fouls_t1_plus, fouls_t1_minus, fouls_t2, fouls_t2_plus, fouls_t2_minus,
                                yellows_t1, yellows_t1_plus, yellows_t1_minus, yellows_t2, yellows_t2_plus,
                                yellows_t2_minus,
                                win_close, win_close_plus, win_close_minus, draw_close, draw_close_plus,
                                draw_close_minus,
                                lose_close, lose_close_plus, lose_close_minus, total15_close, total15_close_plus,
                                total15_close_minus,
                                total25_close, total25_close_plus, total25_close_minus,
                                win_open, win_open_minus, win_open_plus, draw_open, draw_open_plus, draw_open_minus,
                                lose_open, lose_open_plus, lose_open_minus, total15_open, total15_open_plus,
                                total15_open_minus,
                                total25_open, total25_open_plus, total25_open_minus, selected_model)

        timeline_goals = make_timeline(match_ids)

        #print(match_ids)
        if timeline_goals:
            home_goals_h2 = timeline_goals['home_goals_h2']
            away_goals_h2 = timeline_goals['away_goals_h2']
            goals_h2 = timeline_goals['goals_h2']
            # Generate plots
            home_goals_img = plot_goals(home_goals_h2, title='Home 1st goal(2 half)')
            away_goals_img = plot_goals(away_goals_h2, title='Away 1st goal(2 half)')
            goals_img = plot_goals(goals_h2, title='1st goal(2 half)')
            goals_area_img = plot_area_chart(goals_h2, home_goals_h2, away_goals_h2)
            one_goal_between = plot_1goal_distribution(goals_h2)
            next_goal_img = None
            # Проверяем, что since1 и till1 являются целыми числами
            if isinstance(since1, int) and isinstance(till1, int):
                # Если since2 и till2 не заданы (None), передаем None для их значений
                if since2 is None or till2 is None:
                    next_goal_img = one_more_goal(goals_h2, home_goals_h2, away_goals_h2, since1, till1, team1_group,
                                                  None, None, None)
                # Если since2 и till2 также являются целыми числами, вызываем функцию с обеими группами параметров
                elif isinstance(since2, int) and isinstance(till2, int):
                    next_goal_img = one_more_goal(goals_h2, home_goals_h2, away_goals_h2, since1, till1, team1_group,
                                                  since2, till2, team2_group)


            print()
                # print(home_goals_h2)
                # print(away_goals_h2)
                # print(goals_h2)
        else:
                print("No data found for the specified match_id.")
                home_goals_img = away_goals_img = goals_img = goals_area_img = one_goal_between = next_goal_img = None

    try:
        return render_template(
            'soccer/soccer_live.html',
            form=form,
            additional_form=additional_form,
            odds_form=odds_form,
            teams_form=teams_form,
            percentages=percentages,
            team1_percentages=team1_percentages,
            team2_percentages=team2_percentages,
            country_choices=country_choices,
            total_entries=total_entries,
            overall_probability_over0=overall_probability_over0,
            eval1=eval1,
            gth1=gth1,
            home_goals_img=home_goals_img,
            away_goals_img=away_goals_img,
            goals_img=goals_img,
            goals_area_img=goals_area_img,
            one_goal_between=one_goal_between,
            next_goal_img=next_goal_img
        )
    except:
        return render_template(
            'soccer/soccer_live.html',
            form=form,
            additional_form=additional_form,
            odds_form=odds_form,
            teams_form=teams_form,
            percentages=percentages,
            team1_percentages=team1_percentages,
            team2_percentages=team2_percentages,
            country_choices=country_choices,
            total_entries=total_entries,
            overall_probability_over0=overall_probability_over0

        )


@app.route('/get_leagues_live', methods=['GET'])
def get_leagues_live():
    country_id = request.args.get('country_id')
    if not country_id or country_id == 'None':
        return jsonify([])

    # Получение всех уникальных идентификаторов лиг, где есть матчи и фильтрация по выбранной стране
    leagues = db.session.query(ChampionshipsSoccer.id, ChampionshipsSoccer.league).join(
        SoccerMain, ChampionshipsSoccer.id == SoccerMain.league_id
    ).filter(
        ChampionshipsSoccer.country == country_id  # Фильтрация по выбранной стране
    ).distinct().order_by(ChampionshipsSoccer.league.asc()).all()

    league_choices = [(None, 'All Leagues')] + [(league.id, league.league) for league in leagues]
    return jsonify(league_choices)

@app.route('/get_teams_live', methods=['GET'])
def get_teams_live():
    league_id = request.args.get('league_id')
    (f"Received league_id: {league_id}")

    if not league_id or league_id == 'null':
        return jsonify([])  # Вернуть пустой список или другой ответ

    # Получение уникальных команд в рамках лиги
    teams = db.session.query(SoccerMain.team_home).filter(
        SoccerMain.league_id == league_id
    ).distinct().order_by(SoccerMain.team_home.asc()).all()

    team_choices = [(team.team_home,) for team in teams]
    return jsonify(team_choices)


@app.route('/soccer_live_form')
def soccer_live_form():
    return render_template('soccer/soccer_live_form.html')

@app.route('/perform_query/<int:query_number>', methods=['POST'])
def perform_query(query_number):
    # Обработка запроса и возврат JSON-ответа
    result = your_query_function(query_number)
    return jsonify(result)

http = urllib3.PoolManager(
    cert_reqs="CERT_REQUIRED",
    ca_certs=certifi.where()
)


PUBLIC_URL = os.getenv('SOCCER_LIVE_URL')
CACHE_FILE = 'cache.json'
CACHE_TIMESTAMP_FILE = 'cache_timestamp.txt'
CACHE_EXPIRATION_TIME = 20
def load_cached_data():
    """Загружает данные из кеша, если кеш валиден."""
    if os.path.exists(CACHE_FILE) and os.path.exists(CACHE_TIMESTAMP_FILE):
        with open(CACHE_TIMESTAMP_FILE, 'r') as f:
            timestamp = float(f.read().strip())
        if time.time() - timestamp < CACHE_EXPIRATION_TIME:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    return None

def save_to_cache(data):
    """Сохраняет данные в кеш и обновляет метку времени."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)
    with open(CACHE_TIMESTAMP_FILE, 'w') as f:
        f.write(str(time.time()))

def fetch_matches_from_first_server():
    cached_data = load_cached_data()
    if cached_data is not None:
        return cached_data

    try:
        response = http.request('GET', PUBLIC_URL)
        data = json.loads(response.data.decode('utf-8'))
        processed_data = []
        for match in data:
            processed_data.append({
                'match_id': match.get('match_id'),
                'home_team': match.get('home_team'),
                'away_team': match.get('away_team'),
                'league': match.get('league'),
                'country': match.get('country'),
                'half': match.get('half'),
                'current_minute': match.get('current_minute', 'Halftime'),
                'home_score': match.get('home_score', 0),
                'away_score': match.get('away_score', 0),
                'home_score_first_half': match.get('home_score_first_half', 0),
                'away_score_first_half': match.get('away_score_first_half', 0),
                'home_score_second_half': match.get('home_score_second_half', 0),
                'away_score_second_half': match.get('away_score_second_half', 0),
                'stats': match.get('stats', {})
            })
        save_to_cache(processed_data)
        return processed_data
    except (urllib3.exceptions.HTTPError, urllib3.exceptions.NewConnectionError) as e:
        print(f"Error fetching data from first server: {e}")
        return cached_data  # Возвращаем старые данные из кеша, если есть
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON data: {e}")
        return cached_data  # Возвращаем старые данные из кеша, если есть
    except Exception as e:
        print(f"Unexpected error: {e}")
        return cached_data  # Возвращаем старые данные из кеша, если есть

@app.route('/current_matches', methods=['GET', 'POST'])
def current_matches():
    if request.method == 'POST':
        return '', 200
    matches_data = fetch_matches_from_first_server()
    if not matches_data:
        return render_template('current_matches.html', matches=None)
    return render_template('current_matches.html', matches=matches_data)


@app.route('/live_matches_table')
def live_matches_table():
    matches_data = fetch_matches_from_first_server()

    if not matches_data:
        return render_template('soccer/live_matches_table.html', matches=None)

    return render_template('soccer/live_matches_table.html', matches=matches_data)


@app.route('/info')
def info():
    return render_template('info.html')


@app.route('/soccer_prematch', methods=['GET', 'POST'])
def soccer_prematch():
    if request.method == 'POST':
        # Получение данных из POST-запроса
        data = request.json  # Если данные отправлены в формате JSON
        print(data)
        if not data:
            data = request.form  # Если данные отправлены в формате URL-encoded

        # Извлечение переменных из запроса
        country = data.get('country', '').strip()
        league = data.get('league', '').strip()
        team = data.get('team', '').strip()
        opponent = data.get('opponent', '').strip()
        sportbook = data.get('sportbook', '').strip().lower()
        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')

        # Коэффициенты команды 1
        team1_win = safe_float(data.get('team1-win', 0))
        team1_win_minus = safe_float(data.get('team1-win-minus', 0))
        team1_win_plus = safe_float(data.get('team1-win-plus', 0))
        team1_win_close = safe_float(data.get('team1-win-close', 0))
        team1_win_close_minus = safe_float(data.get('team1-win-close-minus', 0))
        team1_win_close_plus = safe_float(data.get('team1-win-close-plus', 0))

        team1_draw = safe_float(data.get('team1-draw', ''))
        team1_draw_minus = safe_float(data.get('team1-draw-minus', ''))
        team1_draw_plus = safe_float(data.get('team1-draw-plus', ''))
        team1_draw_close = safe_float(data.get('team1-draw-close', ''))
        team1_draw_close_minus = safe_float(data.get('team1-draw-close-minus', ''))
        team1_draw_close_plus = safe_float(data.get('team1-draw-close-plus', ''))

        team1_loss = safe_float(data.get('team1-loss', ''))
        team1_loss_minus = safe_float(data.get('team1-loss-minus', ''))
        team1_loss_plus = safe_float(data.get('team1-loss-plus', ''))
        team1_loss_close = safe_float(data.get('team1-loss-close', ''))
        team1_loss_close_minus = safe_float(data.get('team1-loss-close-minus', ''))
        team1_loss_close_plus = safe_float(data.get('team1-loss-close-plus', ''))

        team1_over_1_5 = safe_float(data.get('team1-over-1.5', ''))
        team1_over_1_5_minus = safe_float(data.get('team1-over-1.5-minus', ''))
        team1_over_1_5_plus = safe_float(data.get('team1-over-1.5-plus', ''))
        team1_over_1_5_close = safe_float(data.get('team1-over-1.5-close', ''))
        team1_over_1_5_close_minus = safe_float(data.get('team1-over-1.5-close-minus', ''))
        team1_over_1_5_close_plus = safe_float(data.get('team1-over-1.5-close-plus', ''))

        team1_over_2_5 = safe_float(data.get('team1-over-2.5', ''))
        team1_over_2_5_minus = safe_float(data.get('team1-over-2.5-minus', ''))
        team1_over_2_5_plus = safe_float(data.get('team1-over-2.5-plus', ''))
        team1_over_2_5_close = safe_float(data.get('team1-over-2.5-close', ''))
        team1_over_2_5_close_minus = safe_float(data.get('team1-over-2.5-close-minus', ''))
        team1_over_2_5_close_plus = safe_float(data.get('team1-over-2.5-close-plus', ''))
        print('/////')
        print(team1_win_close, type(team1_win_close))
        print('/////')
        # Конвертация строковых дат в объекты datetime
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date_from format, should be YYYY-MM-DD'}), 400

        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date_to format, should be YYYY-MM-DD'}), 400

        sportbook_models = {
            '1xbet': XbetOdds,
            'bet365': Bet365Odds,
            'unibet': UnibetOdds
        }
        selected_model = sportbook_models.get(sportbook)

        if not selected_model:
            return jsonify({'error': 'Invalid sportbook'}), 400

        ind_info_team = get_ind_goals_team(country, league, team, opponent, sportbook, date_from, date_to,
                  team1_win, team1_win_minus, team1_win_plus, team1_win_close,
                  team1_win_close_minus, team1_win_close_plus, team1_draw,
                  team1_draw_minus, team1_draw_plus, team1_draw_close,
                  team1_draw_close_minus, team1_draw_close_plus, team1_loss,
                  team1_loss_minus, team1_loss_plus, team1_loss_close,
                  team1_loss_close_minus, team1_loss_close_plus, team1_over_1_5,
                  team1_over_1_5_minus, team1_over_1_5_plus, team1_over_1_5_close,
                  team1_over_1_5_close_minus, team1_over_1_5_close_plus, team1_over_2_5,
                  team1_over_2_5_minus, team1_over_2_5_plus, team1_over_2_5_close,
                  team1_over_2_5_close_minus, team1_over_2_5_close_plus, selected_model)

        ind_info_opponent = get_ind_goals_opponent(country, league, team, opponent, sportbook, date_from, date_to,
                  team1_win, team1_win_minus, team1_win_plus, team1_win_close,
                  team1_win_close_minus, team1_win_close_plus, team1_draw,
                  team1_draw_minus, team1_draw_plus, team1_draw_close,
                  team1_draw_close_minus, team1_draw_close_plus, team1_loss,
                  team1_loss_minus, team1_loss_plus, team1_loss_close,
                  team1_loss_close_minus, team1_loss_close_plus, team1_over_1_5,
                  team1_over_1_5_minus, team1_over_1_5_plus, team1_over_1_5_close,
                  team1_over_1_5_close_minus, team1_over_1_5_close_plus, team1_over_2_5,
                  team1_over_2_5_minus, team1_over_2_5_plus, team1_over_2_5_close,
                  team1_over_2_5_close_minus, team1_over_2_5_close_plus, selected_model)

        ind_info_vs = get_ind_goals_vs(country, league, team, opponent, sportbook, date_from, date_to,
                  team1_win, team1_win_minus, team1_win_plus, team1_win_close,
                  team1_win_close_minus, team1_win_close_plus, team1_draw,
                  team1_draw_minus, team1_draw_plus, team1_draw_close,
                  team1_draw_close_minus, team1_draw_close_plus, team1_loss,
                  team1_loss_minus, team1_loss_plus, team1_loss_close,
                  team1_loss_close_minus, team1_loss_close_plus, team1_over_1_5,
                  team1_over_1_5_minus, team1_over_1_5_plus, team1_over_1_5_close,
                  team1_over_1_5_close_minus, team1_over_1_5_close_plus, team1_over_2_5,
                  team1_over_2_5_minus, team1_over_2_5_plus, team1_over_2_5_close,
                  team1_over_2_5_close_minus, team1_over_2_5_close_plus, selected_model)



        print(ind_info_team)
        print()
        print(ind_info_opponent)
        print()
        print(ind_info_vs)

        # return jsonify({'message': 'Data received successfully!', 'results': [str(ind_goal) for ind_goal in ind_goals]}), 200
        return jsonify({
            'ind_info_team': ind_info_team,
            'ind_info_opponent': ind_info_opponent,
            'ind_info_vs': ind_info_vs
        })
    # Если метод GET, просто отобразите страницу
    return render_template('soccer/soccer_prematch.html')