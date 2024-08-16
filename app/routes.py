from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from sqlalchemy import text, func
from urllib.parse import urlsplit
from app import app, db
from app.forms import LoginForm, RegistrationForm, ResendConfirmationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.forms import SoccerLiveInput, SoccerLiveAdditionalInput, SoccerMainOddsInput, CountryLeageTeamBook
from app.models import User, ChampionshipsSoccer, SoccerMain, XbetOdds, Bet365Odds, UnibetOdds, SoccerTimeline
from app.email import send_email, send_password_reset_email
from app.spare_func import safe_float, count_odds_diff
from itsdangerous import URLSafeTimedSerializer
import os
from datetime import datetime

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

@app.route('/under_construction')
def under_construction():
    return render_template('under_construction.html')

@app.route('/soccer')
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
    if not league:
        return jsonify({"error": "League parameter is required"}), 400

    try:
        # Получаем список команд из модели SoccerMain для заданной лиги
        teams = db.session.query(SoccerMain.team_home).filter(
            SoccerMain.league_name == league
        ).distinct().union(
            db.session.query(SoccerMain.team_away).filter(
                SoccerMain.league_name == league
            ).distinct()
        ).order_by(SoccerMain.team_home).all()

        # Преобразуем результат в список строк
        teams_list = [team[0] for team in teams if team[0] is not None]
        return jsonify(teams_list)
    except Exception as e:
        print('Error fetching teams:', e)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/process-form', methods=['POST'])
def process_form():
    data = request.get_json()
    print(data)

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

    print(opponent ,date_from, date_to, position, over_1_5_open - over_1_5_open_minus,
          over_1_5_open + over_1_5_open_plus ,over_2_5_open - over_2_5_open_minus, over_2_5_open + over_2_5_open_plus)

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
    print(country, league, team, sportbook, win_open - win_open_minus, win_open + win_open_plus,
          draw_open - draw_open_minus, draw_open + draw_open_plus, loss_open - loss_open_minus, loss_open + loss_open_plus)

    for result in results:
        if result:
            print(result)
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

            # print(f"{match['date']}. {match['team_home']} vs {match['team_away']}, "
            #       f"Score: {match['home_score_ft']}-{match['away_score_ft']}, WinOpen:"
            #       f" {match['win_home_open']}, WinClose: {match['win_home_close']} LoseOpen:{match['win_away_open']} Loselose:{match['win_away_close']}")
            print(match['total25_diff'])

    print(len(response_list))
    if not response_list:
        response = {'error': 'No matching records found'}
    else:
        response = response_list
    response_list.reverse()
    return jsonify(response_list)


@app.route('/soccer_live', methods=['GET', 'POST'])
def soccer_live():
    form = SoccerLiveInput()
    additional_form = SoccerLiveAdditionalInput()
    odds_form = SoccerMainOddsInput()
    teams_form = CountryLeageTeamBook()

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

        sportbook = teams_form.sportsbook.data
        sportbook_models = {
            '1xbet': XbetOdds,
            'bet365': Bet365Odds,
            'unibet': UnibetOdds
        }
        selected_model = sportbook_models.get(sportbook.lower())
        print(sportbook)

        query = db.session.query(
            (SoccerTimeline.score_t1_h2 + SoccerTimeline.score_t2_h2).label('total_score_h2'),
            func.count().label('count')
        ).filter(
            SoccerTimeline.score_t1_h1 == score_t1_form,
            SoccerTimeline.score_t2_h1 == score_t2_form
        ).join(
            selected_model, SoccerTimeline.match_id == selected_model.match_id
        )

        # Фильтрация по коэффициентам закрытия для победы и ничьи
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

        print(draw_close, draw_close_plus, draw_close_minus)

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

        # Фильтрация по коэффициентам открытия для победы и ничьи
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
        print(draw_open, draw_open_plus, draw_open_minus)

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

        total_entries = sum(entry.count for entry in soccer_timeline_entries)  # Подсчет всех матчей

        if soccer_timeline_entries:
            percentages = [
                (entry.total_score_h2, entry.count, (entry.count / total_entries) * 100)
                for entry in soccer_timeline_entries
            ]

        # Аналогичная фильтрация и расчеты для команд
        team1_entries = db.session.query(
            SoccerTimeline.score_t1_h2.label('team1_score_h2'),
            func.count().label('count')
        ).join(
            selected_model, SoccerTimeline.match_id == selected_model.match_id
        ).filter(
            SoccerTimeline.score_t1_h1 == score_t1_form,
            SoccerTimeline.score_t2_h1 == score_t2_form
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

        team2_entries = db.session.query(
            SoccerTimeline.score_t2_h2.label('team2_score_h2'),
            func.count().label('count')
        ).join(
            selected_model, SoccerTimeline.match_id == selected_model.match_id
        ).filter(
            SoccerTimeline.score_t1_h1 == score_t1_form,
            SoccerTimeline.score_t2_h1 == score_t2_form
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
        # Расчет вероятности того, что хотя бы одна команда забьет гол
        if team1_percentages and team2_percentages:
            # Преобразование процентных данных в вероятности
            team1_goal_over0 = [entry[2] / 100 for entry in team1_percentages if entry[0] == 0]
            team2_goal_over0 = [entry[2] / 100 for entry in team2_percentages if entry[0] == 0]

            print(f"Team 1 Goal Over 0: {team1_goal_over0}")
            print(f"Team 2 Goal Over 0: {team2_goal_over0}")

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
    print(country_id)

    if not country_id:
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
    print(league_id)

    if not league_id:
        return jsonify([])

    # Получение команд из таблицы SoccerMain, фильтрация по выбранной лиге и сортировка по алфавиту
    teams = db.session.query(SoccerMain.team_home).join(
        ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
    ).filter(
        SoccerMain.league_id == league_id
    ).distinct().order_by(SoccerMain.team_home.asc()).all()

    team_choices = [team.team_home for team in teams]
    print(team_choices)
    return jsonify(team_choices)


@app.route('/success')
def success():
    return "Form submitted successfully!"
