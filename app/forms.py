from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from wtforms.validators import InputRequired, Optional
import sqlalchemy as sa
from app import db
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ResendConfirmationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Resend Confirmation')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class SoccerLiveInput(FlaskForm):
    score_t1 = IntegerField('Score Team 1', validators=[Optional()])
    score_t2 = IntegerField('Score Team 2', validators=[Optional()])

    xg_t1 = FloatField('xG 1', validators=[Optional()])
    xg_t1_plus = FloatField('Plus', validators=[Optional()])
    xg_t1_minus = FloatField('Minus', validators=[Optional()])

    xg_t2 = FloatField('xG 2', validators=[Optional()])
    xg_t2_plus = FloatField('Plus', validators=[Optional()])
    xg_t2_minus = FloatField('Minus', validators=[Optional()])

    possesion_t1 = IntegerField('Possession Team 1', validators=[Optional()])
    possesion_t1_plus = IntegerField('Possession Team 1 Plus', validators=[Optional()])
    possesion_t1_minus = IntegerField('Possession Team 1 Minus', validators=[Optional()])

    possesion_t2 = IntegerField('Possession Team 2', validators=[Optional()])
    possesion_t2_plus = IntegerField('Possession Team 2 Plus', validators=[Optional()])
    possesion_t2_minus = IntegerField('Possession Team 2 Minus', validators=[Optional()])

    shots_t1 = IntegerField('Shots Team 1', validators=[Optional()])
    shots_t1_plus = IntegerField('Shots Team 1 Plus', validators=[Optional()])
    shots_t1_minus = IntegerField('Shots Team 1 Minus', validators=[Optional()])

    shots_t2 = IntegerField('Shots Team 2', validators=[Optional()])
    shots_t2_plus = IntegerField('Shots Team 2 Plus', validators=[Optional()])
    shots_t2_minus = IntegerField('Shots Team 2 Minus', validators=[Optional()])

    on_goal_t1 = IntegerField('On Goal Team 1', validators=[Optional()])
    on_goal_t1_plus = IntegerField('On Goal Team 1 Plus', validators=[Optional()])
    on_goal_t1_minus = IntegerField('On Goal Team 1 Minus', validators=[Optional()])

    on_goal_t2 = IntegerField('On Goal Team 2', validators=[Optional()])
    on_goal_t2_plus = IntegerField('On Goal Team 2 Plus', validators=[Optional()])
    on_goal_t2_minus = IntegerField('On Goal Team 2 Minus', validators=[Optional()])

    corners_t1 = IntegerField('Corners Team 1', validators=[Optional()])
    corners_t1_plus = IntegerField('Corners Team 1 Plus', validators=[Optional()])
    corners_t1_minus = IntegerField('Corners Team 1 Minus', validators=[Optional()])

    corners_t2 = IntegerField('Corners Team 2', validators=[Optional()])
    corners_t2_plus = IntegerField('Corners Team 2 Plus', validators=[Optional()])
    corners_t2_minus = IntegerField('Corners Team 2 Minus', validators=[Optional()])

    attacks_t1 = IntegerField('Attacks Team 1', validators=[Optional()])
    attacks_t1_plus = IntegerField('Attacks Team 1 Plus', validators=[Optional()])
    attacks_t1_minus = IntegerField('Attacks Team 1 Minus', validators=[Optional()])

    attacks_t2 = IntegerField('Attacks Team 2', validators=[Optional()])
    attacks_t2_plus = IntegerField('Attacks Team 2 Plus', validators=[Optional()])
    attacks_t2_minus = IntegerField('Attacks Team 2 Minus', validators=[Optional()])

    submit = SubmitField('Submit')

