import logging.config

from bybit_prescreening_job.bybit_prescreening_job import BybitPrescreeningJob

from bybit_prescreening_job.constants import LOGGER_CONFIG_FILE_PATH, __logo__, CONFIG_FILE_PATH
from bybit_prescreening_job.utils import load_config

if __name__ == "__main__":
    logging.config.fileConfig(fname=LOGGER_CONFIG_FILE_PATH, disable_existing_loggers=False)
    logging.info(__logo__)

    try:
        config = load_config(CONFIG_FILE_PATH)
        job = BybitPrescreeningJob(config)
        job.run()
    except:
        logging.exception("Error in app: ")
