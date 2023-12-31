# features_creation.py
import pandas as pd
import datetime as dt


class DataManager:

    def __init__(self, csv_path, date_col):

        self.data = pd.read_csv(csv_path, parse_dates=[date_col],
                                date_parser=lambda x: dt.datetime.strptime(x,
                                                                           '%d/%m/%Y'),
                                index_col=date_col)

        # can use uniform to change this
        self.data['t_plus'] = self.data.open.shift(-1)

        self.data.dropna(inplace=True)

        self.df = self.data.copy()
        self.timeframe = '1min'

    def change_resolution(self, new_timeframe):

        resample_dict = {'volume': 'sum', 'open': 'first',
                         'low': 'min', 'high': 'max',
                         'close': 'last',
                         't_plus': 'last'}

        self.df = self.data.resample(new_timeframe).agg(resample_dict)
        self.timeframe = new_timeframe

        return self.df

    def update_sigtime_column(self, output_csv, check_both=False):
        """
        Update the 'sigtime' column based on the conditions specified.

        :param output_csv: the path for the output.csv file.
        :param check_both: Whether to check both 'time_newyork' and
        'time_london' columns, defaults to False.
        """
        if check_both:
            time_columns = ['time_newyork', 'time_london']
        else:
            time_columns = ['time_germany']  # can change time_zone here

        for time_column in time_columns:
            # Check if the specified time_column exists in the DataFrame
            if time_column not in self.df.columns:
                raise ValueError(
                    f"Column '{time_column}' does not exist in the "
                    f"DataFrame.")

            # Convert the time_column to datetime objects remove seconds and ms
            self.df[time_column] = \
                pd.to_datetime(self.df[time_column]).dt.floor('T')

        # function to set the value of 'sigtime' based on the conditions
        def set_sigtime(row):
            if check_both:
                if row['time_newyork'].hour == 9 and \
                        row['time_newyork'].minute == 30:
                    return 1
                elif row['time_london'].hour == 8 and \
                        row['time_london'].minute == 0:
                    return 1
            else:
                if row['time_germany'].hour == 9 and \
                        row['time_germany'].minute == 20:
                    return 1

            return 0

        # Apply the function to each row to update 'sigtime' column
        self.df['sigtime'] = self.df.apply(set_sigtime, axis=1)

        # Save the updated DataFrame back to the CSV file
        self.df.to_csv(output_csv,
                       date_format='%m/%d/%Y %H:%M', index=True)

    def generate_orders(self, lookback, buffer, filename):
        """
        Generates buy/sell orders at the break of the high/low of a previous-
        bar, designated in time by using set_sigtime() and a lookback period.
        """
        self.df['sig_long'] = self.df['high'].rolling(lookback).max()
        self.df['sig_short'] = self.df['low'].rolling(lookback).min()

        long_ord_price, short_ord_price = 0, 0
        long_sig_flag, short_sig_flag = 0, 0

        for row in self.df.itertuples():
            if row.sigtime == 0 and short_sig_flag == long_sig_flag == 0:
                self.df.at[row.Index, 'long_ord'] = 0
                self.df.at[row.Index, 'short_ord'] = 0
            elif row.sigtime == 1:
                long_ord_price, short_ord_price = row.sig_long + buffer, \
                                                  row.sig_short - buffer
                self.df.at[row.Index, 'long_ord'] = long_ord_price
                self.df.at[row.Index, 'short_ord'] = short_ord_price
                long_sig_flag = short_sig_flag = 1
            elif row.sigtime == 0 and (short_sig_flag or long_sig_flag):
                self.df.at[row.Index, 'long_ord'] = long_ord_price
                self.df.at[row.Index, 'short_ord'] = short_ord_price

        # Drop the 'sig_long' and 'sig_short' columns, as they are no longer
        # needed
        self.df.drop(columns=['sig_long', 'sig_short'], inplace=True)

        # Save the updated DataFrame to a CSV file
        self.df.to_csv(filename)
