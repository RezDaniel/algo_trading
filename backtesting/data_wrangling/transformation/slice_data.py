import pandas as pd


def slice_data(input_csv, output_csv, startdate=None, enddate=None):
    """
    Load a CSV file into a DataFrame and slice it based on a specified start
    and end date.

    Example:
        set_start_end_date('data.csv', '2023-01-01 00:00:00',
        '2023-01-31 23:59:59')
    """
    # Load csv to df and convert 'timestamp' column to datetime
    df = pd.read_csv(input_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Set 'timestamp' as the DataFrame index
    df.set_index('timestamp', inplace=True)

    # Define the start and end timestamps if provided
    if startdate:
        start_timestamp = pd.to_datetime(startdate)
        df = df.loc[start_timestamp:]

    if enddate:
        end_timestamp = pd.to_datetime(enddate)
        df = df.loc[:end_timestamp]

    # # Index=False to avoid saving index as a separate column in csv file
    df.to_csv(output_csv, index=True)


def main():
    input_csv = '../../data/clean_data/cleaned_btc.csv'
    start_date = '14/08/2018 00:00'
    end_date = '31/12/2023 23:59'
    output_csv = '../../data/test_data/RipVanWinkle/cleaned_btc_ready_for_resampling.csv'

    slice_data(input_csv, output_csv, start_date, end_date)


if __name__ == "__main__":
    main()
