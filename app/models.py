from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
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