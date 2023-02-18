import pandas as pd


class ImbalanceFinder:
    COUNT_SKIP_CANDLES = 10

    def __init__(self, config: dict):
        self.count_skip_candles = config["imbalanceFinder"]["countSkipCandles"]

    def find_buyer_imbalances(self, ohlc: pd.DataFrame) -> pd.DataFrame:
        ohlc_copy = ohlc.copy()

        # Mark green candles
        ohlc_copy["green"] = ohlc_copy["open"].lt(ohlc_copy["close"])

        # Decide 3 days consecutive green candles
        ohlc_copy['next_3days_green'] = ohlc_copy[::-1].rolling(3)['green'].sum().eq(3)

        # Find buyer imbalances
        buyer_imbalances = self.__find_buyer_imbalances(ohlc_copy)

        return buyer_imbalances

    def find_selling_imbalances(self, ohlc: pd.DataFrame) -> pd.DataFrame:
        ohlc_copy = ohlc.copy()

        # Mark red candles
        ohlc_copy["red"] = ohlc_copy["open"].gt(ohlc_copy["close"])

        # Decide 3 days consecutive red candles
        ohlc_copy['next_3days_red'] = ohlc_copy[::-1].rolling(3)['red'].sum().eq(3)

        # Find seller imbalances
        seller_imbalances = self.__find_seller_imbalances(ohlc_copy)

        return seller_imbalances

    def __find_buyer_imbalances(self, ohlc_copy: pd.DataFrame) -> pd.DataFrame:
        previous_open_price = 0
        is_previous_candle_3days_green = False

        buyer_imbalances = []

        for index, row in ohlc_copy.iterrows():
            if row["next_3days_green"] is True and is_previous_candle_3days_green is False:
                start_imbalance = previous_open_price
                is_tested_imbalance = start_imbalance > ohlc_copy[(index + self.count_skip_candles):][
                    "low"].min()

                buyer_imbalances.append({
                    "date": row["date"],
                    "price": start_imbalance,
                    "tested": is_tested_imbalance
                })

            previous_open_price = row["open"]
            is_previous_candle_3days_green = row["next_3days_green"]

        return pd.DataFrame(buyer_imbalances)

    def __find_seller_imbalances(self, ohlc_copy: pd.DataFrame) -> pd.DataFrame:
        previous_open_price = 0
        is_previous_candle_3days_red = False

        seller_imbalances = []

        for index, row in ohlc_copy.iterrows():
            if row["next_3days_red"] is True and is_previous_candle_3days_red is False:
                start_imbalance = previous_open_price
                is_tested_imbalance = start_imbalance < ohlc_copy[(index + self.count_skip_candles):][
                    "high"].max()

                seller_imbalances.append({
                    "date": row["date"],
                    "price": start_imbalance,
                    "tested": is_tested_imbalance
                })

            previous_open_price = row["open"]
            is_previous_candle_3days_red = row["next_3days_red"]

        return pd.DataFrame(seller_imbalances)
