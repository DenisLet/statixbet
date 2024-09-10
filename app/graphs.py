import matplotlib

matplotlib.use('Agg')  # Устанавливаем backend для работы без GUI
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.ticker import MaxNLocator


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
                if interval[0] <= first_goal_time < interval[1]:
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
        label='Первый гол'  # Изящный зеленый цвет
    )

    bar_70_to_end = ax1.bar(
        '70+',
        first_goals_70_to_end,
        color='#9C27B0',
        label='70-95 минут'  # Элегантный фиолетовый
    )

    # Увеличение шрифта для меток осей, заголовка и текста на графике
    ax1.set_xlabel('Timing (minutes)', fontsize=25)
    ax1.set_ylabel('Number of 1st goals in 2nd half', fontsize=25)
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

def filter_goals(goals_list):
    nogoal_before70_list = []
    for i in goals_list:
        try:
            i.sort()
            if len(i) == 0:
                nogoal_before70_list.append([])
            elif i[0] > 70:
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

