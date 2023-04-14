import locale
import pandas as pd
from pandarallel import pandarallel
from upstream_viz_lib.common import otp
from upstream.potentials.Economics import Economics
from upstream.potentials.Optimizer import get_lambda_thresholds, optimize
from upstream_viz_lib.pages.well.potentials.static.command_format import *

MIN_INCREASE_QN = 3  # минимальный прирост Qн, при котором можно рекомендовать смену ЭЦН

num_allowed_cores = config.get_conf()["pandarallel"]["n_cores"]
pandarallel.initialize(nb_workers=num_allowed_cores)


def get_sums_debit_oildebit_power(date) -> tuple:
    """
    function that replaces get_debit, get_oildebit, getpower from models_potential

    _INSIDE_ app
    :param date:
    :return: tuple of 3 sums liquid_debit, oil_debit, power
    """
    # SUM_DEBIT == SUM_OILDEBIT == SUM_POWER so no need to run the same otl 3 times
    query_sum = otp.render_query(SUM_DEBIT, {"$date$": date})
    data = otp.get_data(query_sum)
    return data["liquid_debit"].values[0], data["oil_debit"].values[0], data["power"].values[0]


def calculate_wells(df, criterions, params):
    crits = get_lambda_thresholds(criterions)

    params_df = df.parallel_apply(lambda x: optimize(x, crits, False), axis=1)

    result_df = params_df[
        [
            "Q",
            "freq",
            "power_esp_optimal",
            "Рекомендуемый УЭЦН",
            "P_bottom_hole",
            "Loading",
        ]
    ].rename(
        {
            "Q": "Q_freq_optimal",
            "freq": "freq_optimal",
            "P_bottom_hole": "P_bottom_hole_freq_optimal",
            "Loading": "Loading_optimal",
        },
        axis=1,
    )
    df = df.join(result_df)
    df_with_economics = df.apply(lambda x: calculate_fcf(x, params), axis=1)
    df = df.join(df_with_economics)
    df = get_diff_columns(df)
    return df


def get_recomended_event(x):
    q_current = x["Q"]
    q_freq = x["Q_freq_optimal"]
    q_pump = x["potential_oil_rate_technical_limit"]

    q_n = x["oilWellopCountedOilDebit"]
    q_n_freq = x["Q_n_freq_optimal"]
    q_n_esp = x["Q_n_new_esp"]

    current_fcf = x["FCF текущий"]
    freq_fcf = x["FCF оптимальный"]
    pump_fcf = x["FCF насос"]
    freq = x["freq_optimal"]
    pump = x["Рекомендуемый УЭЦН"]
    if (
        (pump_fcf > freq_fcf)
        and (pump_fcf > current_fcf)
        and (pump != "Не удалось подобрать УЭЦН")
        and (q_n_esp - q_n > MIN_INCREASE_QN)
    ):
        return f"Сменить насос на {pump}", q_pump, q_n_esp, pump_fcf
    elif (
        (freq_fcf > current_fcf)
        and (q_freq > q_current)
    ):
        return f"Повысить частоту до {freq} Гц.", q_freq, q_n_freq, freq_fcf
    else:
        return "Мероприятие отсутствует", q_current, q_n, current_fcf


def value_with_locale(value):
    return locale.format_string("%10.0f", value, grouping=True).replace(",", " ")


def calculate_fcf(row, params):
    """
    _INSIDE_ calculate_wells
    :param row:
    :param params:
    :return: IS NOT responsible for drawing!
    """
    economics = Economics(
        q_zh_vol=row["Q"],
        ro_sm=row["FluidDensity"] / 1000,
        q_n=row["oilWellopCountedOilDebit"],
        specific_energy_mp=row["ure"],
        **params,
    )
    returns_current = economics.get_FCF()
    debug_current = economics.get_debug_info()
    ratio = row["Q_freq_optimal"] / row["Q"]
    q_n_freq_optimal = row["oilWellopCountedOilDebit"] * ratio

    economics = Economics(
        q_zh_vol=row["Q_freq_optimal"],
        ro_sm=row["FluidDensity"] / 1000,
        q_n=q_n_freq_optimal,
        specific_energy_mp=row["ure"],
        **params,
    )
    returns_optimal = economics.get_FCF()
    debug_optimal = economics.get_debug_info()

    # q_esp = 0
    if row["Рекомендуемый УЭЦН"] != "Не удалось подобрать УЭЦН":
        q_esp = row["potential_oil_rate_technical_limit"]
    else:
        q_esp = row["Q"]

    ratio = q_esp / row["Q"]
    q_n = row["oilWellopCountedOilDebit"] * ratio
    ure_esp = 24 * row["power_esp_optimal"] / row["potential_oil_rate_technical_limit"]
    economics = Economics(
        q_zh_vol=q_esp,
        ro_sm=row["FluidDensity"] / 1000,
        q_n=q_n,
        specific_energy_mp=ure_esp,  # В процентах от 0 до 1
        **params,
    )
    returns_esp = economics.get_FCF()
    debug_esp = economics.get_debug_info()
    result_dict = {
        "Q_n_freq_optimal": q_n_freq_optimal,
        "Q_n_new_esp": q_n,
        "ure_new_esp": ure_esp,
        "FCF текущий": returns_current,
        "FCF оптимальный": returns_optimal,
        "FCF насос": returns_esp,
    }
    return pd.Series(result_dict)


def calculation_event(df):
    # st.write(df)
    df[["event", "q_event", "q_n_event", "FCF_event"]] = df.apply(
        get_recomended_event, axis=1, result_type="expand"
    )
    return df


def get_diff_columns(temp_df):
    temp_df["diff_Q_freq"] = temp_df["Q_freq_optimal"] - temp_df["Q"]
    temp_df["diff_Q_oil_freq"] = (
        temp_df["Q_n_freq_optimal"] - temp_df["oilWellopCountedOilDebit"]
    )
    temp_df["diff_FCF_freq"] = temp_df["FCF оптимальный"] - temp_df["FCF текущий"]
    temp_df["diff_ure_freq"] = temp_df["ure"] - temp_df["ure"]

    temp_df["diff_Q_esp"] = temp_df["potential_oil_rate_technical_limit"] - temp_df["Q"]
    temp_df["diff_Q_oil_esp"] = (
        temp_df["Q_n_new_esp"] - temp_df["oilWellopCountedOilDebit"]
    )
    temp_df["diff_FCF_esp"] = temp_df["FCF насос"] - temp_df["FCF текущий"]
    temp_df["diff_ure_esp"] = temp_df["ure_new_esp"] - temp_df["ure"]
    return temp_df
