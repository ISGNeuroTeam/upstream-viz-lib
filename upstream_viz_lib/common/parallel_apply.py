import logging
from multiprocessing import Pool
from functools import partial
import numpy as np
import pandas as pd


def parallelize(data, func, num_of_processes=16):
    logging.info(f"Start parallelize ({num_of_processes})...")
    data_split = np.array_split(data, num_of_processes)
    pool = Pool(num_of_processes)
    logging.info("Pool created...")
    data = pd.concat(pool.map(func, data_split))
    logging.info("Data concatenated...")
    pool.close()
    pool.join()
    logging.info("Pool closed and joined")
    return data


def run_on_subset(func, data_subset):
    return data_subset.apply(func, axis=1)


def parallelize_on_rows(data, func, num_of_processes=16):
    print("started parallelize_on_rows")
    return parallelize(data, partial(run_on_subset, func), num_of_processes)
