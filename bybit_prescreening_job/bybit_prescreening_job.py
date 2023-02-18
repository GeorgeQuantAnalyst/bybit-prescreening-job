import logging

from bybit_prescreening_job.bybit_prescreening_job_helper import BybitPrescreeningJobHelper
from bybit_prescreening_job.heikin_ashi import HA
from bybit_prescreening_job.imbalance_finder import ImbalanceFinder


class BybitPrescreeningJob:

    def __init__(self, config: dict) -> None:
        self.config = config
        self.is_active_complete_report = config["preScreeningJob"]["typeOfReport"] == "complete"
        self.type = config["preScreeningJob"]["type"]
        self.helper = BybitPrescreeningJobHelper(config)
        self.imbalance_finder = ImbalanceFinder(config)

    def run(self) -> None:
        logging.info("Start job")

        self.helper.prepare_folders(self.is_active_complete_report)
        instruments_info = self.helper.load_instruments_info(self.config["preScreeningJob"]["instrumentsCategory"],
                                                             self.config["preScreeningJob"]["instrumentsSuffix"])
        logging.info("Loaded {} instruments".format(len(instruments_info)))

        first_untested_buyer_imbalances = []
        first_untested_seller_imbalances = []

        for instrument_info in instruments_info:
            symbol = instrument_info["symbol"]
            try:
                logging.info("Process market: {}".format(symbol))

                if self.type == "swing":
                    ohlc = self.helper.get_three_months_4h_ohlc(symbol,
                                                                self.config["preScreeningJob"]["instrumentsCategory"])
                else:
                    ohlc = self.helper.get_ten_years_weekly_ohlc(symbol,
                                                                 self.config["preScreeningJob"]["instrumentsCategory"])
                ohlc = ohlc[::-1]
                ohlc.index = (range(ohlc.shape[0]))

                ohlc_ha = HA(ohlc)

                last_price = self.helper.parse_last_price(ohlc)

                buyer_imbalances = self.imbalance_finder.find_buyer_imbalances(ohlc_ha)
                seller_imbalances = self.imbalance_finder.find_selling_imbalances(ohlc_ha)

                first_untested_buyer_imbalance = self.helper.find_fist_untested_imbalance(buyer_imbalances, symbol,
                                                                                          last_price, self.config[
                                                                                              "preScreeningJob"][
                                                                                              "imbOlderThanDays"])
                first_untested_seller_imbalance = self.helper.find_fist_untested_imbalance(seller_imbalances, symbol,
                                                                                           last_price, self.config[
                                                                                               "preScreeningJob"][
                                                                                               "imbOlderThanDays"])

                if first_untested_buyer_imbalance is not None:
                    first_untested_buyer_imbalances.append(first_untested_buyer_imbalance)

                if first_untested_seller_imbalance is not None:
                    first_untested_seller_imbalances.append(first_untested_seller_imbalance)

                if self.is_active_complete_report:
                    self.helper.write_complete_report(ohlc, ohlc_ha, buyer_imbalances, seller_imbalances, symbol)
            except:
                logging.exception("Error in processing symbol - {}: ".format(symbol))

            self.helper.write_report(first_untested_buyer_imbalances, first_untested_seller_imbalances)

        logging.info("Finished job")
