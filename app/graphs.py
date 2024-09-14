import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.ticker import MaxNLocator
import math

def plot_goals(goals_list, interval_70_to_end=(70, 120), title=''):
    intervals = [(45, 50), (50, 55), (55, 60), (60, 65), (65, 70), (70, 75), (75, 80), (80, 85), (85, 90), (90, 120)]
    first_goals_per_interval = {interval: 0 for interval in intervals}
    first_goals_70_to_end = 0

    if not goals_list:
        return None

    total_matches = len(goals_list)
    if total_matches == 0:
        return None

    for match in goals_list:
        if match:
            first_goal_time = min(match)
            for interval in intervals:
                if interval[0] <first_goal_time <= interval[1]:
                    first_goals_per_interval[interval] += 1
                    break
            if first_goal_time >= interval_70_to_end[0]:
                first_goals_70_to_end += 1

    first_goals_percentage = [count / total_matches * 100 for count in first_goals_per_interval.values()]
    first_goals_70_to_end_percentage = first_goals_70_to_end / total_matches * 100

    fig, ax1 = plt.subplots(figsize=(12, 7))

    bar_container = ax1.bar(
        [f'{interval[0]}-{interval[1]}' if interval[0] != 90 else '90+' for interval in intervals],
        first_goals_per_interval.values(),
        color='#4CAF50',
        label='Первый гол'
    )

    bar_70_to_end = ax1.bar(
        '70+',
        first_goals_70_to_end,
        color='#9C27B0',
        label='70-95 минут'
    )

    ax1.set_xlabel('Timing (minutes)', fontsize=25)
    ax1.set_ylabel('Number of 1st goals in 2nd half', fontsize=25)
    ax1.set_title(title, fontsize=25)

    ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

    for i, bar in enumerate(bar_container):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, height, f'{first_goals_percentage[i]:.1f}%', ha='center',
                 va='bottom', fontsize=25)

    height_70_to_end = bar_70_to_end[0].get_height()
    ax1.text(bar_70_to_end[0].get_x() + bar_70_to_end[0].get_width() / 2, height_70_to_end,
             f'{first_goals_70_to_end_percentage:.1f}%', ha='center', va='bottom', fontsize=25)

    fig.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return img_base64


def plot_yc(goals_list, interval_70_to_end=(80, 120), title=''):
    intervals = [(45, 50), (50, 55), (55, 60), (60, 65), (65, 70), (70, 75), (75, 80), (80, 85), (85, 90), (90, 120)]
    first_goals_per_interval = {interval: 0 for interval in intervals}
    first_goals_70_to_end = 0

    if not goals_list:
        return None

    total_matches = len(goals_list)
    if total_matches == 0:
        return None

    for match in goals_list:
        if match:
            first_goal_time = min(match)
            for interval in intervals:
                if interval[0] <first_goal_time <= interval[1]:
                    first_goals_per_interval[interval] += 1
                    break
            if first_goal_time >= interval_70_to_end[0]:
                first_goals_70_to_end += 1

    first_goals_percentage = [count / total_matches * 100 for count in first_goals_per_interval.values()]
    first_goals_70_to_end_percentage = first_goals_70_to_end / total_matches * 100

    # Создаем фигуру с увеличенными размерами текста
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Изменение цветов баров
    bar_container = ax1.bar(
        [f'{interval[0]}-{interval[1]}' if interval[0] != 90 else '90+' for interval in intervals],
        first_goals_per_interval.values(),
        color='#4CAF50',
        label='1st YC'  # Изящный зеленый цвет
    )

    bar_70_to_end = ax1.bar(
        '80+',
        first_goals_70_to_end,
        color='#9C27B0',
        label='70-95 минут'  # Элегантный фиолетовый
    )

    # Увеличение шрифта для меток осей, заголовка и текста на графике
    ax1.set_xlabel('Timing (minutes)', fontsize=25)
    ax1.set_ylabel('Number of 1st YC in 2nd half', fontsize=25)
    ax1.set_title(title, fontsize=25)

    # Установка целочисленных значений по оси Y
    ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Добавляем процентные метки на бары с увеличенным шрифтом
    for i, bar in enumerate(bar_container):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, height, f'{first_goals_percentage[i]:.1f}%', ha='center',
                 va='bottom', fontsize=25)

    height_70_to_end = bar_70_to_end[0].get_height()
    ax1.text(bar_70_to_end[0].get_x() + bar_70_to_end[0].get_width() / 2, height_70_to_end,
             f'{first_goals_70_to_end_percentage:.1f}%', ha='center', va='bottom', fontsize=25)

    # Применяем tight layout для лучшей компоновки
    fig.tight_layout()

    # Сохраняем график в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Конвертируем изображение в base64
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return img_base64


