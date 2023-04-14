import pandas as pd


def get_all_deposits(metric_df: pd.DataFrame) -> list:
    """
    _INSIDE_ render_data_filters
    :param metric_df:
    :return:
    """
    return list(map(lambda address: address.split(sep=' м/р')[0], metric_df["address"]))
