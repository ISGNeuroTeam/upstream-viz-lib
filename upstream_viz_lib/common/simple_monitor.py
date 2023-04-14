from typing import Dict, Any

import pandas as pd
import os
from datetime import date, timedelta

from upstream_viz_lib.common import otp
from upstream_viz_lib.config import get_data_folder, get_conf

data_folder = get_data_folder()
data_config = get_conf()

date_today = date.today()
date_week_ago = date_today - timedelta(days=7)


def get_metrics_df(filename: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(data_folder, filename))


def get_aggregations(value_field: str) -> Dict[str, Any]:
    """
    _INSIDE_ render_sidebar
    """
    agg_query = f"""
          eval _time = 3600 * floor(_time / 3600) 
        | stats $func$({value_field}) as {value_field} by _time, metric_long_name
        """
    return {
        "Исходные значения": "___",
        "Среднее за час": agg_query.replace("$func$", "mean"),
        "Максимум за час": agg_query.replace("$func$", "max"),
        "Минимум за час": agg_query.replace("$func$", "min"),
    }


def get_data_according_to_metrics(data_options: Dict[str, Any], chart_options: Dict[str, Any]) -> pd.DataFrame:
    """
    _INSIDE_ app
    :return DataFrame that already has _time column if dt column exists
    """
    tws, twf = [int(d.strftime("%s")) for d in data_options["date_range"]]
    metric_str = " OR ".join(f"""metric_long_name="{m}" """ for m in data_options["metrics"])
    round_eval = (
        f""" eval metric_value = round(metric_value, {chart_options["precision"]}) """
        if chart_options["round"] else "___"
    )

    query = f"""
            | otstats index="ptk_zond" NameObject="{data_options["selected_object"]}"
            | rename NameObject as address, Value as metric_value, Description as metric_long_name, TagName as metric_name
            | search {metric_str}
            | {chart_options["agg_query"]}
            | eventstats mean(metric_value) as m, stdev(metric_value) as s by metric_long_name
            | eval upper = m + 2*s, lower = m - 2*s
            | eval _caption = if(metric_value>upper OR metric_value<lower, 1, 0)
            | {round_eval}
            | fields _time, metric_long_name, metric_value, _caption
            | rename metric_long_name as variable, metric_value as value
            """
    df = otp.get_data(query, tws=tws, twf=twf)
    if 'dt' in df.columns:
        df["_time"] = df["dt"]
    return df


def get_gas_data_according_to_metrics(data_options: Dict[str, Any], chart_options: Dict[str, Any]) -> pd.DataFrame:
    """
    _INSIDE_ app_gas
    :return DataFrame that already has _time column if dt column exists
    """
    date_start, date_end = data_options["date_range"]
    metric_str = " OR ".join(f"""metric_long_name="{m}" """ for m in data_options["metrics"])
    round_eval = (
        f""" eval value = round(value, {chart_options["precision"]}) """
        if chart_options["round"] else "___"
    )

    query = f"""
            | {data_config["gas"]["metrics"]}
            | where day>="{date_start}" AND day<"{date_end}"
            | where full_object_name="{data_options["selected_object"]}"
            | search {metric_str}
            | {chart_options["agg_query"]}
            | eventstats mean(value) as m, stdev(value) as s by metric_long_name
            | eval upper = m + 3*s, lower = m - 3*s
            | eval _caption = if(value>upper OR value<lower, 1, 0)
            | {round_eval}
            | fields _time, metric_long_name, value, _caption
            | rename metric_long_name as variable
            """
    df = otp.get_data(query)
    if 'dt' in df.columns:
        df["_time"] = df["dt"]
    return df
