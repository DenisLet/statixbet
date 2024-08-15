from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.dialects.postgresql import ARRAY
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login
import jwt
from time import time
from app import app

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    available_requests: so.Mapped[int] = so.mapped_column(sa.Integer, default=200)
    is_admin: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)
    is_confirmed = db.Column(db.Boolean, default=False)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(User, id)

    def __repr__(self):
        return 'User <{}>'.format(self.username)


class ChampionshipsSoccer(db.Model):
    __tablename__ = 'championships_soccer'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    country: so.Mapped[str] = so.mapped_column(sa.String(64))
    gender: so.Mapped[str] = so.mapped_column(sa.String(64))
    league: so.Mapped[str] = so.mapped_column(sa.String(64))
    link: so.Mapped[str] = so.mapped_column(sa.String(256))

    def __repr__(self):
        return f'<ChampionshipsSoccer {self.country} - {self.league}>'


class SoccerMain(db.Model):
    __tablename__ = 'soccer_main'

    match_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    league_id: so.Mapped[int] = so.mapped_column(sa.Integer)
    match_date: so.Mapped[sa.Date] = so.mapped_column(sa.Date)
    start_time: so.Mapped[sa.Time] = so.mapped_column(sa.Time)
    team_home: so.Mapped[str] = so.mapped_column(sa.String(64))
    team_away: so.Mapped[str] = so.mapped_column(sa.String(64))
    league_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    stage: so.Mapped[str] = so.mapped_column(sa.String(64))
    home_score_ft: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, nullable=True)
    away_score_ft: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, nullable=True)
    total_ft: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer, nullable=True)
    final: so.Mapped[str] = so.mapped_column(sa.String(64))

    def __repr__(self):
        return f'<SoccerMain Match {self.match_id} - {self.team_home} vs {self.team_away}>'


class XbetOdds(db.Model):
    __tablename__ = 'xbet_odds'

    match_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    win_home_open: so.Mapped[float] = so.mapped_column(sa.Float)
    win_home_close: so.Mapped[float] = so.mapped_column(sa.Float)
    draw_open: so.Mapped[float] = so.mapped_column(sa.Float)
    draw_close: so.Mapped[float] = so.mapped_column(sa.Float)
    win_away_open: so.Mapped[float] = so.mapped_column(sa.Float)
    win_away_close: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_1_5_open: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_1_5_close: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_2_5_open: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_2_5_close: so.Mapped[float] = so.mapped_column(sa.Float)

    def __repr__(self):
        return f'<XbetOdds Match {self.match_id, self.win_home_open, self.win_home_close}>'


class Bet365Odds(db.Model):
    __tablename__ = 'bet365_odds'

    match_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    win_home_open: so.Mapped[float] = so.mapped_column(sa.Float)
    win_home_close: so.Mapped[float] = so.mapped_column(sa.Float)
    draw_open: so.Mapped[float] = so.mapped_column(sa.Float)
    draw_close: so.Mapped[float] = so.mapped_column(sa.Float)
    win_away_open: so.Mapped[float] = so.mapped_column(sa.Float)
    win_away_close: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_1_5_open: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_1_5_close: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_2_5_open: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_2_5_close: so.Mapped[float] = so.mapped_column(sa.Float)

    def __repr__(self):
        return f'<Bet365Odds Match {self.match_id,self.win_home_open, self.win_home_close}>'


class UnibetOdds(db.Model):
    __tablename__ = 'unibet_odds'

    match_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    win_home_open: so.Mapped[float] = so.mapped_column(sa.Float)
    win_home_close: so.Mapped[float] = so.mapped_column(sa.Float)
    draw_open: so.Mapped[float] = so.mapped_column(sa.Float)
    draw_close: so.Mapped[float] = so.mapped_column(sa.Float)
    win_away_open: so.Mapped[float] = so.mapped_column(sa.Float)
    win_away_close: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_1_5_open: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_1_5_close: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_2_5_open: so.Mapped[float] = so.mapped_column(sa.Float)
    odds_2_5_close: so.Mapped[float] = so.mapped_column(sa.Float)

    def __repr__(self):
        return f'<UnibetOdds Match {self.match_id,self.win_home_open, self.win_home_close}>'



class SoccerHalf1Stats(db.Model):
    __tablename__ = 'soccer_half1_stats'

    match_id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    home_xg: so.Mapped[float] = so.mapped_column(sa.Float)
    home_possession: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_attempts: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_shots: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_corners: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_freekicks: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_offsides: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_passes: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_throw_ins: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_fouls: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_yellow: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_tackles: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_dangerous_attacks: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_xg: so.Mapped[float] = so.mapped_column(sa.Float)
    away_possession: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_attempts: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_shots: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_corners: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_freekicks: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_offsides: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_passes: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_throw_ins: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_fouls: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_yellow: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_tackles: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_dangerous_attacks: so.Mapped[int] = so.mapped_column(sa.Integer)

    def __repr__(self):
        return f'<SoccerHalf1Stats Match {self.match_id}>'


class SoccerHalf2Stats(db.Model):
    __tablename__ = 'soccer_half2_stats'

    match_id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    home_xg: so.Mapped[float] = so.mapped_column(sa.Float)
    home_possession: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_attempts: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_shots: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_corners: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_freekicks: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_offsides: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_passes: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_throw_ins: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_fouls: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_yellow: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_tackles: so.Mapped[int] = so.mapped_column(sa.Integer)
    home_dangerous_attacks: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_xg: so.Mapped[float] = so.mapped_column(sa.Float)
    away_possession: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_attempts: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_shots: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_corners: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_freekicks: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_offsides: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_passes: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_throw_ins: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_fouls: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_yellow: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_tackles: so.Mapped[int] = so.mapped_column(sa.Integer)
    away_dangerous_attacks: so.Mapped[int] = so.mapped_column(sa.Integer)

    def __repr__(self):
        return f'<SoccerHalf1Stats Match {self.match_id}>'


class SoccerTimeline(db.Model):
    __tablename__ = 'soccer_timeline'

    match_id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    home_goals_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    home_goals_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    home_yellow_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    home_yellow_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    home_red_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    home_red_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    home_disallowed_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    home_disallowed_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    home_second_yellow_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    home_second_yellow_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    home_red_2yellow_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    home_red_2yellow_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_goals_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_goals_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_yellow_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_yellow_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_red_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_red_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_disallowed_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_disallowed_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_second_yellow_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_second_yellow_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_red_2yellow_h1: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))
    away_red_2yellow_h2: so.Mapped[List[int]] = so.mapped_column(ARRAY(sa.Integer))

    score_t1_h1: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    score_t2_h1: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    score_t1_h2: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    score_t2_h2: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
