import matplotlib.pyplot as plt
import numpy as np


def plot_goals(goals_list, intervals, interval_70_to_end=(70, 95), title=''):
    """
    Plots the number of first goals scored by the home team, away team, or total goals in each interval.

    Parameters:
    goals_list (list of lists): List where each element is a list of goal times for a match.
    intervals (list of tuples): List of intervals (start, end) to count the first goals.
    interval_70_to_end (tuple): Specific interval (start, end) to count the first goals separately.
    title (str): Title of the plot.
    """

    # Initialize counters for first goals in each interval
    first_goals_per_interval = {interval: 0 for interval in intervals}
    first_goals_70_to_end = 0

    # Count first goals in each interval and specifically for 70-95 minutes
    for match in goals_list:
        if match:  # Check if there are goals in the match
            first_goal_time = min(match)  # Take the time of the first goal
            for interval in intervals:
                if interval[0] <= first_goal_time < interval[1]:
                    first_goals_per_interval[interval] += 1
                    break  # Count only the first goal and exit the loop
            # Check for interval 70-95 minutes
            if first_goal_time >= interval_70_to_end[0]:
                first_goals_70_to_end += 1

    # Total number of matches
    total_matches = len(goals_list)

    # Calculate the percentage of matches with the first goal in each interval
    first_goals_percentage = [count / total_matches * 100 for count in first_goals_per_interval.values()]
    first_goals_70_to_end_percentage = first_goals_70_to_end / total_matches * 100

    # Plotting
    fig, ax1 = plt.subplots()

    # Plot the number of goals per interval
    bar_container = ax1.bar([f'{interval[0]}-{interval[1]}' for interval in intervals],
                            first_goals_per_interval.values(), color='skyblue', label='Первый гол')
    ax1.set_xlabel('Интервал минут')
    ax1.set_ylabel('Количество первых голов')
    ax1.set_title(title)

    # Add a bar for the interval 70-95 minutes
    bar_70_to_end = ax1.bar('70-95', first_goals_70_to_end, color='orange', label='70-95 минут')

    # Add percentages above the bars
    for i, bar in enumerate(bar_container):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, height, f'{first_goals_percentage[i]:.1f}%', ha='center',
                 va='bottom')

    # Add percentage above the 70-95 minutes bar
    height_70_to_end = bar_70_to_end[0].get_height()
    ax1.text(bar_70_to_end[0].get_x() + bar_70_to_end[0].get_width() / 2, height_70_to_end,
             f'{first_goals_70_to_end_percentage:.1f}%', ha='center', va='bottom')

    # Show the plot
    fig.tight_layout()
    plt.show()
    plt.get


# Define intervals
intervals = [(45, 50), (50, 55), (55, 60), (60, 65), (65, 70), (70, 75), (75, 80), (80, 85), (85, 90), (90, 95)]

# Example data
home_goals_h2 = [[], [87], [], [76], [], [92], [46, 64], [], [], [], [], [67, 86], [79], [70], [], [55], [72], [],
                 [69, 82], [59, 73], [], [75], [], [], [], [], [58, 92], [], [], [55, 71], [], [], [52, 94],
                 [55, 66, 75, 84], [66]]
away_goals_h2 = [[], [49, 95, 98], [94], [], [48, 70], [], [86], [83], [86], [93], [93], [62], [69, 91], [88], [59, 85],
                 [51, 74], [], [], [], [], [70], [], [], [], [83], [], [], [47, 72], [], [88], [56, 93], [], [], [],
                 [58]]
goals_h2 = [[], [87, 49, 95, 98], [94], [76], [48, 70], [92], [46, 64, 86], [83], [86], [93], [93], [67, 86, 62],
            [79, 69, 91], [70, 88], [59, 85], [55, 51, 74], [72], [], [69, 82], [59, 73], [70], [75], [], [], [83], [],
            [58, 92], [47, 72], [], [55, 71, 88], [56, 93], [], [52, 94], [55, 66, 75, 84], [66, 58]]

# Plot for home goals
plot_goals(home_goals_h2, intervals, title='Первый гол домашней команды во втором тайме')

# Plot for away goals
plot_goals(away_goals_h2, intervals, title='Первый гол гостевой команды во втором тайме')

# Plot for total goals
plot_goals(goals_h2, intervals, title='Первый гол в матчах во втором тайме')