def calculate_percentage(goals_list):
    total_matches = len(goals_list)
    matches_with_goals = sum(1 for i in goals_list if len(i) > 0)
    percentage = (matches_with_goals / total_matches) * 100 if total_matches > 0 else 0
    return percentage, matches_with_goals, total_matches

def filter_goals(goals_list, time=70):
    nogoal_before70_list = []
    for i in goals_list:
        try:
            i.sort()
            if len(i) == 0:
                nogoal_before70_list.append([])
            elif i[0] > time:
                nogoal_before70_list.append(i)
        except:
            continue
    return nogoal_before70_list


def plot_area_chart(goals_h2, home_goals_h2, away_goals_h2):
    # Фильтруем данные
    filtered_goals_h2 = filter_goals(goals_h2)
    filtered_home_goals_h2 = filter_goals(home_goals_h2)
    filtered_away_goals_h2 = filter_goals(away_goals_h2)

    # Рассчитываем проценты и количество матчей с голами / общее количество матчей
    percentages = {
        'All Matches': calculate_percentage(filtered_goals_h2),
        'Home Matches': calculate_percentage(filtered_home_goals_h2),
        'Away Matches': calculate_percentage(filtered_away_goals_h2)
    }

    # Создаем фигуру с увеличенными размерами текста
    plt.figure(figsize=(12, 7))

    # Строим площадной график
    plt.fill_between(percentages.keys(), [p[0] for p in percentages.values()], color='skyblue', alpha=0.4)
    plt.plot(percentages.keys(), [p[0] for p in percentages.values()], color='Slateblue', alpha=0.6)

    # Добавление подписей значений на самом графике с указанием отношения матчей с голами к общему количеству матчей
    for i, (key, (percentage, matches_with_goals, total_matches)) in enumerate(percentages.items()):
        x = i
        y = percentage
        text = f'{percentage:.1f}% ({matches_with_goals}/{total_matches})'

        # Позиционирование текста
        if i == 0:  # Для первого значения
            xytext = (10, 5)
            ha = 'left'
        elif i == len(percentages) - 1:  # Для последнего значения
            xytext = (-10, 5)
            ha = 'right'
        else:  # Для всех остальных значений
            xytext = (0, 5)
            ha = 'center'

        plt.annotate(
            text,
            xy=(x, y),
            xytext=xytext,
            textcoords='offset points',
            ha=ha,
            fontsize=15,
            color='black',
            clip_on=True
        )

    # Увеличение шрифта для меток осей и заголовка
    plt.xlabel('Teams', fontsize=25)
    plt.ylabel('Matches with Goals (%)', fontsize=25)
    plt.title('Area Matches with Goals', fontsize=25)

    # Устанавливаем единые лимиты оси Y
    plt.ylim(0, 100)

    # Добавляем сетку для оси Y
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Применяем tight layout
    plt.tight_layout()

    # Сохраняем график в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Конвертируем изображение в base64
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return img_base64


