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


def calculate_gth1(l1, l2):
    # Извлекаем данные из списков
    team1_cases = {x[0]: (x[1], x[2] / 100) for x in l1}  # (номер, количество, процент)
    team2_cases = {x[0]: (x[1], x[2] / 100) for x in l2}  # (номер, количество, процент)

    # Вероятности для указанных исходов
    p_0_0 = team1_cases.get(0, (0, 0))[1] * team2_cases.get(0, (0, 0))[1]
    p_0_1 = team1_cases.get(0, (0, 0))[1] * team2_cases.get(1, (0, 0))[1]
    p_1_0 = team1_cases.get(1, (0, 0))[1] * team2_cases.get(0, (0, 0))[1]

    # Вероятность ровно одного гола в матче (0:1 или 1:0)
    p_exactly_1 = p_0_1 + p_1_0

    # Сумма вероятностей указанных исходов
    sum_specified = p_0_0 + p_0_1 + p_1_0

    # Вероятность других исходов
    p_other = 1 - sum_specified

    return round(p_exactly_1*100, 2) , round(p_other*100, 2)


print(count_odds_diff(2.37, 2.572))