from app.models import User, ChampionshipsSoccer, SoccerMain, XbetOdds, Bet365Odds, UnibetOdds, SoccerTimeline
from app.models import SoccerHalf1Stats, SoccerHalf2Stats
from sqlalchemy import func
from app import app, db


def process_corners(
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
):
    corners_query = db.session.query(
        (SoccerHalf2Stats.home_corners + SoccerHalf2Stats.away_corners).label('total_corners_h2'),
        func.count().label('count')
    ).join(
        SoccerTimeline, SoccerTimeline.match_id == SoccerHalf2Stats.match_id
    ).join(
        selected_model, SoccerTimeline.match_id == selected_model.match_id
    ).join(
        SoccerHalf1Stats, SoccerTimeline.match_id == SoccerHalf1Stats.match_id
    ).filter(
        SoccerHalf2Stats.home_corners >= 0,
        SoccerHalf2Stats.away_corners >= 0
    )

    # Если нужно использовать DISTINCT, его лучше применять позже, а не в самом начале.
    if country and country != 'None':
        corners_query = corners_query.join(
            SoccerMain, SoccerTimeline.match_id == SoccerMain.match_id
        ).join(
            ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
        ).filter(
            ChampionshipsSoccer.country == country
        )
    else:
        corners_query = corners_query.distinct()

    if league and league != 'null':
        corners_query = corners_query.filter(
            SoccerMain.league_id == league
        )

    if team1 and team1 != '':
        corners_query = corners_query.filter(
            SoccerMain.team_home == team1
        )

    if team2 and team2 != '':
        corners_query = corners_query.filter(
            SoccerMain.team_away == team2
        )

    corners_entries = corners_query.group_by(
        'total_corners_h2'
    ).order_by(
        'total_corners_h2'
    ).all()

    total_corners_entries = sum(entry.count for entry in corners_entries)

    corners_percentages = [
        (entry.total_corners_h2, entry.count, (entry.count / total_corners_entries) * 100)
        for entry in corners_entries
    ]

    # Подсчет процентов, которые больше текущего количества угловых
    cumulative_percentage = 0
    result_table = []

    for i, (total_corners, count, percentage) in enumerate(corners_percentages):
        if i < len(corners_percentages) - 1:
            greater_percentage = 100 - cumulative_percentage - percentage
        else:
            greater_percentage = None

        result_table.append((total_corners, count, percentage, greater_percentage))
        cumulative_percentage += percentage

    print(corners_percentages)

    return total_corners_entries, result_table