def plot_area_chart_yc(goals_h2, home_goals_h2, away_goals_h2):
    # Фильтруем данные
    filtered_goals_h2 = filter_goals(goals_h2,time=80)
    filtered_home_goals_h2 = filter_goals(home_goals_h2,time=80)
    filtered_away_goals_h2 = filter_goals(away_goals_h2,time=80)

    # Рассчитываем проценты и количество матчей с голами / общее количество матчей
    percentages = {
        'All Matches': calculate_percentage(filtered_goals_h2),
        'Home Matches': calculate_percentage(filtered_home_goals_h2),
        'Away Matches': calculate_percentage(filtered_away_goals_h2)
    }

    # Создаем фигуру с увеличенными размерами текста
    plt.figure(figsize=(12, 7))

    # Строим площадной график
    plt.fill_between(percentages.keys(), [p[0] for p in percentages.values()], color='skyblue', alpha=0.4)
    plt.plot(percentages.keys(), [p[0] for p in percentages.values()], color='Slateblue', alpha=0.6)

    # Добавление подписей значений на самом графике с указанием отношения матчей с голами к общему количеству матчей
    for i, (key, (percentage, matches_with_goals, total_matches)) in enumerate(percentages.items()):
        x = i
        y = percentage
        text = f'{percentage:.1f}% ({matches_with_goals}/{total_matches})'

        # Позиционирование текста
        if i == 0:  # Для первого значения
            xytext = (10, 5)
            ha = 'left'
        elif i == len(percentages) - 1:  # Для последнего значения
            xytext = (-10, 5)
            ha = 'right'
        else:  # Для всех остальных значений
            xytext = (0, 5)
            ha = 'center'

        plt.annotate(
            text,
            xy=(x, y),
            xytext=xytext,
            textcoords='offset points',
            ha=ha,
            fontsize=15,
            color='black',
            clip_on=True
        )

    # Увеличение шрифта для меток осей и заголовка
    plt.xlabel('Teams', fontsize=25)
    plt.ylabel('Matches with YC (%)', fontsize=25)
    plt.title('Area Matches with YC', fontsize=25)

    # Устанавливаем единые лимиты оси Y
    plt.ylim(0, 100)

    # Добавляем сетку для оси Y
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Применяем tight layout
    plt.tight_layout()

    # Сохраняем график в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Конвертируем изображение в base64
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return img_base64


def plot_1goal_distribution(goals_h2):
    def count_goals_by_periods(goals_h2):
        periods = [
            range(46, 51),
            range(51, 56),
            range(56, 61),
            range(61, 66),
            range(66, 71),
            range(71, 76),
            range(76, 81),
            range(81, 86),
            range(86, 91),
            range(91, 120)
        ]

        period_counts = {i: 0 for i in range(10)}

        for i, period in enumerate(periods):
            for goal_list in goals_h2:
                if goal_list and goal_list[0] in period:
                    period_counts[i] += 1

        return period_counts

    # Подсчитываем количество голов по периодам
    goals_by_period = count_goals_by_periods(goals_h2)

    # Общее количество голов
    total_goals = len(goals_h2)

    # Названия периодов
    period_labels = ['46-50', '51-55', '56-60', '61-65', '66-70', '71-75', '76-80', '81-85', '86-90', '90+']

    # Количество голов для каждого периода
    period_values = [goals_by_period[i] for i in range(10)]

    # Рассчитываем сумму голов для периодов от 76 и выше
    summed_period_values = sum(period_values[6:])

    # Создаем фигуру
    plt.figure(figsize=(10, 6))

    # Построение обычных баров с шириной, которая убирает расстояния между ними
    bars = plt.bar(period_labels, period_values, color='#4CAF50', width=1)

    # Добавление полупрозрачного бара поверх баров начиная с 76 минуты
    for i in range(6, 10):
        plt.bar(
            period_labels[i],  # Метка периода
            summed_period_values,  # Сумма голов для всех периодов с 75 минуты и выше
            width=1,  # Ширина бара (без пробелов)
            color='#4CAF50',  # Цвет бара
            alpha=0.3  # Прозрачность
        )

    # Добавление процентных значений над барами
    for bar in bars:
        yval = bar.get_height()
        if total_goals > 0:
            plt.text(bar.get_x() + bar.get_width()/2, yval, f'{(yval / total_goals) * 100:.1f}%', ha='center', va='bottom')
        else:
            plt.text(bar.get_x() + bar.get_width()/2, yval, '0.0%', ha='center', va='bottom')

    # Добавление процентного значения для суммарного бара
    if total_goals > 0:
        summed_percentage = (summed_period_values / total_goals) * 100
    else:
        summed_percentage = 0

    summed_bar_x = bars[5].get_x()  # Положение суммарного бара в x
    plt.text(
        summed_bar_x + 2.5,  # Смещение для корректного позиционирования текста
        summed_period_values,
        f'{summed_percentage:.1f}%',
        ha='center',
        va='bottom',
        color='black'
    )

    # Настройки осей и заголовок
    plt.xlabel('Time  periods')
    plt.ylabel('Number of goals')
    plt.title('At least 1 goal scored in periods in %')

    # Сохранение графика в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Конвертация изображения в base64
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return img_base64


