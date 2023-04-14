from typing import Optional, Tuple
from pathlib import Path

import upstream_viz_lib.config
import pandas as pd
from upstream_viz_lib.common import otp, styler
from datetime import date, timedelta

from .query_templates import QUERY_METRICS, WELL_STATES, PUMP_PROPS, DATA_QUERY

get_data_conf = upstream_viz_lib.config.get_data_conf()

METRICS_LIST_PATH = str(Path(__file__).parent.parent.parent.parent.resolve() / 'data' / 'well_metrics_list.csv')


def get_metrics_dict(deposit: str, date_range: Optional[Tuple[date, date]] = None, overwrite=False):
    def get_metrics_df():
        if not overwrite:
            return pd.read_csv(METRICS_LIST_PATH)

        source = get_data_conf["well"]["params"]
        filled_date_range = date_range or [
            date.today() - timedelta(days=2),
            date.today() + timedelta(days=1),
        ]

        tws, twf = [int(d.strftime("%s")) for d in filled_date_range]
        query = otp.render_query(
            QUERY_METRICS,
            {"__SOURCE__": source}
        )
        df = otp.get_data(query, tws, twf)
        df.to_csv(METRICS_LIST_PATH, index=False)
        return df

    metrics_dict = {}
    mdf = get_metrics_df().query(f"""__deposit == "{deposit}" """)
    for record in mdf.to_dict(orient="records"):
        k, v = record["metric_name"], record["metric_long_name"]
        metrics_dict[k] = v
    return metrics_dict


def get_well_states(deposit: str) -> dict:
    query = otp.beta_render_query(
        WELL_STATES,
        {"SOURCE": get_data_conf["well"]["states"]}
    )
    df_well_states = otp.get_data(query)
    well_states = {}
    for row in df_well_states.query(f"""__deposit == "{deposit}" """).to_dict(orient="records"):
        well_num = row["__well_num"]
        well_type = row["well_performance_history"]
        well_state = row["well_condition"]
        well_states[well_num] = {"type": well_type, "state": well_state}
    return well_states


def filter_metrics_by_well_type(all_params: dict, well_type: str = 'missed') -> dict:
    """
    pages/common/well_params/well_params_viz.py 69
    Filter all_params dict for well_type
    Args:
        well_type (str): One of "Водозаборные", "Нагнетательные", "Нефтяные"
        all_params (dict): all_params dictionary
    Returns:
        dict: dictionary with metrics for well_type
    """

    def metrics_for_oil_wells(metric_name):
        return (metric_name.startswith("adkuWell") & ~metric_name.startswith("adkuWell_nag")) \
               | metric_name.startswith("adkuControlStation") \
               | metric_name.startswith("neftWellop")

    def metrics_for_nag_wells(metric_name):
        return metric_name.startswith("adkuWell_nag") | metric_name.startswith("nag")

    def metrics_for_water_wells(metric_name):
        return metric_name.startswith("water")

    def metrics_default(metric_name):
        return metric_name is not None

    filter_func_selector = {
        "Нефтяные": metrics_for_oil_wells,
        "Нагнетательные": metrics_for_nag_wells,
        "Водозаборные": metrics_for_water_wells
    }

    filter_func = filter_func_selector.get(well_type, metrics_default)
    current_params = {k: v for k, v in all_params.items() if filter_func(k)}
    return current_params


def rename_pump_df(pump_df):
    """
    pages/common/well_params/well_params_viz.py 202
    """
    cols_renamer = {
        "pump_model": "Модель насоса",
        "pump_depth": "Глубина спуска",
        "perf_depth": "Глубина перфорации",
    }

    return pump_df[cols_renamer.keys()].rename(cols_renamer, axis=1)


def build_chart_query(agg_query: str, precision: int, r: bool, captions: bool):
    """
    pages/common/well_params/well_params_viz.py 222
    Render query for chart
    """
    round_eval = (
        f""" eval value = round(value, {precision}) """
        if r else "___ -- No round, keep initial precision"
    )

    anomalies = (
        """ eventstats mean(value) as m, stdev(value) as s by metric_long_name
        | eval upper = m + 2*s, lower = m - 2*s
        | eval _caption = if(value>upper OR value<lower, 1, 0)"""
        if captions else "___ -- No anomalies detection"
    )

    return f"""
    | {DATA_QUERY}   
    | {agg_query}
    | {anomalies}
    | {round_eval}
    """

