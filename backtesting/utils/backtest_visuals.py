# backtest_visuals.py
import pandas as pd
import plots
import animations
from matplotlib.backends.backend_pdf import PdfPages


def main():
    file_path = '../data/results/TWC/TWC_v1_cycle_2018-2023.csv'
    df = pd.read_csv(file_path, parse_dates=['timestamp'], dayfirst=True)

    # Ignore rows with returns of 0
    df = df[df['returns'] != 0]

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    with PdfPages('../data/results/TWC/TWC_v1_cycle_2018-2023_plots.pdf') as pdf_pages:
        plot_functions = [plots.cumulative_returns_per_trade,
                          plots.trade_direction_accuracy,
                          plots.monthly_cumulative_returns,
                          plots.win_loss_pie_chart,
                          plots.win_loss_ratio,
                          plots.drawdown_lengths,
                          plots.win_loss_heatmap,
                          # plots.cumulative_wins_3d,
                          #plots.box_plots_by_month,
                          #plots.win_loss_scatter_plot,
                          plots.density_plots]

        for plot_function in plot_functions:
            plot_function(df, pdf_pages)

    animate_functions = [animations.win_loss_ratio_animation,
                         #animations.win_loss_scatter_plot_animation,
                         animations.cum_returns_per_trade_animation]

    for animate_function in animate_functions:
        animate_function(df)


if __name__ == '__main__':
    main()
