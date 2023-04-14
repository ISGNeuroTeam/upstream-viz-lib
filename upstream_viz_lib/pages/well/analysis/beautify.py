import numpy as np

from pandas import DataFrame
from upstream_viz_lib.config import RED_COLOR


def is_different_modes(df):
    return df["predict_mode_str"] != df["shtr_mode"]


def beautify_nans(df: DataFrame) -> DataFrame:
    return df.fillna("-").replace("na", "Не определено")


def remove_times_for_const_wells(df: DataFrame) -> DataFrame:
    if ("times" not in df.columns) or ("state" not in df.columns):
        return df
    df.loc[df["state"] == "const", "times"] = "24 ч."
    return df


#  TODO add highlight different periods
def is_different_periods(df):
    return (0.9 <= df["work_time_shtr"] / df["work_time_calculated"] <= 1.1) & (
        0.9 <= df["stop_time_shtr"] / df["stop_time_calculated"] <= 1.1
    )


def highlight_mode_diffs(df):
    color = RED_COLOR
    is_different_regimes = df["Расчетный режим"] != df["Режим ШТР"]
    df_background = DataFrame(
        "background-color: ", index=df.index, columns=df.columns
    )

    for col in ["Расчетный режим", "Режим ШТР"]:
        df_background[col] = np.where(
            is_different_regimes, f"background: {color}", df_background[col]
        )
    return df_background
