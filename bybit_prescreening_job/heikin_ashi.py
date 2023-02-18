import logging

ROUND_PRECISION = 5


def HA(df):
    '''
    The function will take a dataframe and return the Heikin Ashi Price DataFrame
    The input dataframe should contain ['open', 'high', 'low', 'close'] columns
    For detailed implementation refer http://tradewithpython.com/constructing-heikin-ashi-candlesticks-using-python
    '''

    # convert all column headers to lowercase
    df.columns = df.columns.str.lower()

    try:
        new_df = df[['open', 'high', 'low', 'close', 'date']]

        HA_df = new_df.copy()

        # close column
        HA_df['close'] = round(((new_df['open'] + new_df['high'] + new_df['low'] + new_df['close']) / 4),
                               ROUND_PRECISION)

        # open column
        for i in range(len(new_df)):
            if i == 0:
                HA_df.iat[0, 0] = round(((new_df['open'].iloc[0] + new_df['close'].iloc[0]) / 2), ROUND_PRECISION)
            else:
                HA_df.iat[i, 0] = round(((HA_df.iat[i - 1, 0] + HA_df.iat[i - 1, 3]) / 2), ROUND_PRECISION)

        # High and Low column
        HA_df['high'] = HA_df.loc[:, ['open', 'close']].join(new_df['high']).max(axis=1)
        HA_df['low'] = HA_df.loc[:, ['open', 'close']].join(new_df['low']).min(axis=1)

        return HA_df

    except KeyError:
        logging.exception("The dataframe passed do not contain ['open', 'high', 'low', 'close'] columns")
