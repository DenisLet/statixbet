from app.models import User, ChampionshipsSoccer, SoccerMain, XbetOdds, Bet365Odds, UnibetOdds, SoccerTimeline
from app.models import SoccerHalf1Stats, SoccerHalf2Stats
from sqlalchemy import func, case
from app import app, db
from sqlalchemy import or_

def get_ind_goals_team(country=None, league=None, team=None, opponent=None, sportbook=None, date_from=None, date_to=None,
                  team1_win=None, team1_win_minus=None, team1_win_plus=None, team1_win_close=None,
                  team1_win_close_minus=None, team1_win_close_plus=None, team1_draw=None,
                  team1_draw_minus=None, team1_draw_plus=None, team1_draw_close=None,
                  team1_draw_close_minus=None, team1_draw_close_plus=None, team1_loss=None,
                  team1_loss_minus=None, team1_loss_plus=None, team1_loss_close=None,
                  team1_loss_close_minus=None, team1_loss_close_plus=None, team1_over_1_5=None,
                  team1_over_1_5_minus=None, team1_over_1_5_plus=None, team1_over_1_5_close=None,
                  team1_over_1_5_close_minus=None, team1_over_1_5_close_plus=None, team1_over_2_5=None,
                  team1_over_2_5_minus=None, team1_over_2_5_plus=None, team1_over_2_5_close=None,
                  team1_over_2_5_close_minus=None, team1_over_2_5_close_plus=None, selected_model=None):
    home_query = db.session.query(
        ChampionshipsSoccer.country,
        ChampionshipsSoccer.league,
        SoccerMain.team_home,
        func.count(SoccerMain.match_id).label('total_home_matches'),
        # Голов забила домашняя команда
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 0, 1), else_=0)).label(
            'home_goals_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 1, 1), else_=0)).label(
            'home_goals_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 2, 1), else_=0)).label(
            'home_goals_gt2'),
        # Голов пропустила домашняя команда
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 0, 1), else_=0)).label(
            'home_goals_conceded_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 1, 1), else_=0)).label(
            'home_goals_conceded_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 2, 1), else_=0)).label(
            'home_goals_conceded_gt2'),
        # Голов забила домашняя команда в первом тайме
        func.sum(case((SoccerTimeline.score_t1_h1 > 0, 1), else_=0)).label('home_goals_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 1, 1), else_=0)).label('home_goals_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 2, 1), else_=0)).label('home_goals_first_half_gt2'),
        # Голов пропустила домашняя команда в первом тайме
        func.sum(case((SoccerTimeline.score_t2_h1 > 0, 1), else_=0)).label('home_goals_conceded_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 1, 1), else_=0)).label('home_goals_conceded_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 2, 1), else_=0)).label('home_goals_conceded_first_half_gt2'),

        # Подсчеты для побед и поражений в матче
        func.sum(case((
                      SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 3,
                      1), else_=0)).label('home_wins_gt3'),
        func.sum(case((
                      SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 2,
                      1), else_=0)).label('home_wins_gt2'),
        func.sum(case((
                      SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 1,
                      1), else_=0)).label('home_wins_gt1'),
        func.sum(case((
                      SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 3,
                      1), else_=0)).label('home_losses_gt3'),
        func.sum(case((
                      SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 2,
                      1), else_=0)).label('home_losses_gt2'),
        func.sum(case((
                      SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 1,
                      1), else_=0)).label('home_losses_gt1'),
        func.sum(case((
                      SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 == SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2,
                      1), else_=0)).label('home_draws'),

        # Подсчеты для побед и поражений в первом тайме
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 3, 1), else_=0)).label(
            'home_wins_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 2, 1), else_=0)).label(
            'home_wins_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 1, 1), else_=0)).label(
            'home_wins_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 3, 1), else_=0)).label(
            'home_losses_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 2, 1), else_=0)).label(
            'home_losses_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 1, 1), else_=0)).label(
            'home_losses_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 == SoccerTimeline.score_t2_h1, 1), else_=0)).label(
            'home_draws_first_half')
    ).join(
        SoccerMain, SoccerTimeline.match_id == SoccerMain.match_id
    ).join(
        ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
    ).join(
        selected_model, SoccerTimeline.match_id == selected_model.match_id
    ).filter(
    SoccerMain.final != 'Awarded'  # Добавляем фильтр на поле final
        )

    # Запрос для выездных игр
    away_query = db.session.query(
        ChampionshipsSoccer.country,
        ChampionshipsSoccer.league,
        SoccerMain.team_away,
        func.count(SoccerMain.match_id).label('total_away_matches'),
        # Голов забила выездная команда
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 0, 1), else_=0)).label(
            'away_goals_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 1, 1), else_=0)).label(
            'away_goals_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 2, 1), else_=0)).label(
            'away_goals_gt2'),
        # Голов пропустила выездная команда
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 0, 1), else_=0)).label(
            'away_goals_conceded_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 1, 1), else_=0)).label(
            'away_goals_conceded_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 2, 1), else_=0)).label(
            'away_goals_conceded_gt2'),
        # Голов забила выездная команда в первом тайме
        func.sum(case((SoccerTimeline.score_t2_h1 > 0, 1), else_=0)).label('away_goals_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 1, 1), else_=0)).label('away_goals_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 2, 1), else_=0)).label('away_goals_first_half_gt2'),
        # Голов пропустила выездная команда в первом тайме
        func.sum(case((SoccerTimeline.score_t1_h1 > 0, 1), else_=0)).label('away_goals_conceded_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 1, 1), else_=0)).label('away_goals_conceded_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 2, 1), else_=0)).label('away_goals_conceded_first_half_gt2'),

        # Подсчеты для побед и поражений по итогам всего матча
        func.sum(case((
                      SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 3,
                      1), else_=0)).label('away_wins_gt3'),
        func.sum(case((
                      SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 2,
                      1), else_=0)).label('away_wins_gt2'),
        func.sum(case((
                      SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 1,
                      1), else_=0)).label('away_wins_gt1'),
        func.sum(case((
                      SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 3,
                      1), else_=0)).label('away_losses_gt3'),
        func.sum(case((
                      SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 2,
                      1), else_=0)).label('away_losses_gt2'),
        func.sum(case((
                      SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 1,
                      1), else_=0)).label('away_losses_gt1'),
        func.sum(case((
                      SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 == SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2,
                      1), else_=0)).label('away_draws'),

        # Подсчеты для побед и поражений по итогам первого тайма
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 3, 1), else_=0)).label(
            'away_wins_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 2, 1), else_=0)).label(
            'away_wins_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 1, 1), else_=0)).label(
            'away_wins_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 3, 1), else_=0)).label(
            'away_losses_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 2, 1), else_=0)).label(
            'away_losses_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 1, 1), else_=0)).label(
            'away_losses_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 == SoccerTimeline.score_t2_h1, 1), else_=0)).label(
            'away_draws_first_half'),
    ).join(
        SoccerMain, SoccerTimeline.match_id == SoccerMain.match_id
    ).join(
        ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
    ).join(
        selected_model, SoccerTimeline.match_id == selected_model.match_id
    ).filter(
    SoccerMain.final != 'Awarded'  # Добавляем фильтр на поле final
        )

    # Фильтрация по стране, лиге и датам (для обоих запросов)
    if country:
        home_query = home_query.filter(ChampionshipsSoccer.country == country)
        away_query = away_query.filter(ChampionshipsSoccer.country == country)
    if league:
        home_query = home_query.filter(ChampionshipsSoccer.league == league)
        away_query = away_query.filter(ChampionshipsSoccer.league == league)
    if team:
        home_query = home_query.filter(SoccerMain.team_home == team)
        away_query = away_query.filter(SoccerMain.team_away == team)
    if date_from:
        home_query = home_query.filter(SoccerMain.match_date >= date_from)
        away_query = away_query.filter(SoccerMain.match_date >= date_from)
    if date_to:
        home_query = home_query.filter(SoccerMain.match_date <= date_to)
        away_query = away_query.filter(SoccerMain.match_date <= date_to)


    if team1_win !=0:
        home_query = home_query.filter(
            selected_model.win_home_open.between(team1_win - team1_win_minus,
                                                  team1_win + team1_win_plus)
        )
        away_query = away_query.filter(
            selected_model.win_away_open.between(team1_win - team1_win_minus,
                                                  team1_win + team1_win_plus)
        )

    # Фильтрация по team1_win_close
    if team1_win_close !=0:
        home_query = home_query.filter(
            selected_model.win_home_close.between(team1_win_close - team1_win_close_minus,
                                                  team1_win_close + team1_win_close_plus)
        )
        away_query = away_query.filter(
            selected_model.win_away_close.between(team1_win_close - team1_win_close_minus,
                                                  team1_win_close + team1_win_close_plus)
        )

    if team1_draw !=0:
        home_query = home_query.filter(
            selected_model.draw_open.between(team1_draw - team1_draw_minus,
                                                  team1_draw + team1_draw_plus)
        )
        away_query = away_query.filter(
            selected_model.draw_open.between(team1_draw - team1_draw_minus,
                                                  team1_draw + team1_draw_plus)
        )

    if team1_draw_close !=0:
        home_query = home_query.filter(
            selected_model.draw_close.between(team1_draw_close - team1_draw_close_minus,
                                                  team1_draw_close + team1_draw_close_plus)
        )
        away_query = away_query.filter(
            selected_model.draw_close.between(team1_draw_close - team1_draw_close_minus,
                                                  team1_draw_close + team1_draw_close_plus)
        )


    if team1_loss !=0:
        home_query = home_query.filter(
            selected_model.win_away_open.between(team1_loss - team1_loss_minus,
                                                  team1_loss + team1_loss_plus)
        )
        away_query = away_query.filter(
            selected_model.win_home_open.between(team1_loss - team1_loss_minus,
                                                  team1_loss + team1_loss_plus)
        )

    if team1_loss_close !=0:
        home_query = home_query.filter(
            selected_model.win_away_open.between(team1_loss_close - team1_loss_close_minus,
                                                  team1_loss_close + team1_loss_close_plus)
        )
        away_query = away_query.filter(
            selected_model.win_home_open.between(team1_loss_close - team1_loss_close_minus,
                                                  team1_loss_close + team1_loss_close_plus)
        )

    if team1_over_1_5 !=0:
        home_query = home_query.filter(
            selected_model.odds_1_5_open.between(team1_over_1_5 - team1_over_1_5_minus,
                                                  team1_over_1_5 + team1_over_1_5_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_1_5_open.between(team1_over_1_5 - team1_over_1_5_minus,
                                                  team1_over_1_5 + team1_over_1_5_plus)
        )

    if team1_over_1_5_close !=0:
        home_query = home_query.filter(
            selected_model.odds_1_5_close.between(team1_over_1_5_close - team1_over_1_5_close_minus,
                                                  team1_over_1_5_close + team1_over_1_5_close_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_1_5_close.between(team1_over_1_5_close - team1_over_1_5_close_minus,
                                                  team1_over_1_5_close + team1_over_1_5_close_plus)
        )

    if team1_over_2_5 != 0:
        home_query = home_query.filter(
            selected_model.odds_2_5_open.between(team1_over_2_5 - team1_over_2_5_minus,
                                                 team1_over_2_5 + team1_over_2_5_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_2_5_open.between(team1_over_2_5 - team1_over_2_5_minus,
                                                 team1_over_2_5 + team1_over_2_5_plus)
        )

    if team1_over_2_5_close != 0:
        home_query = home_query.filter(
            selected_model.odds_2_5_close.between(team1_over_2_5_close - team1_over_2_5_close_minus,
                                                  team1_over_2_5_close + team1_over_2_5_close_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_2_5_close.between(team1_over_2_5_close - team1_over_2_5_close_minus,
                                                  team1_over_2_5_close + team1_over_2_5_close_plus)
        )



    # Группировка по команде, стране и лиге
    home_query = home_query.group_by(SoccerMain.team_home, ChampionshipsSoccer.country, ChampionshipsSoccer.league)
    away_query = away_query.group_by(SoccerMain.team_away, ChampionshipsSoccer.country, ChampionshipsSoccer.league)

    # Выполняем запросы
    home_results = home_query.all()
    away_results = away_query.all()

    # Преобразование результатов в словарь
    result_list = []
    total_home_goals_gt0 = 0
    total_home_goals_gt1 = 0
    total_home_goals_gt2 = 0
    total_home_goals_conceded_gt0 = 0
    total_home_goals_conceded_gt1 = 0
    total_home_goals_conceded_gt2 = 0
    total_home_goals_first_half_gt0 = 0
    total_home_goals_first_half_gt1 = 0
    total_home_goals_first_half_gt2 = 0
    total_home_goals_conceded_first_half_gt0 = 0
    total_home_goals_conceded_first_half_gt1 = 0
    total_home_goals_conceded_first_half_gt2 = 0
    total_home_wins_gt1 = 0
    total_home_wins_gt2 = 0
    total_home_wins_gt3 = 0
    total_home_losses_gt1 = 0
    total_home_losses_gt2 = 0
    total_home_losses_gt3 = 0
    total_home_draws = 0
    total_home_matches = 0
    total_home_wins_gt1_h1 = 0
    total_home_wins_gt2_h1 = 0
    total_home_wins_gt3_h1 = 0
    total_home_losses_gt1_h1 = 0
    total_home_losses_gt2_h1 = 0
    total_home_losses_gt3_h1 = 0
    total_home_draws_h1 = 0

    # Суммирование значений из всех кортежей
    for res in home_results:
        total_home_goals_gt0 += res.home_goals_gt0
        total_home_goals_gt1 += res.home_goals_gt1
        total_home_goals_gt2 += res.home_goals_gt2
        total_home_goals_conceded_gt0 += res.home_goals_conceded_gt0
        total_home_goals_conceded_gt1 += res.home_goals_conceded_gt1
        total_home_goals_conceded_gt2 += res.home_goals_conceded_gt2
        total_home_goals_first_half_gt0 += res.home_goals_first_half_gt0
        total_home_goals_first_half_gt1 += res.home_goals_first_half_gt1
        total_home_goals_first_half_gt2 += res.home_goals_first_half_gt2
        total_home_goals_conceded_first_half_gt0 += res.home_goals_conceded_first_half_gt0
        total_home_goals_conceded_first_half_gt1 += res.home_goals_conceded_first_half_gt1
        total_home_goals_conceded_first_half_gt2 += res.home_goals_conceded_first_half_gt2
        total_home_wins_gt1 += res.home_wins_gt1
        total_home_wins_gt2 += res.home_wins_gt2
        total_home_wins_gt3 += res.home_wins_gt3
        total_home_losses_gt1 += res.home_losses_gt1
        total_home_losses_gt2 += res.home_losses_gt2
        total_home_losses_gt3 += res.home_losses_gt3
        total_home_draws += res.home_draws

        total_home_wins_gt1_h1 += res.home_wins_first_half_gt1
        total_home_wins_gt2_h1 += res.home_wins_first_half_gt2
        total_home_wins_gt3_h1 += res.home_wins_first_half_gt3
        total_home_losses_gt1_h1 += res.home_losses_first_half_gt1
        total_home_losses_gt2_h1 += res.home_losses_first_half_gt2
        total_home_losses_gt3_h1 += res.home_losses_first_half_gt3
        total_home_draws_h1 += res.home_draws_first_half
        total_home_matches += res.total_home_matches

    # Создание итогового словаря
    home_result_dict = {
        'home': {
            'scored': {
                'gt0': total_home_goals_gt0,
                'gt1': total_home_goals_gt1,
                'gt2': total_home_goals_gt2
            },
            'conceded': {
                'gt0': total_home_goals_conceded_gt0,
                'gt1': total_home_goals_conceded_gt1,
                'gt2': total_home_goals_conceded_gt2
            },
            'first_half': {
                'scored': {
                    'gt0': total_home_goals_first_half_gt0,
                    'gt1': total_home_goals_first_half_gt1,
                    'gt2': total_home_goals_first_half_gt2
                },
                'conceded': {
                    'gt0': total_home_goals_conceded_first_half_gt0,
                    'gt1': total_home_goals_conceded_first_half_gt1,
                    'gt2': total_home_goals_conceded_first_half_gt2
                },
                'wins': {
                    'wins': total_home_wins_gt1_h1,
                    'gt1': total_home_wins_gt2_h1,
                    'gt2': total_home_wins_gt3_h1
            },
                'losses': {
                    'lose': total_home_losses_gt1_h1,
                    'gt1': total_home_losses_gt2_h1,
                    'gt2': total_home_losses_gt3_h1
                },
                'draws': total_home_draws_h1
            },
            'wins': {
                'wins': total_home_wins_gt1,
                'gt1': total_home_wins_gt2,
                'gt2': total_home_wins_gt3
            },
            'losses': {
                'lose': total_home_losses_gt1,
                'gt1': total_home_losses_gt2,
                'gt2': total_home_losses_gt3
            },
            'draws': total_home_draws,
            'number': total_home_matches
        }
    }

    result_list.append(home_result_dict)

    total_away_goals_gt0 = 0
    total_away_goals_gt1 = 0
    total_away_goals_gt2 = 0
    total_away_goals_conceded_gt0 = 0
    total_away_goals_conceded_gt1 = 0
    total_away_goals_conceded_gt2 = 0
    total_away_goals_first_half_gt0 = 0
    total_away_goals_first_half_gt1 = 0
    total_away_goals_first_half_gt2 = 0
    total_away_goals_conceded_first_half_gt0 = 0
    total_away_goals_conceded_first_half_gt1 = 0
    total_away_goals_conceded_first_half_gt2 = 0
    total_away_wins_gt1 = 0
    total_away_wins_gt2 = 0
    total_away_wins_gt3 = 0
    total_away_losses_gt1 = 0
    total_away_losses_gt2 = 0
    total_away_losses_gt3 = 0
    total_away_draws = 0
    total_away_matches = 0
    total_away_wins_gt1_h1 = 0
    total_away_wins_gt2_h1 = 0
    total_away_wins_gt3_h1 = 0
    total_away_losses_gt1_h1 = 0
    total_away_losses_gt2_h1 = 0
    total_away_losses_gt3_h1 = 0
    total_away_draws_h1 = 0

    # Суммирование значений из всех кортежей
    for res in away_results:
        total_away_goals_gt0 += res.away_goals_gt0
        total_away_goals_gt1 += res.away_goals_gt1
        total_away_goals_gt2 += res.away_goals_gt2
        total_away_goals_conceded_gt0 += res.away_goals_conceded_gt0
        total_away_goals_conceded_gt1 += res.away_goals_conceded_gt1
        total_away_goals_conceded_gt2 += res.away_goals_conceded_gt2
        total_away_goals_first_half_gt0 += res.away_goals_first_half_gt0
        total_away_goals_first_half_gt1 += res.away_goals_first_half_gt1
        total_away_goals_first_half_gt2 += res.away_goals_first_half_gt2
        total_away_goals_conceded_first_half_gt0 += res.away_goals_conceded_first_half_gt0
        total_away_goals_conceded_first_half_gt1 += res.away_goals_conceded_first_half_gt1
        total_away_goals_conceded_first_half_gt2 += res.away_goals_conceded_first_half_gt2
        total_away_wins_gt1 += res.away_wins_gt1
        total_away_wins_gt2 += res.away_wins_gt2
        total_away_wins_gt3 += res.away_wins_gt3
        total_away_losses_gt1 += res.away_losses_gt1
        total_away_losses_gt2 += res.away_losses_gt2
        total_away_losses_gt3 += res.away_losses_gt3
        total_away_draws += res.away_draws

        total_away_wins_gt1_h1 += res.away_wins_first_half_gt1
        total_away_wins_gt2_h1 += res.away_wins_first_half_gt2
        total_away_wins_gt3_h1 += res.away_wins_first_half_gt3
        total_away_losses_gt1_h1 += res.away_losses_first_half_gt1
        total_away_losses_gt2_h1 += res.away_losses_first_half_gt2
        total_away_losses_gt3_h1 += res.away_losses_first_half_gt3
        total_away_draws_h1 += res.away_draws_first_half
        total_away_matches += res.total_away_matches

    # Создание итогового словаря
    away_result_dict = {
        'away': {
            'scored': {
                'gt0': total_away_goals_gt0,
                'gt1': total_away_goals_gt1,
                'gt2': total_away_goals_gt2
            },
            'conceded': {
                'gt0': total_away_goals_conceded_gt0,
                'gt1': total_away_goals_conceded_gt1,
                'gt2': total_away_goals_conceded_gt2
            },
            'first_half': {
                'scored': {
                    'gt0': total_away_goals_first_half_gt0,
                    'gt1': total_away_goals_first_half_gt1,
                    'gt2': total_away_goals_first_half_gt2
                },
                'conceded': {
                    'gt0': total_away_goals_conceded_first_half_gt0,
                    'gt1': total_away_goals_conceded_first_half_gt1,
                    'gt2': total_away_goals_conceded_first_half_gt2
                },
                'wins': {
                    'wins': total_away_wins_gt1_h1,
                    'gt1': total_away_wins_gt2_h1,
                    'gt2': total_away_wins_gt3_h1
                },
                'losses': {
                    'lose': total_away_losses_gt1_h1,
                    'gt1': total_away_losses_gt2_h1,
                    'gt2': total_away_losses_gt3_h1
                },
                'draws': total_away_draws_h1
            },
            'wins': {
                'wins': total_away_wins_gt1,
                'gt1': total_away_wins_gt2,
                'gt2': total_away_wins_gt3
            },
            'losses': {
                'lose': total_away_losses_gt1,
                'gt1': total_away_losses_gt2,
                'gt2': total_away_losses_gt3
            },
            'draws': total_away_draws,
            'number': total_away_matches  # Ничьи
        }
    }

    # Добавление итогового словаря в список результатов
    result_list.append(away_result_dict)

    return result_list


def get_ind_goals_opponent(country=None, league=None, team=None, opponent=None, sportbook=None, date_from=None, date_to=None,
                  team1_win=None, team1_win_minus=None, team1_win_plus=None, team1_win_close=None,
                  team1_win_close_minus=None, team1_win_close_plus=None, team1_draw=None,
                  team1_draw_minus=None, team1_draw_plus=None, team1_draw_close=None,
                  team1_draw_close_minus=None, team1_draw_close_plus=None, team1_loss=None,
                  team1_loss_minus=None, team1_loss_plus=None, team1_loss_close=None,
                  team1_loss_close_minus=None, team1_loss_close_plus=None, team1_over_1_5=None,
                  team1_over_1_5_minus=None, team1_over_1_5_plus=None, team1_over_1_5_close=None,
                  team1_over_1_5_close_minus=None, team1_over_1_5_close_plus=None, team1_over_2_5=None,
                  team1_over_2_5_minus=None, team1_over_2_5_plus=None, team1_over_2_5_close=None,
                  team1_over_2_5_close_minus=None, team1_over_2_5_close_plus=None, selected_model=None):

    home_query = db.session.query(
        ChampionshipsSoccer.country,
        ChampionshipsSoccer.league,
        SoccerMain.team_home,
        func.count(SoccerMain.match_id).label('total_home_matches'),
        # Голов забила домашняя команда
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 0, 1), else_=0)).label('home_goals_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 1, 1), else_=0)).label('home_goals_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 2, 1), else_=0)).label('home_goals_gt2'),
        # Голов пропустила домашняя команда
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 0, 1), else_=0)).label('home_goals_conceded_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 1, 1), else_=0)).label('home_goals_conceded_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 2, 1), else_=0)).label('home_goals_conceded_gt2'),
        # Голов забила домашняя команда в первом тайме
        func.sum(case((SoccerTimeline.score_t1_h1 > 0, 1), else_=0)).label('home_goals_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 1, 1), else_=0)).label('home_goals_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 2, 1), else_=0)).label('home_goals_first_half_gt2'),
        # Голов пропустила домашняя команда в первом тайме
        func.sum(case((SoccerTimeline.score_t2_h1 > 0, 1), else_=0)).label('home_goals_conceded_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 1, 1), else_=0)).label('home_goals_conceded_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 2, 1), else_=0)).label('home_goals_conceded_first_half_gt2'),

        # Подсчеты для побед и поражений
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 3, 1), else_=0)).label('home_wins_gt3'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 2, 1), else_=0)).label('home_wins_gt2'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 1, 1), else_=0)).label('home_wins_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 3, 1), else_=0)).label('home_losses_gt3'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 2, 1), else_=0)).label('home_losses_gt2'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 1, 1), else_=0)).label('home_losses_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 == SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2, 1), else_=0)).label('home_draws'),
        # Подсчеты для побед и поражений в первом тайме
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 3, 1), else_=0)).label(
            'home_wins_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 2, 1), else_=0)).label(
            'home_wins_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 1, 1), else_=0)).label(
            'home_wins_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 3, 1), else_=0)).label(
            'home_losses_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 2, 1), else_=0)).label(
            'home_losses_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 1, 1), else_=0)).label(
            'home_losses_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 == SoccerTimeline.score_t2_h1, 1), else_=0)).label(
            'home_draws_first_half'),
    ).join(
        SoccerMain, SoccerTimeline.match_id == SoccerMain.match_id
    ).join(
        ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
    ).join(
        selected_model, SoccerTimeline.match_id == selected_model.match_id
    ).filter(
    SoccerMain.final != 'Awarded'  # Добавляем фильтр на поле final
        )

    # Запрос для выездных игр
    away_query = db.session.query(
        ChampionshipsSoccer.country,
        ChampionshipsSoccer.league,
        SoccerMain.team_away,
        func.count(SoccerMain.match_id).label('total_away_matches'),
        # Голов забила выездная команда
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 0, 1), else_=0)).label('away_goals_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 1, 1), else_=0)).label('away_goals_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 2, 1), else_=0)).label('away_goals_gt2'),
        # Голов пропустила выездная команда
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 0, 1), else_=0)).label('away_goals_conceded_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 1, 1), else_=0)).label('away_goals_conceded_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 2, 1), else_=0)).label('away_goals_conceded_gt2'),
        # Голов забила выездная команда в первом тайме
        func.sum(case((SoccerTimeline.score_t2_h1 > 0, 1), else_=0)).label('away_goals_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 1, 1), else_=0)).label('away_goals_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 2, 1), else_=0)).label('away_goals_first_half_gt2'),
        # Голов пропустила выездная команда в первом тайме
        func.sum(case((SoccerTimeline.score_t1_h1 > 0, 1), else_=0)).label('away_goals_conceded_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 1, 1), else_=0)).label('away_goals_conceded_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 2, 1), else_=0)).label('away_goals_conceded_first_half_gt2'),

        # Подсчеты для побед и поражений
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 3, 1), else_=0)).label('away_wins_gt3'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 2, 1), else_=0)).label('away_wins_gt2'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 1, 1), else_=0)).label('away_wins_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 3, 1), else_=0)).label('away_losses_gt3'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 2, 1), else_=0)).label('away_losses_gt2'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 1, 1), else_=0)).label('away_losses_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 == SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2, 1), else_=0)).label('away_draws'),
        # Подсчеты для побед и поражений по итогам первого тайма
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 3, 1), else_=0)).label(
            'away_wins_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 2, 1), else_=0)).label(
            'away_wins_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 1, 1), else_=0)).label(
            'away_wins_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 3, 1), else_=0)).label(
            'away_losses_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 2, 1), else_=0)).label(
            'away_losses_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 1, 1), else_=0)).label(
            'away_losses_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 == SoccerTimeline.score_t2_h1, 1), else_=0)).label(
            'away_draws_first_half'),
    ).join(
        SoccerMain, SoccerTimeline.match_id == SoccerMain.match_id
    ).join(
        ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
    ).join(
        selected_model, SoccerTimeline.match_id == selected_model.match_id
    ).filter(
    SoccerMain.final != 'Awarded'  # Добавляем фильтр на поле final
        )


    # Фильтрация по стране, лиге и датам (для обоих запросов)
    if country:
        home_query = home_query.filter(ChampionshipsSoccer.country == country)
        away_query = away_query.filter(ChampionshipsSoccer.country == country)
    if league:
        home_query = home_query.filter(ChampionshipsSoccer.league == league)
        away_query = away_query.filter(ChampionshipsSoccer.league == league)
    if team:
        home_query = home_query.filter(SoccerMain.team_home == opponent)
        away_query = away_query.filter(SoccerMain.team_away == opponent)
    if date_from:
        home_query = home_query.filter(SoccerMain.match_date >= date_from)
        away_query = away_query.filter(SoccerMain.match_date >= date_from)
    if date_to:
        home_query = home_query.filter(SoccerMain.match_date <= date_to)
        away_query = away_query.filter(SoccerMain.match_date <= date_to)


    if team1_win !=0:
        home_query = home_query.filter(
            selected_model.win_home_open.between(team1_win - team1_win_minus,
                                                  team1_win + team1_win_plus)
        )
        away_query = away_query.filter(
            selected_model.win_away_open.between(team1_win - team1_win_minus,
                                                  team1_win + team1_win_plus)
        )

    # Фильтрация по team1_win_close
    if team1_win_close !=0:
        home_query = home_query.filter(
            selected_model.win_home_close.between(team1_win_close - team1_win_close_minus,
                                                  team1_win_close + team1_win_close_plus)
        )
        away_query = away_query.filter(
            selected_model.win_away_close.between(team1_win_close - team1_win_close_minus,
                                                  team1_win_close + team1_win_close_plus)
        )

    if team1_draw !=0:
        home_query = home_query.filter(
            selected_model.draw_open.between(team1_draw - team1_draw_minus,
                                                  team1_draw + team1_draw_plus)
        )
        away_query = away_query.filter(
            selected_model.draw_open.between(team1_draw - team1_draw_minus,
                                                  team1_draw + team1_draw_plus)
        )

    if team1_draw_close !=0:
        home_query = home_query.filter(
            selected_model.draw_close.between(team1_draw_close - team1_draw_close_minus,
                                                  team1_draw_close + team1_draw_close_plus)
        )
        away_query = away_query.filter(
            selected_model.draw_close.between(team1_draw_close - team1_draw_close_minus,
                                                  team1_draw_close + team1_draw_close_plus)
        )


    if team1_loss !=0:
        home_query = home_query.filter(
            selected_model.win_away_open.between(team1_loss - team1_loss_minus,
                                                  team1_loss + team1_loss_plus)
        )
        away_query = away_query.filter(
            selected_model.win_home_open.between(team1_loss - team1_loss_minus,
                                                  team1_loss + team1_loss_plus)
        )

    if team1_loss_close !=0:
        home_query = home_query.filter(
            selected_model.win_away_open.between(team1_loss_close - team1_loss_close_minus,
                                                  team1_loss_close + team1_loss_close_plus)
        )
        away_query = away_query.filter(
            selected_model.win_home_open.between(team1_loss_close - team1_loss_close_minus,
                                                  team1_loss_close + team1_loss_close_plus)
        )

    if team1_over_1_5 !=0:
        home_query = home_query.filter(
            selected_model.odds_1_5_open.between(team1_over_1_5 - team1_over_1_5_minus,
                                                  team1_over_1_5 + team1_over_1_5_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_1_5_open.between(team1_over_1_5 - team1_over_1_5_minus,
                                                  team1_over_1_5 + team1_over_1_5_plus)
        )

    if team1_over_1_5_close !=0:
        home_query = home_query.filter(
            selected_model.odds_1_5_close.between(team1_over_1_5_close - team1_over_1_5_close_minus,
                                                  team1_over_1_5_close + team1_over_1_5_close_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_1_5_close.between(team1_over_1_5_close - team1_over_1_5_close_minus,
                                                  team1_over_1_5_close + team1_over_1_5_close_plus)
        )

    if team1_over_2_5 != 0:
        home_query = home_query.filter(
            selected_model.odds_2_5_open.between(team1_over_2_5 - team1_over_2_5_minus,
                                                 team1_over_2_5 + team1_over_2_5_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_2_5_open.between(team1_over_2_5 - team1_over_2_5_minus,
                                                 team1_over_2_5 + team1_over_2_5_plus)
        )

    if team1_over_2_5_close != 0:
        home_query = home_query.filter(
            selected_model.odds_2_5_close.between(team1_over_2_5_close - team1_over_2_5_close_minus,
                                                  team1_over_2_5_close + team1_over_2_5_close_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_2_5_close.between(team1_over_2_5_close - team1_over_2_5_close_minus,
                                                  team1_over_2_5_close + team1_over_2_5_close_plus)
        )

    # Группировка по команде, стране и лиге
    home_query = home_query.group_by(SoccerMain.team_home, ChampionshipsSoccer.country, ChampionshipsSoccer.league)
    away_query = away_query.group_by(SoccerMain.team_away, ChampionshipsSoccer.country, ChampionshipsSoccer.league)

    # Выполняем запросы
    home_results = home_query.all()
    away_results = away_query.all()

    # Преобразование результатов в словарь
    result_list = []
    total_home_goals_gt0 = 0
    total_home_goals_gt1 = 0
    total_home_goals_gt2 = 0
    total_home_goals_conceded_gt0 = 0
    total_home_goals_conceded_gt1 = 0
    total_home_goals_conceded_gt2 = 0
    total_home_goals_first_half_gt0 = 0
    total_home_goals_first_half_gt1 = 0
    total_home_goals_first_half_gt2 = 0
    total_home_goals_conceded_first_half_gt0 = 0
    total_home_goals_conceded_first_half_gt1 = 0
    total_home_goals_conceded_first_half_gt2 = 0
    total_home_wins_gt1 = 0
    total_home_wins_gt2 = 0
    total_home_wins_gt3 = 0
    total_home_losses_gt1 = 0
    total_home_losses_gt2 = 0
    total_home_losses_gt3 = 0
    total_home_draws = 0
    total_home_matches = 0
    total_home_wins_gt1_h1 = 0
    total_home_wins_gt2_h1 = 0
    total_home_wins_gt3_h1 = 0
    total_home_losses_gt1_h1 = 0
    total_home_losses_gt2_h1 = 0
    total_home_losses_gt3_h1 = 0
    total_home_draws_h1 = 0

    # Суммирование значений из всех кортежей
    for res in home_results:
        total_home_goals_gt0 += res.home_goals_gt0
        total_home_goals_gt1 += res.home_goals_gt1
        total_home_goals_gt2 += res.home_goals_gt2
        total_home_goals_conceded_gt0 += res.home_goals_conceded_gt0
        total_home_goals_conceded_gt1 += res.home_goals_conceded_gt1
        total_home_goals_conceded_gt2 += res.home_goals_conceded_gt2
        total_home_goals_first_half_gt0 += res.home_goals_first_half_gt0
        total_home_goals_first_half_gt1 += res.home_goals_first_half_gt1
        total_home_goals_first_half_gt2 += res.home_goals_first_half_gt2
        total_home_goals_conceded_first_half_gt0 += res.home_goals_conceded_first_half_gt0
        total_home_goals_conceded_first_half_gt1 += res.home_goals_conceded_first_half_gt1
        total_home_goals_conceded_first_half_gt2 += res.home_goals_conceded_first_half_gt2
        total_home_wins_gt1 += res.home_wins_gt1
        total_home_wins_gt2 += res.home_wins_gt2
        total_home_wins_gt3 += res.home_wins_gt3
        total_home_losses_gt1 += res.home_losses_gt1
        total_home_losses_gt2 += res.home_losses_gt2
        total_home_losses_gt3 += res.home_losses_gt3
        total_home_draws += res.home_draws

        total_home_wins_gt1_h1 += res.home_wins_first_half_gt1
        total_home_wins_gt2_h1 += res.home_wins_first_half_gt2
        total_home_wins_gt3_h1 += res.home_wins_first_half_gt3
        total_home_losses_gt1_h1 += res.home_losses_first_half_gt1
        total_home_losses_gt2_h1 += res.home_losses_first_half_gt2
        total_home_losses_gt3_h1 += res.home_losses_first_half_gt3
        total_home_draws_h1 += res.home_draws_first_half
        total_home_matches += res.total_home_matches

    # Создание итогового словаря
    home_result_dict = {
        'home': {
            'scored': {
                'gt0': total_home_goals_gt0,
                'gt1': total_home_goals_gt1,
                'gt2': total_home_goals_gt2
            },
            'conceded': {
                'gt0': total_home_goals_conceded_gt0,
                'gt1': total_home_goals_conceded_gt1,
                'gt2': total_home_goals_conceded_gt2
            },
            'first_half': {
                'scored': {
                    'gt0': total_home_goals_first_half_gt0,
                    'gt1': total_home_goals_first_half_gt1,
                    'gt2': total_home_goals_first_half_gt2
                },
                'conceded': {
                    'gt0': total_home_goals_conceded_first_half_gt0,
                    'gt1': total_home_goals_conceded_first_half_gt1,
                    'gt2': total_home_goals_conceded_first_half_gt2
                },
                'wins': {
                    'wins': total_home_wins_gt1_h1,
                    'gt1': total_home_wins_gt2_h1,
                    'gt2': total_home_wins_gt3_h1
            },
                'losses': {
                    'lose': total_home_losses_gt1_h1,
                    'gt1': total_home_losses_gt2_h1,
                    'gt2': total_home_losses_gt3_h1
                },
                'draws': total_home_draws_h1
            },
            'wins': {
                'wins': total_home_wins_gt1,
                'gt1': total_home_wins_gt2,
                'gt2': total_home_wins_gt3
            },
            'losses': {
                'lose': total_home_losses_gt1,
                'gt1': total_home_losses_gt2,
                'gt2': total_home_losses_gt3
            },
            'draws': total_home_draws,
            'number': total_home_matches
        }
    }

    result_list.append(home_result_dict)

    total_away_goals_gt0 = 0
    total_away_goals_gt1 = 0
    total_away_goals_gt2 = 0
    total_away_goals_conceded_gt0 = 0
    total_away_goals_conceded_gt1 = 0
    total_away_goals_conceded_gt2 = 0
    total_away_goals_first_half_gt0 = 0
    total_away_goals_first_half_gt1 = 0
    total_away_goals_first_half_gt2 = 0
    total_away_goals_conceded_first_half_gt0 = 0
    total_away_goals_conceded_first_half_gt1 = 0
    total_away_goals_conceded_first_half_gt2 = 0
    total_away_wins_gt1 = 0
    total_away_wins_gt2 = 0
    total_away_wins_gt3 = 0
    total_away_losses_gt1 = 0
    total_away_losses_gt2 = 0
    total_away_losses_gt3 = 0
    total_away_draws = 0
    total_away_matches = 0
    total_away_wins_gt1_h1 = 0
    total_away_wins_gt2_h1 = 0
    total_away_wins_gt3_h1 = 0
    total_away_losses_gt1_h1 = 0
    total_away_losses_gt2_h1 = 0
    total_away_losses_gt3_h1 = 0
    total_away_draws_h1 = 0

    # Суммирование значений из всех кортежей
    for res in away_results:
        total_away_goals_gt0 += res.away_goals_gt0
        total_away_goals_gt1 += res.away_goals_gt1
        total_away_goals_gt2 += res.away_goals_gt2
        total_away_goals_conceded_gt0 += res.away_goals_conceded_gt0
        total_away_goals_conceded_gt1 += res.away_goals_conceded_gt1
        total_away_goals_conceded_gt2 += res.away_goals_conceded_gt2
        total_away_goals_first_half_gt0 += res.away_goals_first_half_gt0
        total_away_goals_first_half_gt1 += res.away_goals_first_half_gt1
        total_away_goals_first_half_gt2 += res.away_goals_first_half_gt2
        total_away_goals_conceded_first_half_gt0 += res.away_goals_conceded_first_half_gt0
        total_away_goals_conceded_first_half_gt1 += res.away_goals_conceded_first_half_gt1
        total_away_goals_conceded_first_half_gt2 += res.away_goals_conceded_first_half_gt2
        total_away_wins_gt1 += res.away_wins_gt1
        total_away_wins_gt2 += res.away_wins_gt2
        total_away_wins_gt3 += res.away_wins_gt3
        total_away_losses_gt1 += res.away_losses_gt1
        total_away_losses_gt2 += res.away_losses_gt2
        total_away_losses_gt3 += res.away_losses_gt3
        total_away_draws += res.away_draws

        total_away_wins_gt1_h1 += res.away_wins_first_half_gt1
        total_away_wins_gt2_h1 += res.away_wins_first_half_gt2
        total_away_wins_gt3_h1 += res.away_wins_first_half_gt3
        total_away_losses_gt1_h1 += res.away_losses_first_half_gt1
        total_away_losses_gt2_h1 += res.away_losses_first_half_gt2
        total_away_losses_gt3_h1 += res.away_losses_first_half_gt3
        total_away_draws_h1 += res.away_draws_first_half
        total_away_matches += res.total_away_matches

    # Создание итогового словаря
    away_result_dict = {
        'away': {
            'scored': {
                'gt0': total_away_goals_gt0,
                'gt1': total_away_goals_gt1,
                'gt2': total_away_goals_gt2
            },
            'conceded': {
                'gt0': total_away_goals_conceded_gt0,
                'gt1': total_away_goals_conceded_gt1,
                'gt2': total_away_goals_conceded_gt2
            },
            'first_half': {
                'scored': {
                    'gt0': total_away_goals_first_half_gt0,
                    'gt1': total_away_goals_first_half_gt1,
                    'gt2': total_away_goals_first_half_gt2
                },
                'conceded': {
                    'gt0': total_away_goals_conceded_first_half_gt0,
                    'gt1': total_away_goals_conceded_first_half_gt1,
                    'gt2': total_away_goals_conceded_first_half_gt2
                },
                'wins': {
                    'wins': total_away_wins_gt1_h1,
                    'gt1': total_away_wins_gt2_h1,
                    'gt2': total_away_wins_gt3_h1
                },
                'losses': {
                    'lose': total_away_losses_gt1_h1,
                    'gt1': total_away_losses_gt2_h1,
                    'gt2': total_away_losses_gt3_h1
                },
                'draws': total_away_draws_h1
            },
            'wins': {
                'wins': total_away_wins_gt1,
                'gt1': total_away_wins_gt2,
                'gt2': total_away_wins_gt3
            },
            'losses': {
                'lose': total_away_losses_gt1,
                'gt1': total_away_losses_gt2,
                'gt2': total_away_losses_gt3
            },
            'draws': total_away_draws,
            'number': total_away_matches  # Ничьи
        }
    }

    # Добавление итогового словаря в список результатов
    result_list.append(away_result_dict)

    return result_list

def get_ind_goals_vs(country=None, league=None, team=None, opponent=None, sportbook=None, date_from=None, date_to=None,
                  team1_win=None, team1_win_minus=None, team1_win_plus=None, team1_win_close=None,
                  team1_win_close_minus=None, team1_win_close_plus=None, team1_draw=None,
                  team1_draw_minus=None, team1_draw_plus=None, team1_draw_close=None,
                  team1_draw_close_minus=None, team1_draw_close_plus=None, team1_loss=None,
                  team1_loss_minus=None, team1_loss_plus=None, team1_loss_close=None,
                  team1_loss_close_minus=None, team1_loss_close_plus=None, team1_over_1_5=None,
                  team1_over_1_5_minus=None, team1_over_1_5_plus=None, team1_over_1_5_close=None,
                  team1_over_1_5_close_minus=None, team1_over_1_5_close_plus=None, team1_over_2_5=None,
                  team1_over_2_5_minus=None, team1_over_2_5_plus=None, team1_over_2_5_close=None,
                  team1_over_2_5_close_minus=None, team1_over_2_5_close_plus=None, selected_model=None):

    home_query = db.session.query(
        ChampionshipsSoccer.country,
        ChampionshipsSoccer.league,
        SoccerMain.team_home,
        func.count(SoccerMain.match_id).label('total_home_matches'),
        # Голов забила домашняя команда
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 0, 1), else_=0)).label('home_goals_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 1, 1), else_=0)).label('home_goals_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 2, 1), else_=0)).label('home_goals_gt2'),
        # Голов пропустила домашняя команда
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 0, 1), else_=0)).label('home_goals_conceded_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 1, 1), else_=0)).label('home_goals_conceded_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 2, 1), else_=0)).label('home_goals_conceded_gt2'),
        # Голов забила домашняя команда в первом тайме
        func.sum(case((SoccerTimeline.score_t1_h1 > 0, 1), else_=0)).label('home_goals_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 1, 1), else_=0)).label('home_goals_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 2, 1), else_=0)).label('home_goals_first_half_gt2'),
        # Голов пропустила домашняя команда в первом тайме
        func.sum(case((SoccerTimeline.score_t2_h1 > 0, 1), else_=0)).label('home_goals_conceded_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 1, 1), else_=0)).label('home_goals_conceded_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 2, 1), else_=0)).label('home_goals_conceded_first_half_gt2'),

        # Подсчеты для побед и поражений
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 3, 1), else_=0)).label('home_wins_gt3'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 2, 1), else_=0)).label('home_wins_gt2'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 1, 1), else_=0)).label('home_wins_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 3, 1), else_=0)).label('home_losses_gt3'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 2, 1), else_=0)).label('home_losses_gt2'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 1, 1), else_=0)).label('home_losses_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 == SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2, 1), else_=0)).label('home_draws'),
        # Подсчеты для побед и поражений в первом тайме
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 3, 1), else_=0)).label(
            'home_wins_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 2, 1), else_=0)).label(
            'home_wins_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 1, 1), else_=0)).label(
            'home_wins_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 3, 1), else_=0)).label(
            'home_losses_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 2, 1), else_=0)).label(
            'home_losses_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 1, 1), else_=0)).label(
            'home_losses_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 == SoccerTimeline.score_t2_h1, 1), else_=0)).label(
            'home_draws_first_half'),
    ).join(
        SoccerMain, SoccerTimeline.match_id == SoccerMain.match_id
    ).join(
        ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
    ).join(
        selected_model, SoccerTimeline.match_id == selected_model.match_id
    ).filter(
    SoccerMain.final != 'Awarded'  # Добавляем фильтр на поле final
        )

    # Запрос для выездных игр
    away_query = db.session.query(
        ChampionshipsSoccer.country,
        ChampionshipsSoccer.league,
        SoccerMain.team_away,
        func.count(SoccerMain.match_id).label('total_away_matches'),
        # Голов забила выездная команда
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 0, 1), else_=0)).label('away_goals_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 1, 1), else_=0)).label('away_goals_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 > 2, 1), else_=0)).label('away_goals_gt2'),
        # Голов пропустила выездная команда
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 0, 1), else_=0)).label('away_goals_conceded_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 1, 1), else_=0)).label('away_goals_conceded_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 > 2, 1), else_=0)).label('away_goals_conceded_gt2'),
        # Голов забила выездная команда в первом тайме
        func.sum(case((SoccerTimeline.score_t2_h1 > 0, 1), else_=0)).label('away_goals_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 1, 1), else_=0)).label('away_goals_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t2_h1 > 2, 1), else_=0)).label('away_goals_first_half_gt2'),
        # Голов пропустила выездная команда в первом тайме
        func.sum(case((SoccerTimeline.score_t1_h1 > 0, 1), else_=0)).label('away_goals_conceded_first_half_gt0'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 1, 1), else_=0)).label('away_goals_conceded_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 > 2, 1), else_=0)).label('away_goals_conceded_first_half_gt2'),

        # Подсчеты для побед и поражений
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 3, 1), else_=0)).label('away_wins_gt3'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 2, 1), else_=0)).label('away_wins_gt2'),
        func.sum(case((SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2 - SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t1_h2 >= 1, 1), else_=0)).label('away_wins_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 3, 1), else_=0)).label('away_losses_gt3'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 2, 1), else_=0)).label('away_losses_gt2'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 - SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t2_h2 >= 1, 1), else_=0)).label('away_losses_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 + SoccerTimeline.score_t1_h2 == SoccerTimeline.score_t2_h1 + SoccerTimeline.score_t2_h2, 1), else_=0)).label('away_draws'),
        # Подсчеты для побед и поражений по итогам первого тайма
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 3, 1), else_=0)).label(
            'away_wins_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 2, 1), else_=0)).label(
            'away_wins_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t2_h1 - SoccerTimeline.score_t1_h1 >= 1, 1), else_=0)).label(
            'away_wins_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 3, 1), else_=0)).label(
            'away_losses_first_half_gt3'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 2, 1), else_=0)).label(
            'away_losses_first_half_gt2'),
        func.sum(case((SoccerTimeline.score_t1_h1 - SoccerTimeline.score_t2_h1 >= 1, 1), else_=0)).label(
            'away_losses_first_half_gt1'),
        func.sum(case((SoccerTimeline.score_t1_h1 == SoccerTimeline.score_t2_h1, 1), else_=0)).label(
            'away_draws_first_half'),
    ).join(
        SoccerMain, SoccerTimeline.match_id == SoccerMain.match_id
    ).join(
        ChampionshipsSoccer, SoccerMain.league_id == ChampionshipsSoccer.id
    ).join(
        selected_model, SoccerTimeline.match_id == selected_model.match_id
    ).filter(
    SoccerMain.final != 'Awarded'  # Добавляем фильтр на поле final
        )


    # Фильтрация по стране, лиге и датам (для обоих запросов)
    if country:
        home_query = home_query.filter(ChampionshipsSoccer.country == country)
        away_query = away_query.filter(ChampionshipsSoccer.country == country)
    if league:
        home_query = home_query.filter(ChampionshipsSoccer.league == league)
        away_query = away_query.filter(ChampionshipsSoccer.league == league)
    if team:
        home_query = home_query.filter(SoccerMain.team_home == team,SoccerMain.team_away == opponent)
        away_query = away_query.filter(SoccerMain.team_away == team, SoccerMain.team_home == opponent)
    if date_from:
        home_query = home_query.filter(SoccerMain.match_date >= date_from)
        away_query = away_query.filter(SoccerMain.match_date >= date_from)
    if date_to:
        home_query = home_query.filter(SoccerMain.match_date <= date_to)
        away_query = away_query.filter(SoccerMain.match_date <= date_to)


    if team1_win !=0:
        home_query = home_query.filter(
            selected_model.win_home_open.between(team1_win - team1_win_minus,
                                                  team1_win + team1_win_plus)
        )
        away_query = away_query.filter(
            selected_model.win_away_open.between(team1_win - team1_win_minus,
                                                  team1_win + team1_win_plus)
        )

    # Фильтрация по team1_win_close
    if team1_win_close !=0:
        home_query = home_query.filter(
            selected_model.win_home_close.between(team1_win_close - team1_win_close_minus,
                                                  team1_win_close + team1_win_close_plus)
        )
        away_query = away_query.filter(
            selected_model.win_away_close.between(team1_win_close - team1_win_close_minus,
                                                  team1_win_close + team1_win_close_plus)
        )

    if team1_draw !=0:
        home_query = home_query.filter(
            selected_model.draw_open.between(team1_draw - team1_draw_minus,
                                                  team1_draw + team1_draw_plus)
        )
        away_query = away_query.filter(
            selected_model.draw_open.between(team1_draw - team1_draw_minus,
                                                  team1_draw + team1_draw_plus)
        )

    if team1_draw_close !=0:
        home_query = home_query.filter(
            selected_model.draw_close.between(team1_draw_close - team1_draw_close_minus,
                                                  team1_draw_close + team1_draw_close_plus)
        )
        away_query = away_query.filter(
            selected_model.draw_close.between(team1_draw_close - team1_draw_close_minus,
                                                  team1_draw_close + team1_draw_close_plus)
        )


    if team1_loss !=0:
        home_query = home_query.filter(
            selected_model.win_away_open.between(team1_loss - team1_loss_minus,
                                                  team1_loss + team1_loss_plus)
        )
        away_query = away_query.filter(
            selected_model.win_home_open.between(team1_loss - team1_loss_minus,
                                                  team1_loss + team1_loss_plus)
        )

    if team1_loss_close !=0:
        home_query = home_query.filter(
            selected_model.win_away_open.between(team1_loss_close - team1_loss_close_minus,
                                                  team1_loss_close + team1_loss_close_plus)
        )
        away_query = away_query.filter(
            selected_model.win_home_open.between(team1_loss_close - team1_loss_close_minus,
                                                  team1_loss_close + team1_loss_close_plus)
        )

    if team1_over_1_5 !=0:
        home_query = home_query.filter(
            selected_model.odds_1_5_open.between(team1_over_1_5 - team1_over_1_5_minus,
                                                  team1_over_1_5 + team1_over_1_5_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_1_5_open.between(team1_over_1_5 - team1_over_1_5_minus,
                                                  team1_over_1_5 + team1_over_1_5_plus)
        )

    if team1_over_1_5_close !=0:
        home_query = home_query.filter(
            selected_model.odds_1_5_close.between(team1_over_1_5_close - team1_over_1_5_close_minus,
                                                  team1_over_1_5_close + team1_over_1_5_close_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_1_5_close.between(team1_over_1_5_close - team1_over_1_5_close_minus,
                                                  team1_over_1_5_close + team1_over_1_5_close_plus)
        )

    if team1_over_2_5 != 0:
        home_query = home_query.filter(
            selected_model.odds_2_5_open.between(team1_over_2_5 - team1_over_2_5_minus,
                                                 team1_over_2_5 + team1_over_2_5_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_2_5_open.between(team1_over_2_5 - team1_over_2_5_minus,
                                                 team1_over_2_5 + team1_over_2_5_plus)
        )

    if team1_over_2_5_close != 0:
        home_query = home_query.filter(
            selected_model.odds_2_5_close.between(team1_over_2_5_close - team1_over_2_5_close_minus,
                                                  team1_over_2_5_close + team1_over_2_5_close_plus)
        )
        away_query = away_query.filter(
            selected_model.odds_2_5_close.between(team1_over_2_5_close - team1_over_2_5_close_minus,
                                                  team1_over_2_5_close + team1_over_2_5_close_plus)
        )

    # Группировка по команде, стране и лиге
    home_query = home_query.group_by(SoccerMain.team_home, ChampionshipsSoccer.country, ChampionshipsSoccer.league)
    away_query = away_query.group_by(SoccerMain.team_away, ChampionshipsSoccer.country, ChampionshipsSoccer.league)

    # Выполняем запросы
    home_results = home_query.all()
    away_results = away_query.all()

    # Преобразование результатов в словарь
    result_list = []
    total_home_goals_gt0 = 0
    total_home_goals_gt1 = 0
    total_home_goals_gt2 = 0
    total_home_goals_conceded_gt0 = 0
    total_home_goals_conceded_gt1 = 0
    total_home_goals_conceded_gt2 = 0
    total_home_goals_first_half_gt0 = 0
    total_home_goals_first_half_gt1 = 0
    total_home_goals_first_half_gt2 = 0
    total_home_goals_conceded_first_half_gt0 = 0
    total_home_goals_conceded_first_half_gt1 = 0
    total_home_goals_conceded_first_half_gt2 = 0
    total_home_wins_gt1 = 0
    total_home_wins_gt2 = 0
    total_home_wins_gt3 = 0
    total_home_losses_gt1 = 0
    total_home_losses_gt2 = 0
    total_home_losses_gt3 = 0
    total_home_draws = 0
    total_home_matches = 0
    total_home_wins_gt1_h1 = 0
    total_home_wins_gt2_h1 = 0
    total_home_wins_gt3_h1 = 0
    total_home_losses_gt1_h1 = 0
    total_home_losses_gt2_h1 = 0
    total_home_losses_gt3_h1 = 0
    total_home_draws_h1 = 0

    # Суммирование значений из всех кортежей
    for res in home_results:
        total_home_goals_gt0 += res.home_goals_gt0
        total_home_goals_gt1 += res.home_goals_gt1
        total_home_goals_gt2 += res.home_goals_gt2
        total_home_goals_conceded_gt0 += res.home_goals_conceded_gt0
        total_home_goals_conceded_gt1 += res.home_goals_conceded_gt1
        total_home_goals_conceded_gt2 += res.home_goals_conceded_gt2
        total_home_goals_first_half_gt0 += res.home_goals_first_half_gt0
        total_home_goals_first_half_gt1 += res.home_goals_first_half_gt1
        total_home_goals_first_half_gt2 += res.home_goals_first_half_gt2
        total_home_goals_conceded_first_half_gt0 += res.home_goals_conceded_first_half_gt0
        total_home_goals_conceded_first_half_gt1 += res.home_goals_conceded_first_half_gt1
        total_home_goals_conceded_first_half_gt2 += res.home_goals_conceded_first_half_gt2
        total_home_wins_gt1 += res.home_wins_gt1
        total_home_wins_gt2 += res.home_wins_gt2
        total_home_wins_gt3 += res.home_wins_gt3
        total_home_losses_gt1 += res.home_losses_gt1
        total_home_losses_gt2 += res.home_losses_gt2
        total_home_losses_gt3 += res.home_losses_gt3
        total_home_draws += res.home_draws

        total_home_wins_gt1_h1 += res.home_wins_first_half_gt1
        total_home_wins_gt2_h1 += res.home_wins_first_half_gt2
        total_home_wins_gt3_h1 += res.home_wins_first_half_gt3
        total_home_losses_gt1_h1 += res.home_losses_first_half_gt1
        total_home_losses_gt2_h1 += res.home_losses_first_half_gt2
        total_home_losses_gt3_h1 += res.home_losses_first_half_gt3
        total_home_draws_h1 += res.home_draws_first_half
        total_home_matches += res.total_home_matches

    # Создание итогового словаря
    home_result_dict = {
        'home': {
            'scored': {
                'gt0': total_home_goals_gt0,
                'gt1': total_home_goals_gt1,
                'gt2': total_home_goals_gt2
            },
            'conceded': {
                'gt0': total_home_goals_conceded_gt0,
                'gt1': total_home_goals_conceded_gt1,
                'gt2': total_home_goals_conceded_gt2
            },
            'first_half': {
                'scored': {
                    'gt0': total_home_goals_first_half_gt0,
                    'gt1': total_home_goals_first_half_gt1,
                    'gt2': total_home_goals_first_half_gt2
                },
                'conceded': {
                    'gt0': total_home_goals_conceded_first_half_gt0,
                    'gt1': total_home_goals_conceded_first_half_gt1,
                    'gt2': total_home_goals_conceded_first_half_gt2
                },
                'wins': {
                    'wins': total_home_wins_gt1_h1,
                    'gt1': total_home_wins_gt2_h1,
                    'gt2': total_home_wins_gt3_h1
            },
                'losses': {
                    'lose': total_home_losses_gt1_h1,
                    'gt1': total_home_losses_gt2_h1,
                    'gt2': total_home_losses_gt3_h1
                },
                'draws': total_home_draws_h1
            },
            'wins': {
                'wins': total_home_wins_gt1,
                'gt1': total_home_wins_gt2,
                'gt2': total_home_wins_gt3
            },
            'losses': {
                'lose': total_home_losses_gt1,
                'gt1': total_home_losses_gt2,
                'gt2': total_home_losses_gt3
            },
            'draws': total_home_draws,
            'number': total_home_matches
        }
    }

    result_list.append(home_result_dict)

    total_away_goals_gt0 = 0
    total_away_goals_gt1 = 0
    total_away_goals_gt2 = 0
    total_away_goals_conceded_gt0 = 0
    total_away_goals_conceded_gt1 = 0
    total_away_goals_conceded_gt2 = 0
    total_away_goals_first_half_gt0 = 0
    total_away_goals_first_half_gt1 = 0
    total_away_goals_first_half_gt2 = 0
    total_away_goals_conceded_first_half_gt0 = 0
    total_away_goals_conceded_first_half_gt1 = 0
    total_away_goals_conceded_first_half_gt2 = 0
    total_away_wins_gt1 = 0
    total_away_wins_gt2 = 0
    total_away_wins_gt3 = 0
    total_away_losses_gt1 = 0
    total_away_losses_gt2 = 0
    total_away_losses_gt3 = 0
    total_away_draws = 0
    total_away_matches = 0
    total_away_wins_gt1_h1 = 0
    total_away_wins_gt2_h1 = 0
    total_away_wins_gt3_h1 = 0
    total_away_losses_gt1_h1 = 0
    total_away_losses_gt2_h1 = 0
    total_away_losses_gt3_h1 = 0
    total_away_draws_h1 = 0

    # Суммирование значений из всех кортежей
    for res in away_results:
        total_away_goals_gt0 += res.away_goals_gt0
        total_away_goals_gt1 += res.away_goals_gt1
        total_away_goals_gt2 += res.away_goals_gt2
        total_away_goals_conceded_gt0 += res.away_goals_conceded_gt0
        total_away_goals_conceded_gt1 += res.away_goals_conceded_gt1
        total_away_goals_conceded_gt2 += res.away_goals_conceded_gt2
        total_away_goals_first_half_gt0 += res.away_goals_first_half_gt0
        total_away_goals_first_half_gt1 += res.away_goals_first_half_gt1
        total_away_goals_first_half_gt2 += res.away_goals_first_half_gt2
        total_away_goals_conceded_first_half_gt0 += res.away_goals_conceded_first_half_gt0
        total_away_goals_conceded_first_half_gt1 += res.away_goals_conceded_first_half_gt1
        total_away_goals_conceded_first_half_gt2 += res.away_goals_conceded_first_half_gt2
        total_away_wins_gt1 += res.away_wins_gt1
        total_away_wins_gt2 += res.away_wins_gt2
        total_away_wins_gt3 += res.away_wins_gt3
        total_away_losses_gt1 += res.away_losses_gt1
        total_away_losses_gt2 += res.away_losses_gt2
        total_away_losses_gt3 += res.away_losses_gt3
        total_away_draws += res.away_draws

        total_away_wins_gt1_h1 += res.away_wins_first_half_gt1
        total_away_wins_gt2_h1 += res.away_wins_first_half_gt2
        total_away_wins_gt3_h1 += res.away_wins_first_half_gt3
        total_away_losses_gt1_h1 += res.away_losses_first_half_gt1
        total_away_losses_gt2_h1 += res.away_losses_first_half_gt2
        total_away_losses_gt3_h1 += res.away_losses_first_half_gt3
        total_away_draws_h1 += res.away_draws_first_half
        total_away_matches += res.total_away_matches

    # Создание итогового словаря
    away_result_dict = {
        'away': {
            'scored': {
                'gt0': total_away_goals_gt0,
                'gt1': total_away_goals_gt1,
                'gt2': total_away_goals_gt2
            },
            'conceded': {
                'gt0': total_away_goals_conceded_gt0,
                'gt1': total_away_goals_conceded_gt1,
                'gt2': total_away_goals_conceded_gt2
            },
            'first_half': {
                'scored': {
                    'gt0': total_away_goals_first_half_gt0,
                    'gt1': total_away_goals_first_half_gt1,
                    'gt2': total_away_goals_first_half_gt2
                },
                'conceded': {
                    'gt0': total_away_goals_conceded_first_half_gt0,
                    'gt1': total_away_goals_conceded_first_half_gt1,
                    'gt2': total_away_goals_conceded_first_half_gt2
                },
                'wins': {
                    'wins': total_away_wins_gt1_h1,
                    'gt1': total_away_wins_gt2_h1,
                    'gt2': total_away_wins_gt3_h1
                },
                'losses': {
                    'lose': total_away_losses_gt1_h1,
                    'gt1': total_away_losses_gt2_h1,
                    'gt2': total_away_losses_gt3_h1
                },
                'draws': total_away_draws_h1
            },
            'wins': {
                'wins': total_away_wins_gt1,
                'gt1': total_away_wins_gt2,
                'gt2': total_away_wins_gt3
            },
            'losses': {
                'lose': total_away_losses_gt1,
                'gt1': total_away_losses_gt2,
                'gt2': total_away_losses_gt3
            },
            'draws': total_away_draws,
            'number': total_away_matches  # Ничьи
        }
    }

    # Добавление итогового словаря в список результатов
    result_list.append(away_result_dict)

    return result_list


