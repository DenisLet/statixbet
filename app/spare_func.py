
def count_odds_diff(old: float, new: float) -> (float, float):
    if new and old:
        diff_value = round(old - new, 3)
        diff_percent = round((diff_value*100/new), 2)
        return -diff_value, diff_percent



print(count_odds_diff(2.37, 2.572))