def plot_1yc_distribution(goals_h2):
    def count_goals_by_periods(goals_h2):
        periods = [
            range(46, 51),
            range(51, 56),
            range(56, 61),
            range(61, 66),
            range(66, 71),
            range(71, 76),
            range(76, 81),
            range(81, 86),
            range(86, 91),
            range(91, 120)
        ]

        period_counts = {i: 0 for i in range(10)}

        for i, period in enumerate(periods):
            for goal_list in goals_h2:
                if goal_list and goal_list[0] in period:
                    period_counts[i] += 1

        return period_counts

    # Подсчитываем количество голов по периодам
    goals_by_period = count_goals_by_periods(goals_h2)

    # Общее количество голов
    total_goals = len(goals_h2)

    # Названия периодов
    period_labels = ['46-50', '51-55', '56-60', '61-65', '66-70', '71-75', '76-80', '81-85', '86-90', '90+']

    # Количество голов для каждого периода
    period_values = [goals_by_period[i] for i in range(10)]

    # Рассчитываем сумму голов для периодов от 76 и выше
    summed_period_values = sum(period_values[5:])

    # Создаем фигуру
    plt.figure(figsize=(10, 6))

    # Построение обычных баров с шириной, которая убирает расстояния между ними
    bars = plt.bar(period_labels, period_values, color='#4CAF50', width=1)

    # Добавление полупрозрачного бара поверх баров начиная с 76 минуты
    for i in range(6, 10):
        plt.bar(
            period_labels[i],  # Метка периода
            summed_period_values,  # Сумма голов для всех периодов с 75 минуты и выше
            width=1,  # Ширина бара (без пробелов)
            color='#9C27B0',  # Цвет бара
            alpha=0.3  # Прозрачность
        )

    # Добавление процентных значений над барами
    for bar in bars:
        yval = bar.get_height()
        if total_goals > 0:
            plt.text(bar.get_x() + bar.get_width()/2, yval, f'{(yval / total_goals) * 100:.1f}%', ha='center', va='bottom')
        else:
            plt.text(bar.get_x() + bar.get_width()/2, yval, '0.0%', ha='center', va='bottom')

    # Добавление процентного значения для суммарного бара
    if total_goals > 0:
        summed_percentage = (summed_period_values / total_goals) * 100
    else:
        summed_percentage = 0

    summed_bar_x = bars[5].get_x()  # Положение суммарного бара в x
    plt.text(
        summed_bar_x + 2.5,  # Смещение для корректного позиционирования текста
        summed_period_values,
        f'{summed_percentage:.1f}%',
        ha='center',
        va='bottom',
        color='black'
    )

    # Настройки осей и заголовок
    plt.xlabel('Time  periods')
    plt.ylabel('Number of goals')
    plt.title('At least 1 goal scored in periods in %')

    # Сохранение графика в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Конвертация изображения в base64
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return img_base64


def check_goals(goals, team, since, till, goals_h2):
    list_1 = []
    list_2 = []
    for i, j in enumerate(goals):
        if not j:
            continue
        if since <= j[0] <= till:
            list_1.append(1)
            list_2.append(goals_h2[i])
    return list_1, list_2

