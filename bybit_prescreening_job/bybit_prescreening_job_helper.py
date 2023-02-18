import os
import shutil
from datetime import datetime, timedelta

import mplfinance as mpf
import pandas as pd
import requests


class BybitPrescreeningJobHelper:
    COUNT_CANDLES_ON_CHART_IN_REPORT = 150

    def __init__(self, config: dict):
        self.instruments_info_api_url = config["preScreeningJobHelper"]["instrumentsInfoApiUrl"]
        self.klines_api_url = config["preScreeningJobHelper"]["klinesApiUrl"]
        self.report_directory_path = "data/report/{}".format(datetime.now().strftime('%Y%m%d'))

    def prepare_folders(self, is_enable_complete_report: bool) -> None:

        if os.path.exists(self.report_directory_path):
            shutil.rmtree(self.report_directory_path)
        os.mkdir(self.report_directory_path)

        if is_enable_complete_report:
            os.mkdir(self.report_directory_path + "/ohlc")
            os.mkdir(self.report_directory_path + "/ohlc_ha")
            os.mkdir(self.report_directory_path + "/candle_stick_charts")
            os.mkdir(self.report_directory_path + "/heikin_ashi_charts")
            os.mkdir(self.report_directory_path + "/buyer_imbalances")
            os.mkdir(self.report_directory_path + "/seller_imbalances")

    def load_instruments_info(self, category: str, instrument_suffix: str) -> list:
        response = requests.get(self.instruments_info_api_url.format(category)).json()
        instruments_info = response["result"]["list"]
        instruments_info_filtered = [x for x in instruments_info if x["symbol"].endswith(instrument_suffix)]
        return instruments_info_filtered

    def get_ohlc(self, symbol: str, category: str, interval: str, start_date: datetime,
                 end_date: datetime) -> pd.DataFrame:
        start_date_timestamp = str(int(start_date.timestamp() * 1000))
        end_date_timestamp = str(int(end_date.timestamp() * 1000))
        url = self.klines_api_url.format(category, symbol, interval, start_date_timestamp,
                                         end_date_timestamp)
        response = requests.get(url).json()

        result = pd.DataFrame(response["result"]["list"],
                              columns=["date", "open", "high", "low", "close", "volume", "turnover"])
        if not result.empty:
            result["date"] = pd.to_datetime(result["date"], unit='ms')
            result["open"] = result["open"].astype("float")
            result["high"] = result["high"].astype("float")
            result["low"] = result["low"].astype("float")
            result["volume"] = result["volume"].astype("float")
            result["close"] = result["close"].astype("float")

        return result

    def get_three_months_4h_ohlc(self, symbol: str, category: str) -> pd.DataFrame:
        now = datetime.now()

        time_frame = "240"  # 240 minutes -> 4h
        days_offset = 30

        ohcl_part1 = self.get_ohlc(symbol, category, time_frame,
                                   now - timedelta(days=days_offset),
                                   now)
        ohcl_part2 = self.get_ohlc(symbol, category, time_frame,
                                   now - timedelta(days=days_offset * 2),
                                   now - timedelta(days=days_offset))
        ohcl_part3 = self.get_ohlc(symbol, category, time_frame,
                                   now - timedelta(days=days_offset * 3),
                                   now - timedelta(days=days_offset * 2))

        return pd.concat([ohcl_part1, ohcl_part2, ohcl_part3], axis=0).reset_index(drop=True)

    def get_ten_years_weekly_ohlc(self, symbol: str, category: str) -> pd.DataFrame:
        now = datetime.now()

        time_frame = "W"  # Weekly
        days_offset = 730  # Two years

        ohcl_part1 = self.get_ohlc(symbol, category, time_frame,
                                   now - timedelta(days=days_offset),
                                   now)
        ohcl_part2 = self.get_ohlc(symbol, category, time_frame,
                                   now - timedelta(days=days_offset * 2),
                                   now - timedelta(days=days_offset))
        ohcl_part3 = self.get_ohlc(symbol, category, time_frame,
                                   now - timedelta(days=days_offset * 3),
                                   now - timedelta(days=days_offset * 2))
        ohcl_part4 = self.get_ohlc(symbol, category, time_frame,
                                   now - timedelta(days=days_offset * 4),
                                   now - timedelta(days=days_offset * 3))
        ohcl_part5 = self.get_ohlc(symbol, category, time_frame,
                                   now - timedelta(days=days_offset * 5),
                                   now - timedelta(days=days_offset * 4))

        return pd.concat([ohcl_part1, ohcl_part2, ohcl_part3, ohcl_part4, ohcl_part5], axis=0).reset_index(drop=True)

    def create_candlestick_chart_and_save_to_file(self, ohlc: pd.DataFrame, file_path: str) -> None:
        df = ohlc[["date", "open", "high", "low", "close"]]

        # Convert date to matplotlib date format
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index("date")

        # df = df.sort_index(ascending=True)
        mpf.plot(df, type='candle', style='yahoo', savefig=file_path)

    def parse_last_price(self, ohlc: pd.DataFrame) -> float:
        return ohlc.tail(1)["close"].values[0]

    def find_fist_untested_imbalance(self, imbalances: pd.DataFrame, symbol: str, last_price: float,
                                     older_than_days: float) -> dict:
        if imbalances.empty:
            return None

        older_than_date = pd.to_datetime(datetime.now() - timedelta(days=older_than_days))
        filtered_imbalances = imbalances.loc[imbalances["date"] < older_than_date]
        first_untested_imbalance = filtered_imbalances.loc[filtered_imbalances["tested"] == False].tail(1)

        if first_untested_imbalance.empty:
            return None

        result = first_untested_imbalance.iloc[0].to_dict()
        result["symbol"] = symbol
        result["distance"] = round(1 - (result["price"] / last_price), 2)
        return result

    def write_complete_report(self, ohlc: pd.DataFrame, ohlc_ha: pd.DataFrame, buyer_imbalances: pd.DataFrame,
                              seller_imbalances: pd.DataFrame, symbol: str) -> None:
        ohlc.to_csv(self.report_directory_path + "/ohlc/{}.csv".format(symbol), index=False)
        ohlc_ha.to_csv(self.report_directory_path + "/ohlc_ha/{}.csv".format(symbol), index=False)
        self.create_candlestick_chart_and_save_to_file(ohlc.tail(self.COUNT_CANDLES_ON_CHART_IN_REPORT),
                                                       self.report_directory_path + "/candle_stick_charts/{}.png".format(
                                                           symbol))
        self.create_candlestick_chart_and_save_to_file(ohlc_ha.tail(self.COUNT_CANDLES_ON_CHART_IN_REPORT),
                                                       self.report_directory_path + "/heikin_ashi_charts/{}.png".format(
                                                           symbol))
        buyer_imbalances.to_csv(self.report_directory_path + "/buyer_imbalances/{}.csv".format(symbol),
                                index=False)
        seller_imbalances.to_csv(self.report_directory_path + "/seller_imbalances/{}.csv".format(symbol),
                                 index=False)

    def write_report(self, first_untested_buyer_imbalances: list,
                     first_untested_seller_imbalances: list) -> None:
        if len(first_untested_buyer_imbalances) > 0:
            first_untested_buyer_imbalances_df = pd.DataFrame(first_untested_buyer_imbalances).sort_values(
                "distance")
            first_untested_buyer_imbalances_df = first_untested_buyer_imbalances_df[
                ["symbol", "distance", "price", "date"]]
            first_untested_buyer_imbalances_df.to_csv(
                self.report_directory_path + "/first_untested_buyer_imbalances.csv", index=False)

            self.format_untested_imbalances_to_tw_text_file(first_untested_buyer_imbalances)
            buyer_imb_tw = self.format_untested_imbalances_to_tw_text_file(first_untested_buyer_imbalances)
            with open(self.report_directory_path + "/first_untested_buyer_imbalances_for_tw.txt", "w") as f:
                f.write(buyer_imb_tw)

        if len(first_untested_seller_imbalances) > 0:
            first_untested_seller_imbalances_df = pd.DataFrame(first_untested_seller_imbalances).sort_values("distance",
                                                                                                             ascending=False)
            first_untested_seller_imbalances_df = first_untested_seller_imbalances_df[
                ["symbol", "distance", "price", "date"]]

            first_untested_seller_imbalances_df.to_csv(
                self.report_directory_path + "/first_untested_seller_imbalances.csv",
                index=False)

            self.format_untested_imbalances_to_tw_text_file(first_untested_seller_imbalances)
            seller_imb_tw = self.format_untested_imbalances_to_tw_text_file(first_untested_seller_imbalances)
            with open(self.report_directory_path + "/first_untested_seller_imbalances_for_tw.txt", "w") as f:
                f.write(seller_imb_tw)

    def format_untested_imbalances_to_tw_text_file(self, first_untested_imbalances: list) -> str:
        result = ""
        for imbalance in first_untested_imbalances:
            symbol_formatted = "BYBIT:{}.P,".format(imbalance["symbol"])
            result = result + symbol_formatted
        return result