class SoccerLiveAdditionalInput(FlaskForm):

    freekicks_t1 = IntegerField('Free Kicks Team 1', validators=[Optional()])
    freekicks_t1_plus = IntegerField('Free Kicks Team 1 Plus', validators=[Optional()])
    freekicks_t1_minus = IntegerField('Free Kicks Team 1 Minus', validators=[Optional()])
    freekicks_t2 = IntegerField('Free Kicks Team 2', validators=[Optional()])
    freekicks_t2_plus = IntegerField('Free Kicks Team 2 Plus', validators=[Optional()])
    freekicks_t2_minus = IntegerField('Free Kicks Team 2 Minus', validators=[Optional()])

    throw_ins_t1 = IntegerField('Throw-ins Team 1', validators=[Optional()])
    throw_ins_t1_plus = IntegerField('Throw-ins Team 1 Plus', validators=[Optional()])
    throw_ins_t1_minus = IntegerField('Throw-ins Team 1 Minus', validators=[Optional()])
    throw_ins_t2 = IntegerField('Throw-ins Team 2', validators=[Optional()])
    throw_ins_t2_plus = IntegerField('Throw-ins Team 2 Plus', validators=[Optional()])
    throw_ins_t2_minus = IntegerField('Throw-ins Team 2 Minus', validators=[Optional()])

    offsides_t1 = IntegerField('Offsides Team 1', validators=[Optional()])
    offsides_t1_plus = IntegerField('Offsides Team 1 Plus', validators=[Optional()])
    offsides_t1_minus = IntegerField('Offsides Team 1 Minus', validators=[Optional()])
    offsides_t2 = IntegerField('Offsides Team 2', validators=[Optional()])
    offsides_t2_plus = IntegerField('Offsides Team 2 Plus', validators=[Optional()])
    offsides_t2_minus = IntegerField('Offsides Team 2 Minus', validators=[Optional()])

    fouls_t1 = IntegerField('Fouls Team 1', validators=[Optional()])
    fouls_t1_plus = IntegerField('Fouls Team 1 Plus', validators=[Optional()])
    fouls_t1_minus = IntegerField('Fouls Team 1 Minus', validators=[Optional()])
    fouls_t2 = IntegerField('Fouls Team 2', validators=[Optional()])
    fouls_t2_plus = IntegerField('Fouls Team 2 Plus', validators=[Optional()])
    fouls_t2_minus = IntegerField('Fouls Team 2 Minus', validators=[Optional()])

    yellows_t1 = IntegerField('Yellow Cards Team 1', validators=[Optional()])
    yellows_t1_plus = IntegerField('Yellow Cards Team 1 Plus', validators=[Optional()])
    yellows_t1_minus = IntegerField('Yellow Cards Team 1 Minus', validators=[Optional()])
    yellows_t2 = IntegerField('Yellow Cards Team 2', validators=[Optional()])
    yellows_t2_plus = IntegerField('Yellow Cards Team 2 Plus', validators=[Optional()])
    yellows_t2_minus = IntegerField('Yellow Cards Team 2 Minus', validators=[Optional()])

class SoccerMainOddsInput(FlaskForm):
    win_t1 = FloatField('Win 1', validators=[Optional()])
    win_t1_plus = FloatField('+/-', validators=[Optional()])
    win_t1_minus = FloatField('+/-', validators=[Optional()])
    win_t1_open = FloatField('Win 1', validators=[Optional()])
    win_t1_open_plus = FloatField('Win 1', validators=[Optional()])
    win_t1_open_minus = FloatField('Win 1', validators=[Optional()])
    draw = FloatField('Draw', validators=[Optional()])
    draw_plus = FloatField('+/-', validators=[Optional()])
    draw_minus = FloatField('+/-', validators=[Optional()])
    draw_open = FloatField('Draw', validators=[Optional()])
    draw_open_plus = FloatField('+/-', validators=[Optional()])
    draw_open_minus = FloatField('+/-', validators=[Optional()])
    win_t2 = FloatField('Win 2', validators=[Optional()])
    win_t2_plus = FloatField('Win 2', validators=[Optional()])
    win_t2_minus = FloatField('Win 2', validators=[Optional()])
    win_t2_open = FloatField('Win 2', validators=[Optional()])
    win_t2_open_plus = FloatField('+/-', validators=[Optional()])
    win_t2_open_minus = FloatField('+/-', validators=[Optional()])
    total_15 = FloatField('Over 1.5', validators=[Optional()])
    total_15_plus = FloatField('Over 1.5', validators=[Optional()])
    total_15_minus = FloatField('Over 1.5', validators=[Optional()])
    total_15_open = FloatField('Over 1.5', validators=[Optional()])
    total_15_open_plus= FloatField('+', validators=[Optional()])
    total_15_open_minus = FloatField('-', validators=[Optional()])
    total_25 = FloatField('Over 2.5', validators=[Optional()])
    total_25_plus = FloatField('+', validators=[Optional()])
    total_25_minus = FloatField('-', validators=[Optional()])
    total_25_open = FloatField('Over 2.5', validators=[Optional()])
    total_25_open_plus = FloatField('Over 2.5', validators=[Optional()])
    total_25_open_minus = FloatField('Over 2.5', validators=[Optional()])

class CountryLeageTeamBook(FlaskForm):
    country = StringField('Country', validators=[Optional()])
    league = StringField('League', validators=[Optional()])
    team_home = StringField('Team 1', validators=[Optional()])
    team_away = StringField('Team 2', validators=[Optional()])
    sportsbook = StringField('Sportbook', validators=[Optional()])