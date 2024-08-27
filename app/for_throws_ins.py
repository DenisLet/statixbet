from app.models import User, ChampionshipsSoccer, SoccerMain, XbetOdds, Bet365Odds, UnibetOdds, SoccerTimeline
from app.models import SoccerHalf1Stats, SoccerHalf2Stats
from sqlalchemy import func
from app import app, db


def process_throws_ins(
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
    throws_query = db.session.query(
        (SoccerHalf2Stats.home_throw_ins + SoccerHalf2Stats.away_throw_ins).label('total_throws_h2'),
        func.count().label('count')
    ).join(
        SoccerTimeline, SoccerTimeline.match_id == SoccerHalf2Stats.match_id
    ).join(
        selected_model, SoccerTimeline.match_id == selected_model.match_id
    ).join(
        SoccerHalf1Stats, SoccerTimeline.match_id == SoccerHalf1Stats.match_id
    ).filter(
        (SoccerTimeline.score_t1_h1 == score_t1_form) if score_t1_form else True,
        (SoccerTimeline.score_t2_h1 == score_t2_form) if score_t2_form else True,
        SoccerHalf2Stats.home_throw_ins.between(0, 40),
        SoccerHalf2Stats.away_throw_ins.between(0, 40)
    )

    # Фильтрация по странам, лигам и командам
    if country and country != 'None':
        throws_query = throws_query.join(
            SoccerMain, SoccerTimeline.match_id == SoccerMain.match_id
        ).join(
            ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
        ).filter(
            ChampionshipsSoccer.country == country
        )

    if league and league != 'null':
        throws_query = throws_query.filter(
            SoccerMain.league_id == league
        )

    if team1 and team1 != '':
        throws_query = throws_query.filter(
            SoccerMain.team_home == team1
        )

    if team2 and team2 != '':
        throws_query = throws_query.filter(
            SoccerMain.team_away == team2
        )

    '''stats queries'''
    # Фильтрация по xG для команды 1
    if xg_t1 is not None and xg_t1_minus is not None and xg_t1_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.home_xg.between(xg_t1 - xg_t1_minus, xg_t1 + xg_t1_plus)
        )

    # Фильтрация по xG для команды 2
    if xg_t2 is not None and xg_t2_minus is not None and xg_t2_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.away_xg.between(xg_t2 - xg_t2_minus, xg_t2 + xg_t2_plus)
        )

    if shots_t1 is not None and shots_t1_minus is not None and shots_t1_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.home_attempts.between(shots_t1 - shots_t1_minus, shots_t1 + shots_t1_plus)
        )

    # Фильтрация по xG для команды 2
    if shots_t2 is not None and shots_t2_minus is not None and shots_t2_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.away_attempts.between(shots_t2 - shots_t2_minus, shots_t2 + shots_t2_plus)
        )

    if ongoal_t1 is not None and ongoal_t1_minus is not None and ongoal_t1_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.home_shots.between(ongoal_t1 - ongoal_t1_minus, ongoal_t1 + ongoal_t1_plus)
        )

    if ongoal_t2 is not None and ongoal_t2_minus is not None and ongoal_t2_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.away_shots.between(ongoal_t2 - ongoal_t2_minus, ongoal_t2 + ongoal_t2_plus)
        )

    if poss_t1 is not None and poss_t1_minus is not None and poss_t1_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.home_possession.between(poss_t1 - poss_t1_minus, poss_t1 + poss_t1_plus)
        )

    if poss_t2 is not None and poss_t2_minus is not None and poss_t2_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.away_possession.between(poss_t2 - poss_t2_minus, poss_t2 + poss_t2_plus)
        )

    if corners_t1 is not None and corners_t1_minus is not None and corners_t1_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.home_corners.between(corners_t1 - corners_t1_minus, corners_t1 + corners_t1_plus)
        )

    if corners_t2 is not None and corners_t2_minus is not None and corners_t2_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.away_corners.between(corners_t2 - corners_t2_minus, corners_t2 + corners_t2_plus)
        )

    if attacks_t1 is not None and attacks_t1_minus is not None and attacks_t1_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.home_dangerous_attacks.between(attacks_t1 - attacks_t1_minus, attacks_t1 + attacks_t1_plus)
        )

    if attacks_t2 is not None and attacks_t2_minus is not None and attacks_t2_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.away_dangerous_attacks.between(attacks_t2 - attacks_t2_minus, attacks_t2 + attacks_t2_plus)
        )

    if fkicks_t1 is not None and fkicks_t1_minus is not None and fkicks_t1_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.home_freekicks.between(fkicks_t1 - fkicks_t1_minus, fkicks_t1 + fkicks_t1_plus)
        )

    if fkicks_t2 is not None and fkicks_t2_minus is not None and fkicks_t2_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.away_freekicks.between(fkicks_t2 - fkicks_t2_minus, fkicks_t2 + fkicks_t2_plus)
        )

    if throwins_t1 is not None and throwins_t1_minus is not None and throwins_t1_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.home_throw_ins.between(throwins_t1 - throwins_t1_minus, throwins_t1 + throwins_t1_plus)
        )

    if throwins_t2 is not None and throwins_t2_minus is not None and throwins_t2_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.away_throw_ins.between(throwins_t2 - throwins_t2_minus, throwins_t2 + throwins_t2_plus)
        )

    if offsides_t1 is not None and offsides_t1_minus is not None and offsides_t1_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.home_offsides.between(offsides_t1 - offsides_t1_minus, offsides_t1 + offsides_t1_plus)
        )

    if offsides_t2 is not None and offsides_t2_minus is not None and offsides_t2_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.away_offsides.between(offsides_t2 - offsides_t2_minus, offsides_t2 + offsides_t2_plus)
        )

    if fouls_t1 is not None and fouls_t1_minus is not None and fouls_t1_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.home_fouls.between(fouls_t1 - fouls_t1_minus, fouls_t1 + fouls_t1_plus)
        )

    if fouls_t2 is not None and fouls_t2_minus is not None and fouls_t2_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.away_fouls.between(fouls_t2 - fouls_t2_minus, fouls_t2 + fouls_t2_plus)
        )

    if yellows_t1 is not None and yellows_t1_minus is not None and yellows_t1_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.home_yellow.between(yellows_t1 - yellows_t1_minus, yellows_t1 + yellows_t1_plus)
        )

    if yellows_t2 is not None and yellows_t2_minus is not None and yellows_t2_plus is not None:
        throws_query = throws_query.filter(
            SoccerHalf1Stats.away_yellow.between(yellows_t2 - yellows_t2_minus, yellows_t2 + yellows_t2_plus)
        )

    if win_close is not None and win_close_minus is not None and win_close_plus is not None:
        throws_query = throws_query.filter(
            selected_model.win_home_close.between(win_close - win_close_minus, win_close + win_close_plus)
        )
    if draw_close is not None and draw_close_minus is not None and draw_close_plus is not None:
        throws_query = throws_query.filter(
            selected_model.draw_close.between(draw_close - abs(draw_close_minus), draw_close + abs(draw_close_plus))
        )
    if lose_close is not None and lose_close_minus is not None and lose_close_plus is not None:
        throws_query = throws_query.filter(
            selected_model.win_away_close.between(lose_close - lose_close_minus, lose_close + lose_close_plus)
        )

    if total15_close is not None and total15_close_minus is not None and total15_close_plus is not None:
        throws_query = throws_query.filter(
            selected_model.odds_1_5_close.between(total15_close - total15_close_minus,
                                                  total15_close + total15_close_plus)
        )

    if total25_close is not None and total25_close_minus is not None and total25_close_plus is not None:
        throws_query = throws_query.filter(
            selected_model.odds_2_5_close.between(total25_close - total25_close_minus,
                                                  total25_close + total25_close_plus)
        )

    # Фильтрация по коэффициентам открытия для победы, ничьи и поражения
    if win_open is not None and win_open_minus is not None and win_open_plus is not None:
        throws_query = throws_query.filter(
            selected_model.win_home_open.between(win_open - win_open_minus, win_open + win_open_plus)
        )
    if draw_open is not None and draw_open_minus is not None and draw_open_plus is not None:
        throws_query = throws_query.filter(
            selected_model.draw_open.between(draw_open - abs(draw_open_minus), draw_open + abs(draw_open_plus))
        )
    if lose_open is not None and lose_open_minus is not None and lose_open_plus is not None:
        throws_query = throws_query.filter(
            selected_model.win_away_open.between(lose_open - lose_open_minus, lose_open + lose_open_plus)
        )

    if total15_open is not None and total15_open_minus is not None and total15_open_plus is not None:
        throws_query = throws_query.filter(
            selected_model.odds_1_5_open.between(total15_open - total15_open_minus,
                                                 total15_open + total15_open_plus)
        )

    if total25_open is not None and total25_open_minus is not None and total25_open_plus is not None:
        throws_query = throws_query.filter(
            selected_model.odds_2_5_open.between(total25_open - total25_open_minus,
                                                 total25_open + total25_open_plus)
        )

    throws_entries = throws_query.group_by(
        'total_throws_h2'
    ).order_by(
        'total_throws_h2'
    ).all()

    total_throws_entries = sum(entry.count for entry in throws_entries)

    if total_throws_entries == 0:
        return total_throws_entries, [], [], []

    throws_percentages = [
        (entry.total_throws_h2, entry.count, (entry.count / total_throws_entries) * 100)
        for entry in throws_entries

    ]



    # Подсчет процентов, которые больше текущего количества угловых
    cumulative_percentage = 0
    result_table = []

    for i, (total_throws, count, percentage) in enumerate(throws_percentages):
        if i < len(throws_percentages) - 1:
            greater_percentage = 100 - cumulative_percentage - percentage
        else:
            greater_percentage = None

        result_table.append((total_throws, count, percentage, greater_percentage))
        cumulative_percentage += percentage


    return total_throws_entries, result_table