import pandas as pd
from typing import Optional

from upstream_viz_lib.common import otp
from upstream_viz_lib.pages.well.potentials.model_potentials import calculate_wells, calculation_event
from upstream_viz_lib.pages.well.potentials.static.command_format import QUERY_POTENTIALS
from upstream.potentials.Economics import Economics


def get_data_from_platform(water_limit, date) -> Optional[pd.DataFrame]:
    """
    _INSIDE_ app
    :param water_limit:
    :param date:
    :return: dataframe filtered by water_limit
    """
    query = otp.render_query(QUERY_POTENTIALS, {"$date$": date})
    data_from_platform = otp.get_data(query)

    if not data_from_platform.empty:
        data_from_platform = data_from_platform.query(f"water <= {water_limit}")
    return data_from_platform


def get_positive_p_input(data_from_platform: pd.DataFrame) -> pd.DataFrame:
    """
    _INSIDE_ app
    :param data_from_platform:
    :return: dataframe without unnecessary columns and record where p_input > 0
    """
    df = (
        data_from_platform.copy()
        .dropna(subset=["loading", "ure", "k_flow", "pump_model"])
        .query("p_input>0")
    )
    return df


def calculations_on_button_press(df: pd.DataFrame, criterions: dict, params: dict) -> pd.DataFrame:
    """
    _INSIDE_ app

    :param df: dataframe on which calculations are performed
    :param criterions: custom fields
    :param params: custom fields
    :return: calculated dataframe
    """
    df = calculate_wells(df, criterions, params)
    df = calculation_event(df)
    return df

def get_debit_and_fcf(df: pd.DataFrame, params, sum_debit, sum_oildebit, sum_power) -> pd.DataFrame:
    """
    _INSIDE_ draw_debit
    """

    fcf_before = df["FCF текущий"].sum()
    fcf_after = df["FCF_event"].sum()
    diff_debit = df["q_event"].sum() - df["Q"].sum()
    diff_oildebit = df["q_n_event"].sum() - df["oilWellopCountedOilDebit"].sum()
    fcf_full = Economics(
        q_zh_vol=sum_debit,
        ro_sm=0.931,
        q_n=sum_oildebit,
        specific_energy_mp=24 * sum_power / sum_debit,  # В процентах от 0 до 1
        **params,
    ).get_FCF()
    fcf_after_proportional = (fcf_after - fcf_before) + fcf_full
    debit_and_fcf = {
        'liquid_debit_before': sum_debit,
        'liquid_debit_after': sum_debit + diff_debit,
        'liquid_debit_delta': round(100 * diff_debit / sum_debit, 1),
        'oil_debit_before': sum_oildebit,
        'oil_debit_after': sum_oildebit + diff_oildebit,
        'oil_debit_delta': round(100 * diff_oildebit / sum_oildebit, 1),
        'fcf_before': fcf_full,
        'fcf_after': fcf_after_proportional,
        'fcf_delta': round(100 * (fcf_after_proportional - fcf_full) / fcf_full, 1)
    }
    return pd.DataFrame(debit_and_fcf, index=[0])
