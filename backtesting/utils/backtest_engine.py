# backtest_engine.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from datamanager import DataManager
from logger import MyLogger

# instance of MyLogger, add False as last param to disable.
log = MyLogger('data/results/logfile.log', "backtest_engine.py", False)


class BackTestSA:

    """
    backtesting class for all single asset strategies,
    columns must include the following :
    close: float
    timestamp: date
    """

    def __init__(self, csv_path, date_col):

        self.dmgt = DataManager(csv_path, date_col)

        # trade variables
        self.current_df = pd.DataFrame()
        self.entry_count = 0  # count number of times sig executed
        self.trade_count = 0  # count how many times signal has been taken
        self.open_pos = False
        self.timestamp = None
        self.entry_price = 0
        self.direction = 0
        self.target_price = 0
        self.stop_price = 0

        # target multipliers
        self.long_mult = 1.04
        self.short_mult = 0.96

        self.returns_series = []
        self.holding_series = []
        self.direction_series = []

    def open_long(self, price):
        """

        :param price: price we open long at
        :return: populates trade variables from constructor with relevant
        variables
        """
        self.open_pos = True
        self.direction = 1
        self.entry_price = price
        self.trade_count += 1
        self.entry_count += 1
        self.add_zeros()

        # log.logger.info(
        #     #str(self.trade_count)
        #     #+ " entry_count-" + str(int(self.entry_count))
        #     str(self.timestamp)
        #     + " long : " + str(int(self.entry_price))
        #     + " tp : " + str((int(self.target_price)))
        #     + " sl: " + str(int(self.stop_price)))

    def open_short(self, price):
        """

        :param price: price we open short at
        :return: populates trade variables from constructor with relevant
        variables
        """
        self.open_pos = True
        self.direction = -1
        self.entry_price = price
        self.trade_count += 1
        self.entry_count += 1
        self.add_zeros()

        # log.logger.info(
        #     str(self.timestamp)
        #     + " short: " + str(int(self.entry_price))
        #     + " tp : " + str(int(self.target_price))
        #     + " sl: " + str(int(self.stop_price)))

    def reverse_position(self, price, cur_pos_dir):
        """

        :param price: price we open position at
        :cur_pos_dir: direction of current position being closed and reversed
        :return: populates trade variables from constructor with relevant
        variables
        """
        self.open_pos = True
        self.entry_price = price
        self.trade_count += 1
        self.entry_count += 1

        if cur_pos_dir == 1:
            self.direction = -1
        else:
            self.direction = 1

        # log.logger.info(
        #     str(self.timestamp)
        #     + " dir: " + str(int(self.direction))
        #     + " entry: " + str(int(self.entry_price))
        #     + " tp : " + str(int(self.target_price))
        #     + " sl: " + str(int(self.stop_price)))

    def reset_variables(self):
        """
        resets the variables after we close a trade
        """
        self.open_pos = False
        self.timestamp = None
        self.entry_price = 0
        self.direction = 0
        self.target_price = 0
        self.stop_price = 0

    def add_zeros(self):
        self.returns_series.append(0)
        self.holding_series.append(0)
        self.direction_series.append(0)

    def close_position(self, price):
        """

        :param price: price we are exiting trade at
        :return: appends the trade pnl to the returns series
        and resets variables
        """
        pnl = (price / self.entry_price - 1) * self.direction
        self.process_close_var(pnl)

        # log.logger.info(
        #     str(self.timestamp)
        #     + " close: " + str((int(price)))
        #     + " pips: "
        #     + str((int(self.entry_price - price) * self.direction) * - 1)
        #     + " pnl: " + str("{:.1f}%".format(pnl * 100))
        #     + "\n")

        self.reset_variables()

    def process_close_var(self, pnl):
        self.returns_series.append(pnl)
        self.direction_series.append(self.direction)

    def generate_signals(self):
        """

        use this function to make sure generate signals has been included in the child class
        """
        if 'entry' not in self.dmgt.df.columns:
            raise Exception('You have not created signals yet')

    def monitor_open_positions(self, price, timestamp):
        # check if target breached for long positions
        if price >= self.target_price and self.direction == 1:
            self.timestamp = timestamp
            self.close_position(price)
        # check if stop-loss breached for long positions
        elif price <= self.stop_price and self.direction == 1:
            self.timestamp = timestamp
            self.close_position(price)
        # check if target breached for short positions
        elif price <= self.target_price and self.direction == -1:
            self.timestamp = timestamp
            self.close_position(price)
        # check if stop-loss breached for short positions
        elif price >= self.stop_price and self.direction == -1:
            self.timestamp = timestamp
            self.close_position(price)

        # if all above conditions not true, append a zero to returns column
        else:
            self.add_zeros()

    def add_trade_cols(self):
        """
        merges the new columns we created for our backtest into our dataframe,
        also resets the returns series to empty lists, incase we want to change
        the strategy heartbeat.
        """
        self.dmgt.df['returns'] = self.returns_series
        self.dmgt.df['direction'] = self.direction_series

        self.returns_series = []
        self.direction_series = []

    def run_backtest(self):
        # signals generated from child class
        self.generate_signals()

        # loop over dataframe
        for row in self.dmgt.df.itertuples():
            # if we get a long signal and do not have open position open a long
            if row.entry == 1 and self.open_pos is False:
                self.open_long(row.t_plus)
            # if we short signal and do not have open position open a sort
            elif row.entry == -1 and self.open_pos is False:
                self.open_short(row.t_plus)
            # monitor open positions to see if any of the barriers have been
            # touched, see function above
            elif self.open_pos:
                self.monitor_open_positions(row.close, row.Index)
            else:
                self.add_zeros()

        self.add_trade_cols()

    def show_performace(self):
        plt.style.use('ggplot')
        self.dmgt.df.returns.cumsum().plot()
        plt.title(f"Strategy results for {self.dmgt.timeframe} timeframe")
        plt.show()

    def save_backtest(self, instrument):
        """

        :param instrument: ETH, BTC for Ethereum and Bitcoin
        saves backtest to our backtests folder
        """
        strat_name = self.__class__.__name__
        tf = self.dmgt.timeframe
        self.dmgt.df.to_csv(
            #f"../data/results/{strat_name}_{tf}-{instrument}.csv")
            f"../data/results/{strat_name}_{instrument}.csv")



