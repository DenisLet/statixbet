from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
import requests
import time
import threading
from fake_useragent import UserAgent

app = Flask(__name__)
socketio = SocketIO(app)

matches_data = []
last_request_time = 0  # Время последнего GET-запроса
last_sent_data = []  # Последние отправленные данные


SEND_INTERVAL = 30
TARGET_URL = 'http://127.0.0.1:5000/current_matches'

def fetch_live_matches():
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    url = 'https://www.sofascore.com/api/v1/sport/football/events/live'
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('events', [])
    except requests.RequestException:
        return []

def fetch_match_statistics(match_id):
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    stats_url = f'https://www.sofascore.com/api/v1/event/{match_id}/statistics'
    try:
        response = requests.get(stats_url, headers=headers)
        response.raise_for_status()
        return response.json().get('statistics', [])
    except requests.RequestException:
        return []

def calculate_current_minute(time_data, match_status):
    current_period_start = time_data.get('currentPeriodStartTimestamp')
    initial = time_data.get('initial', 0)

    if not current_period_start or match_status.lower() in [
        "halftime", "break", "finished", "postponed", "penalties", "awaiting extra time",
        "awaiting penalties", "1st extra", "2nd extra", "awaiting"
    ]:
        return None

    current_timestamp = time.time()
    elapsed_time = current_timestamp - current_period_start + initial
    current_minute = int(elapsed_time // 60)
    return f"{current_minute}'"

def extract_required_statistics(statistics):
    required_stats_keys = {
        'cornerKicks': 'Corners',
        'shotsOnGoal': 'Shots on Goal',
        'totalShotsOnGoal': 'Shots',
        'yellowCards': 'Yellow Cards',
        'fouls': 'Fouls',
        'offsides': 'Offsides'
    }

    stats_result = {}

    for period_data in statistics:
        period = period_data.get('period')
        stats_result[period] = {}
        for group in period_data.get('groups', []):
            for item in group.get('statisticsItems', []):
                key = item.get('key')
                if key in required_stats_keys:
                    stat_name = required_stats_keys[key]
                    home_value = item.get('home', 0)
                    away_value = item.get('away', 0)
                    stats_result[period][stat_name] = {
                        'home': home_value,
                        'away': away_value
                    }
    return stats_result

def update_matches_data():
    global matches_data, last_sent_data

    while True:
        live_matches = fetch_live_matches()
        if not live_matches:
            matches_data = []

        updated_data = []  # Новые данные для отправки
        for event in live_matches:
            match_id = event.get('id')
            home_team = event.get('homeTeam', {}).get('name', 'N/A')
            away_team = event.get('awayTeam', {}).get('name', 'N/A')

            status = event.get('status', {})
            match_status = status.get('description', 'N/A')

            time_data = event.get('time', {})
            current_minute = calculate_current_minute(time_data, match_status)
            current_minute = int(current_minute.replace("'", "")) if current_minute is not None else None
            if current_minute is None and match_status.lower() != "halftime":
                continue

            tournament = event.get('tournament', {})
            league = tournament.get('name', 'N/A')
            country = tournament.get('category', {}).get('name', 'N/A')

            current_score1 = event.get('homeScore', {}).get('current', 0)
            current_score2 = event.get('awayScore', {}).get('current', 0)
            home_score_1st = event.get('homeScore', {}).get('period1', 0)
            away_score_1st = event.get('awayScore', {}).get('period1', 0)
            home_score_2nd = int(current_score1) - int(home_score_1st)
            away_score_2nd = int(current_score2) - int(away_score_1st)

            if match_status.lower() in ['1st half', 'halftime']:
                home_score_2nd = 0
                away_score_2nd = 0
                if home_score_1st != current_score1:
                    home_score_1st = current_score1
                if away_score_1st != current_score2:
                    away_score_1st = current_score2

            statistics = fetch_match_statistics(match_id)
            stats = extract_required_statistics(statistics) if statistics else {}

            updated_data.append({
                'match_id': match_id,
                'home_team': home_team,
                'away_team': away_team,
                'league': league,
                'country': country,
                'half': match_status.replace('half', ''),
                'current_minute': current_minute if current_minute else 'Halftime',
                'home_score': current_score1,
                'away_score': current_score2,
                'home_score_first_half': home_score_1st,
                'away_score_first_half': away_score_1st,
                'home_score_second_half': home_score_2nd,
                'away_score_second_half': away_score_2nd,
                'stats': stats
            })

        matches_data = updated_data  # Обновляем данные
        print(matches_data)
        if updated_data != last_sent_data:
            # Отправляем данные через WebSocket
            socketio.emit('update_matches', updated_data)
            last_sent_data = updated_data  # Обновляем отправленные данные

        time.sleep(30)

def auto_send_if_no_requests():
    global last_request_time
    while True:
        current_time = time.time()
        if current_time - last_request_time > SEND_INTERVAL and matches_data:
            # Отправляем данные через WebSocket
            socketio.emit('update_matches', matches_data)
        time.sleep(30)
@app.route('/', methods=['GET'])
@app.route('/api/live_matches', methods=['GET'])
def get_live_matches():
    global last_request_time
    last_request_time = time.time()


    return jsonify(matches_data)

if __name__ == '__main__':
    threading.Thread(target=update_matches_data, daemon=True).start()
    threading.Thread(target=auto_send_if_no_requests, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5001)
