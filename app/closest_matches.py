from datetime import date, datetime
from app import app, db
from app.models import SoccerMain


class MatchFinder:
    def __init__(self):
        pass

    def find_closest_matches_with_stats(self, team1, team2, opponent=None):
        with app.app_context():
            today = datetime.today().date()

            # Найти ближайший домашний матч для team1 против opponent
            home_matches_team1 = db.session.query(SoccerMain).filter(
                SoccerMain.team_home == team1,
                SoccerMain.team_away == opponent
            ).order_by(SoccerMain.match_date).all()

            # Найти ближайший домашний матч для team2 против opponent
            home_matches_team2 = db.session.query(SoccerMain).filter(
                SoccerMain.team_home == team2,
                SoccerMain.team_away == opponent
            ).order_by(SoccerMain.match_date).all()

            # Найти ближайший гостевой матч для team1 против opponent
            away_matches_team1 = db.session.query(SoccerMain).filter(
                SoccerMain.team_away == team1,
                SoccerMain.team_home == opponent
            ).order_by(SoccerMain.match_date).all()

            # Найти ближайший гостевой матч для team2 против opponent
            away_matches_team2 = db.session.query(SoccerMain).filter(
                SoccerMain.team_away == team2,
                SoccerMain.team_home == opponent
            ).order_by(SoccerMain.match_date).all()

            closest_home_team1 = self._find_closest_match(home_matches_team1, today)
            closest_home_team2 = self._find_closest_match(home_matches_team2, today)
            closest_away_team1 = self._find_closest_match(away_matches_team1, today)
            closest_away_team2 = self._find_closest_match(away_matches_team2, today)

            home_matches_info = []
            away_matches_info = []

            if closest_home_team1 and closest_home_team2:
                home_matches_info = self._get_match_stats(team1, team2, closest_home_team1, closest_home_team2, "home", opponent)

            if closest_away_team1 and closest_away_team2:
                away_matches_info = self._get_match_stats(team1, team2, closest_away_team1, closest_away_team2, "away", opponent)

            return {
                "home_matches": home_matches_info,
                "away_matches": away_matches_info
            }

    def find_closest_home_match(self, team1, team2):
        """ Найти ближайший матч, где команды играют дома с одним соперником (без указания соперника) """
        with app.app_context():
            today = date.today()

            # Найти домашние матчи для team1 и team2
            matches_team1 = db.session.query(SoccerMain).filter(SoccerMain.team_home == team1).all()
            matches_team2 = db.session.query(SoccerMain).filter(SoccerMain.team_home == team2).all()

            closest_match = None
            min_date_diff = None

            # Поиск матчей для team1
            for match1 in matches_team1:
                # Поиск матчей для team2 с тем же соперником
                for match2 in matches_team2:
                    if match1.team_away == match2.team_away:  # Один и тот же соперник в гостях
                        # Проверка разницы дат
                        date_diff = abs((match1.match_date - match2.match_date).days)
                        today_diff1 = abs((match1.match_date - today).days)
                        today_diff2 = abs((match2.match_date - today).days)

                        # Находим ближайшую к сегодняшнему дню дату для обеих команд
                        if min_date_diff is None or (today_diff1 < min_date_diff and today_diff2 < min_date_diff):
                            min_date_diff = min(today_diff1, today_diff2)
                            closest_match = (match1, match2)

            if closest_match:
                return self._get_match_stats(team1, team2, closest_match[0], closest_match[1], "home")
            return None

    def find_closest_away_match(self, team1, team2):
        """ Найти ближайший матч, где команды играют в гостях против одного соперника (без указания соперника) """
        with app.app_context():
            today = date.today()

            # Найти гостевые матчи для team1 и team2
            matches_team1 = db.session.query(SoccerMain).filter(SoccerMain.team_away == team1).all()
            matches_team2 = db.session.query(SoccerMain).filter(SoccerMain.team_away == team2).all()

            closest_match = None
            min_date_diff = None

            # Поиск матчей для team1
            for match1 in matches_team1:
                # Поиск матчей для team2 против того же соперника (дома)
                for match2 in matches_team2:
                    if match1.team_home == match2.team_home:  # Один и тот же соперник дома
                        # Проверка разницы дат
                        date_diff = abs((match1.match_date - match2.match_date).days)
                        today_diff1 = abs((match1.match_date - today).days)
                        today_diff2 = abs((match2.match_date - today).days)

                        # Находим ближайшую к сегодняшнему дню дату для обеих команд
                        if min_date_diff is None or (today_diff1 < min_date_diff and today_diff2 < min_date_diff):
                            min_date_diff = min(today_diff1, today_diff2)
                            closest_match = (match1, match2)

            if closest_match:
                return self._get_match_stats(team1, team2, closest_match[0], closest_match[1], "away")
            return None

    def _find_closest_match(self, matches, today):
        for match in matches:
            if match.match_date >= today:
                return match
        return matches[-1] if matches else None

    def _calculate_days_since_last_match(self, match, today):
        return (today - match.match_date).days if match else None

    def _calculate_matches_played(self, team, since_date):
        with app.app_context():
            return db.session.query(SoccerMain).filter(
                (SoccerMain.team_home == team) | (SoccerMain.team_away == team),
                SoccerMain.match_date > since_date
            ).count()

    def _get_match_stats(self, team1, team2, match1, match2, location, opponent=None):
        today = datetime.today().date()

        days_team1 = self._calculate_days_since_last_match(match1, today)
        days_team2 = self._calculate_days_since_last_match(match2, today)

        matches_played_team1 = self._calculate_matches_played(team1, match1.match_date)
        matches_played_team2 = self._calculate_matches_played(team2, match2.match_date)

        return {
            "team1": {
                "match_id": match1.match_id,
                "opponent": opponent if opponent else (match1.team_home if location == "away" else match1.team_away),
                # Определяем соперника в зависимости от типа матча
                "match_date": match1.match_date,
                "days_since_last_match": days_team1,
                "matches_played_since": matches_played_team1
            },
            "team2": {
                "match_id": match2.match_id,
                "opponent": opponent if opponent else (match2.team_home if location == "away" else match2.team_away),
                # Аналогично для второй команды
                "match_date": match2.match_date,
                "days_since_last_match": days_team2,
                "matches_played_since": matches_played_team2
            },
            "location": location
        }
