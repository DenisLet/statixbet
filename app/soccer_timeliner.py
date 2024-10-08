from app.models import User, ChampionshipsSoccer, SoccerMain, XbetOdds, Bet365Odds, UnibetOdds, SoccerTimeline
from app.models import SoccerHalf1Stats, SoccerHalf2Stats
from sqlalchemy import func
from app import app, db


def make_timeline(match_ids):
    # Query to retrieve home_goals_h2 and away_goals_h2 arrays based on match_ids
    timelines = db.session.query(
        SoccerTimeline.home_goals_h2,
        SoccerTimeline.away_goals_h2
    ).filter(SoccerTimeline.match_id.in_(match_ids)).all()

    if timelines:
        home_goals_h2 = []
        away_goals_h2 = []
        goals_h2 = []

        # Iterate through the results to combine them
        for timeline in timelines:
            if timeline.home_goals_h2 is None:
                timeline.home_goals_h2 = []
            if timeline.away_goals_h2 is None:
                timeline.away_goals_h2 = []

            # Добавляем список голов для каждого матча в home_goals_h2 и away_goals_h2
            home_goals_h2.append(timeline.home_goals_h2)
            away_goals_h2.append(timeline.away_goals_h2)

            # Create a list of lists for each match
            match_goals = timeline.home_goals_h2 + timeline.away_goals_h2
            goals_h2.append(match_goals)

        return {
            'home_goals_h2': home_goals_h2,
            'away_goals_h2': away_goals_h2,
            'goals_h2': goals_h2
        }
    else:
        # Если нет данных, возвращаем списки списков с пустыми значениями
        return {
            'home_goals_h2': [[] for _ in match_ids],
            'away_goals_h2': [[] for _ in match_ids],
            'goals_h2': [[] for _ in match_ids]
        }


def make_timeline_yc(match_ids):
    # Query to retrieve home_goals_h2 and away_goals_h2 arrays based on match_ids
    timelines = db.session.query(
        SoccerTimeline.home_yellow_h2,
        SoccerTimeline.away_yellow_h2
    ).filter(SoccerTimeline.match_id.in_(match_ids)).all()

    if timelines:
        home_yc_h2 = []
        away_yc_h2 = []
        yc_h2 = []

        # Iterate through the results to combine them
        for timeline in timelines:
            if timeline.home_yellow_h2 is None:
                timeline.home_yellow_h2 = []
            if timeline.away_yellow_h2 is None:
                timeline.away_yellow_h2 = []

            # Добавляем список голов для каждого матча в home_goals_h2 и away_goals_h2
            home_yc_h2.append(timeline.home_yellow_h2)
            away_yc_h2.append(timeline.away_yellow_h2)

            # Create a list of lists for each match
            match_yc = timeline.home_yellow_h2 + timeline.away_yellow_h2
            yc_h2.append(match_yc)

        return {
            'home_yc_h2': home_yc_h2,
            'away_yc_h2': away_yc_h2,
            'yc_h2': yc_h2
        }
    else:
        # Если нет данных, возвращаем списки списков с пустыми значениями
        return {
            'home_yc_h2': [[] for _ in match_ids],
            'away_yc_h2': [[] for _ in match_ids],
            'yc_h2': [[] for _ in match_ids]
        }