from upstream_viz_lib import config
import pandas as pd
from os import path
from typing import Tuple, Union
from upstream_viz_lib.common import otp
from upstream_viz_lib.config import get_data_folder
import numpy as np

from ksolver.io.calculate_DF import calculate_DF
from upstream.well.single_well import SingleWell
from upstream.well.single_well import get_schedule_dataframe


data_folder = config.get_data_folder()

QUERY_WELL_DAILY_PARAMS = f"""
| __SOURCE__
| latestrow _time=day engine=window by __deposit, __well_num
"""

def get_pump_curves_and_pump_model_list() -> Tuple[pd.DataFrame, list]:
    """
    _INSIDE_ app
    """
    pump_curves = pd.read_csv(path.join(data_folder, "PumpChart.csv")).set_index(
        "pumpModel"
    )
    pump_model_list = list(set(pump_curves.index))
    return pump_curves, pump_model_list


def get_what_if_data(well_num: str) -> pd.DataFrame:
    """
    _INSIDE_ app
    """
    query = otp.render_query(
        QUERY_WELL_DAILY_PARAMS,
        {"__SOURCE__": config.get_conf("get_data.yaml")["well"]["whatif"]},
    )
    df_well_params = otp.get_data(query)
    df_well_params = df_well_params[df_well_params["__well_num"] == well_num]
    return df_well_params


def get_init_and_calculated_params(params_dict: dict,
                                   dataset: pd.DataFrame
                                   ):
    """
    _INSIDE_ app
    """

    df = pd.DataFrame(dataset, index=[0])

    mdf = calculate_DF(df, data_folder)
    Q = mdf.iloc[-1]
    Q = Q["X_kg_sec"] * 86400 / Q["res_liquid_density_kg_m3"]
    init_params = []
    for field in ["adku_debit", "p_plast", "p_zaboy", "p_input", "p_output", "p_head"]:
        value = params_dict.get(field)
        if value:
            rounded_value = round(value) if not np.isnan(value) else value
            init_params.append(str(rounded_value))
        else:
            init_params.append("-")

    calculated_params = [round(Q)] + [round(p) for p in mdf["startP"].values]
    result_dict = {
        "Параметр": [
            "Дебит",
            "Пластовое",
            "Забойное",
            "На приеме",
            "На выкиде",
            "Устьевое",
        ],
        "Исходные": init_params,
        "Расчетные": calculated_params,
    }
    return result_dict


def calculate_single_well_schedule(solver_df: pd.DataFrame, mode: dict, oil_params: dict) -> pd.DataFrame:
    """
    _INSIDE_ app
    """
    oil_params = {param: float(value) for param, value in oil_params.items()}
    schedule = get_schedule_dataframe(mode)
    single_well = SingleWell(solver_df, schedule, oil_params, "INFO", data_folder=get_data_folder())
    results = single_well.calc_schedule().reset_index()
    return results
