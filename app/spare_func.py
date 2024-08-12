def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def count_odds_diff(old: float, new: float) -> (float, float):
    if old is None or new is None:
        return 0.0, 0.0
    diff_value = round(old - new, 3)
    diff_percent = round((diff_value * 100 / new), 2)
    return -diff_value, diff_percent


print(count_odds_diff(2.37, 2.572))