# Обработка команд и времени
def analyze_teams(home_goals, away_goals, goals_h2, since1, till1, team1, since2, till2, team2):
    list_1, list_2 = [], []

    if team1 == 'team1' and not team2:
        list_1, list_2 = check_goals(home_goals, team1, since1, till1, goals_h2)
    elif team1 == 'team2' and not team2:
        list_1, list_2 = check_goals(away_goals, team1, since1, till1, goals_h2)
    elif team1 == 'team1' and team2 == 'team1':
        for i, j in enumerate(home_goals):
            if len(j) < 2:
                continue
            if since1 <= j[0] <= till1 and since2 <= j[1] <= till2:
                list_1.append(2)
                list_2.append(goals_h2[i])
    elif team1 == 'team1' and team2 == 'team2':
        for i, j in enumerate(home_goals):
            if not j or not away_goals[i]:
                continue
            if since1 <= j[0] <= till1 and since2 <= away_goals[i][0] <= till2:
                list_1.append(2)
                list_2.append(goals_h2[i])
    elif team1 == 'team2' and team2 == 'team1':
        for i, j in enumerate(away_goals):
            if not j or not home_goals[i]:
                continue
            if since1 <= j[0] <= till1 and since2 <= home_goals[i][0] <= till2:
                list_1.append(2)
                list_2.append(goals_h2[i])
    elif team1 == 'team2' and team2 == 'team2':
        for i, j in enumerate(away_goals):
            if len(j) < 2:
                continue
            if since1 <= j[0] <= till1 and since2 <= j[1] <= till2:
                list_1.append(2)
                list_2.append(goals_h2[i])

    return list_1, list_2

# Подсчет дополнительных голов
def count_extra_goals(list_1, list_2):
    one_more_goal = 0
    no_more_goals = 0

    for i, j in enumerate(list_2):
        if (len(j) > 1 and list_1[i] == 1) or (len(j) > 2 and list_1[i] == 2):
            one_more_goal += 1
        else:
            no_more_goals += 1

    return one_more_goal, no_more_goals

# Построение круговой диаграммы
def plot_pie_chart(one_more_goal, no_more_goals):
    total = one_more_goal + no_more_goals
    labels = ['+ Goal', 'No Goal']
    sizes = [one_more_goal, no_more_goals]
    colors = ['#4CAF50', '#F44336']
    explode = (0.1, 0)  # Выделим кусок диаграммы для '+ Goal'

    # Создание фигуры и осей
    fig, ax = plt.subplots()

    # Построение круговой диаграммы
    try:
        ax.pie(sizes, explode=explode, labels=labels, colors=colors,
           autopct='%1.0f%%', shadow=False, startangle=90)
    except:
        return None
    # Добавление круга в центре диаграммы (для пончикового вида)
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)

    # Форматируем текст для отображения по центру диаграммы
    text_center = (f'+ Goal:\n{one_more_goal} / {total}\n'
                   f'No Goal:\n{no_more_goals} / {total}')

    # Отображение текста по центру диаграммы
    ax.text(0, 0, text_center, ha='center', va='center', fontsize=12, fontweight='bold')

    ax.axis('equal')  # Круг сохраняет форму круга

    # Сохранение графика в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    # Конвертация изображения в base64
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return img_base64

# Основная функция для анализа данных и возвращения графика
def one_more_goal(goals_h2, home_goals_h2, away_goals_h2, since1, till1, team1, since2, till2, team2):
    if team1:
        list_1, list_2 = analyze_teams(home_goals_h2, away_goals_h2, goals_h2, since1, till1, team1, since2, till2, team2)
        one_more_goal, no_more_goals = count_extra_goals(list_1, list_2)

        print(f"Список голов по матчам: {list_1}")
        print(f"Голы за матчи: {list_2}")
        print(f"Еще один гол: {one_more_goal}")
        print(f"Больше голов не было: {no_more_goals}")

        # Получение графика в формате base64
        pie_chart_base64 = plot_pie_chart(one_more_goal, no_more_goals)
        return pie_chart_base64
    else:
        print("Нет данных для анализа.")
        return None