def extract_match_ids(home_match, away_match, matches_with_opponent):
    match_ids = []

    # Извлечение match_id для домашнего матча
    if home_match and 'team1' in home_match:
        match_ids.append(home_match['team1']['match_id'])
    if home_match and 'team2' in home_match:
        match_ids.append(home_match['team2']['match_id'])

    # Извлечение match_id для выездного матча
    if away_match and 'team1' in away_match:
        match_ids.append(away_match['team1']['match_id'])
    if away_match and 'team2' in away_match:
        match_ids.append(away_match['team2']['match_id'])

    # Извлечение match_id для матчей с оппонентом
    if matches_with_opponent:
        if 'home_matches' in matches_with_opponent:
            if 'team1' in matches_with_opponent['home_matches']:
                match_ids.append(matches_with_opponent['home_matches']['team1']['match_id'])
            if 'team2' in matches_with_opponent['home_matches']:
                match_ids.append(matches_with_opponent['home_matches']['team2']['match_id'])

        if 'away_matches' in matches_with_opponent:
            if 'team1' in matches_with_opponent['away_matches']:
                match_ids.append(matches_with_opponent['away_matches']['team1']['match_id'])
            if 'team2' in matches_with_opponent['away_matches']:
                match_ids.append(matches_with_opponent['away_matches']['team2']['match_id'])

    return match_ids

def odds_calc(match_ids, bookmaker_model):
    # Извлечение матчей с заданными match_id
    matches = db.session.query(bookmaker_model).filter(bookmaker_model.match_id.in_(match_ids)).all()

    # Создаем словарь, чтобы быстро находить данные по match_id
    matches_dict = {match.match_id: match for match in matches}

    odds_data = []
    # Проходим по match_ids в заданной последовательности
    for match_id in match_ids:
        match = matches_dict.get(match_id)  # Получаем матч по match_id
        if match:
            match_odds = {
                'match_id_e': match.match_id,
                'win_home_open_e': match.win_home_open,
                'win_home_close_e': match.win_home_close,
                'draw_open_e': match.draw_open,
                'draw_close_e': match.draw_close,
                'win_away_open_e': match.win_away_open,
                'win_away_close_e': match.win_away_close,
                'odds_1_5_open_e': match.odds_1_5_open,
                'odds_1_5_close_e': match.odds_1_5_close,
                'odds_2_5_open_e': match.odds_2_5_open,
                'odds_2_5_close_e': match.odds_2_5_close,
            }
            odds_data.append(match_odds)
        else:
            # Если матч не найден, можно добавить пустые значения или пропустить
            odds_data.append({'match_id': match_id, 'error': 'Match not found'})

    return odds_data



