import numpy as np
import pandas as pd
from pandas import DataFrame
import glob
import os
from upstream_viz_lib.config import get_conf, with_locale, get_data_folder
from upstream_viz_lib.common import otp, styler, logger
import pdb

from ksolver.io.calculate_DF import (
    make_oilpipe_schema_from_OT_dataset,
    put_result_to_dataframe,
)
from ksolver.solver.HE2_Solver import HE2_Solver
from ksolver.tools.HE2_tools import check_solution
from upstream.potentials.Economics import Economics


data_folder = get_data_folder()


def beautify_result_df(df):
    def swap_start_end(row):
        if not row["startIsSource"] and row["X_kg_sec"] < 0:
            return row["node_name_end"], row["node_name_start"]
        else:
            return row["node_name_start"], row["node_name_end"]

    def make_positive(row, colname):
        return row[colname] if row["startIsSource"] else abs(row[colname])

    def make_flow_positive(row):
        return make_positive(row, "X_kg_sec")

    def make_velocity_positive(row):
        return make_positive(row, "velocity_m_sec")

    def convert_flow_to_m3_day(row):
        density = (
            row["density_calc"] * 1000
            if "density_calc" in row
            else row["res_liquid_density_kg_m3"]
        )
        return row["X_kg_sec"] * 86400 / density

    df[["node_name_start", "node_name_end"]] = df.apply(
        swap_start_end, axis=1, result_type="expand"
    )
    df["X_kg_sec"] = df.apply(make_flow_positive, axis=1)
    df["X_m3_day"] = df.apply(convert_flow_to_m3_day, axis=1)
    df["velocity_m_sec"] = df.apply(make_velocity_positive, axis=1)
    return df

def calculate_fcf(
    row,
    params,
    q_col="shtr_debit",
    qn_col="shtr_oil_debit",
    density_col="density_calc",
    ure_col="URE",
):
    economics = Economics(
        q_zh_vol=row[q_col],
        ro_sm=row[density_col],
        q_n=row[qn_col],
        specific_energy_mp=row[ure_col],
        **params,
    )
    return economics.get_FCF()


def get_dns_load_pct(q: float, _df_dns_load: pd.DataFrame) -> (float, str):
    idxmin = _df_dns_load["prod"].idxmin()
    min_row = _df_dns_load.iloc[[idxmin]].to_dict(orient="records")[0]
    return 100 * q / min_row["prod"], min_row["device_type"]


def run_solver(df):
    G, calc_df, df_to_graph_edges_mapping = make_oilpipe_schema_from_OT_dataset(
        df, folder=data_folder
    )
    solver = HE2_Solver(G)
    solver.push_result_to_log = True
    solver.solve(it_limit=500, threshold=7.5)
    if not solver.op_result.success:
        return

    vld = check_solution(G)
    if (vld.negative_P > 0) or (vld.misdirected_flow > 0) or (vld.bad_directions > 0):
        logger.logger.warning(vld)
        return

    calc_df = put_result_to_dataframe(G, calc_df, df_to_graph_edges_mapping)
    return calc_df


def get_random_params(df_params) -> dict:
    return df_params.groupby("wellNum").sample(1).set_index("wellNum").T.to_dict()


def mutate_df_opt(df_opt, df_params_choice):
    for well_num, params in df_params_choice.items():
        if well_num not in df_opt["wellNum"].values:
            continue
        freq = params["freq"]
        model = params["model"]
        df_opt.loc[(df_opt["wellNum"] == well_num), "frequency"] = freq
        df_opt.loc[(df_opt["wellNum"] == well_num), "model"] = model
    return df_opt


def filter_and_beautify(df, params):
    wells_mask = df["juncType"] == "wellpump"
    pipes_q_mask = (df["juncType"] == "pipe") & (df["startKind"] == "Q")
    result_wells_mask = wells_mask | pipes_q_mask
    pretty_df = beautify_result_df(df[result_wells_mask])
    pretty_df = add_new_fcf(pretty_df, params)

    return pretty_df


def get_oil_debit(row):
    init_q = row["shtr_debit"]
    init_qn = row["shtr_oil_debit"]
    init_water = row["VolumeWater"]
    oil_volume_rate = (100 - init_water) / 100
    q = row["X_m3_day"]
    oil_density = init_qn / (init_q * oil_volume_rate)
    return oil_density * q * oil_volume_rate


def add_new_fcf(df, _params):
    df["Qn_new"] = df.apply(lambda row: get_oil_debit(row), axis=1)
    df["URE_new"] = (
        24 * df["res_pump_power_watt"] / (1000 * df["X_m3_day"] * df["density_calc"])
    )
    df["URE_new"] = df["URE_new"].fillna(df["URE"])
    df["FCF_new"] = df.apply(
        lambda x: calculate_fcf(
            x, _params, q_col="X_m3_day", qn_col="Qn_new", ure_col="URE_new"
        ),
        axis=1,
    )
    return df

def run_solver_and_filter_and_beautify(df_opt, params):
    """
    upstream-viz  pages/opt/optimize.py 151
    Args:
        df (DataFrame): 

    Returns:
        DataFrame: new sorted dataframe 
    """
    df_init_calc = run_solver(df_opt)
    df_init_calc = filter_and_beautify(df_init_calc, params).rename(
            {
                "FCF_new": "FCF_init",
                "X_m3_day": "Q_init",
                "Qn_new": "Qn_init",
                "URE_new": "URE_init",
                "frequency": "freq_init",
                "model": "model_init",
            },
            axis=1,
        )

    return df_init_calc

def sort_by_padnum_and_wellnum(df):
    """
    upstream-viz  pages/opt/optimize.py 166 332
    Args:
        df (DataFrame): 

    Returns:
        DataFrame: new sorted dataframe 
    """
    return df.sort_values(["padNum", "wellNum"])

def get_init_q(df_init_calc):
    """
    upstream-viz  pages/opt/optimize.py 169
    Args:
        df_init_calc (DataFrame): 

    Returns:
        float: sum of init debit values
    """
    return df_init_calc["Q_init"].sum()

def get_init_qn(df_init_calc):
    """
    upstream-viz  pages/opt/optimize.py 166
    Args:
        df_init_calc (DataFrame): 

    Returns:
        float: sum of oil debit values
    """
    return df_init_calc["Qn_init"].sum()

def get_init_fcf(df_init_calc):
    """
    upstream-viz  pages/opt/optimize.py 166
    Args:
        df_init_calc (DataFrame): 

    Returns:
        float: FCF sum 
    """
    return df_init_calc["FCF_init"].sum()

def get_query_dns_load_tokens(selected_dns, init_q):
    """
    upstream-viz  pages/opt/optimize.py 173
    Args:
        df (DataFrame): 

    Returns:
        Dict: dict with DNS and QN values 
    """    
    return {
        "DNS": selected_dns.replace("НС ", ""),
        "QN": init_q,
    }

def get_init_dns_load_and_init_crit_device(init_q, selected_dns, df_dns_load):
    """
    upstream-viz  pages/opt/optimize.py 184
    Args:
        init_q (float): init debit sum
        selected_dns (str): name of dns folder 
        df_dns_load (DataFrame): df with DNS loading data 

    Returns:
        float: percent of DNS loading 
    """
    return get_dns_load_pct(
        init_q + 4966 if (selected_dns == "НС Тайлаковское м/р ДНС-1") else init_q,
        df_dns_load,
    )

def get_count_of_calculated_variants(df_params):
    """
    upstream-viz  pages/opt/optimize.py 206
    Args:
        df (DataFrame): df with economy parameters

    Returns:
        DataFrame: new sorted dataframe 
    """
    var_cnt = df_params.groupby(["wellNum", "model"]).size().astype("int64").product()
    var_cnt = var_cnt if var_cnt > 0 else 9223372036854775806
    return var_cnt

def get_best_fcf_df(selected_dns, df_opt, params):
    """
    upstream-viz  pages/opt/optimize.py 283
    Args:
        selected_dns (str):
        df_opt (DataFrame): 

    Returns:
        DataFrame: new sorted dataframe 
    """
    dns_folder = f"dns{selected_dns[-1]}"
    csv_files = glob.glob(os.path.join(data_folder, "opt", dns_folder, "*.csv"))
    fcfs = []
    df_init_calc = run_solver_and_filter_and_beautify(df_opt, params)
    for f in csv_files:
        result_df = pd.read_csv(f, dtype={"wellNum": str})

        cols_to_drop = [
            "FCF_init",
            "freq_init",
            "model_init",
            "Q_init",
            "Qn_init",
            "shtr_oil_debit",
            "density_calc",
            "URE",
            "predict_mode_str",
        ]
        for col in cols_to_drop:
            if col in result_df.columns:
                result_df = result_df.drop(col, axis=1)
        result_df = result_df.merge(
            df_init_calc[["wellNum"] + cols_to_drop], how="left", on="wellNum"
        )
        wells_mask = result_df["juncType"] == "wellpump"
        pipes_q_mask = (result_df["juncType"] == "pipe") & (
            result_df["startKind"] == "Q"
        )
        result_wells_mask = wells_mask | pipes_q_mask
        try:
            pretty_df = beautify_result_df(result_df[result_wells_mask])
            pretty_df = add_new_fcf(pretty_df, params)
            fcfs.append((pretty_df, pretty_df["FCF_new"].sum()))
        except Exception as _:
            logger.logger.error(result_df)
        
        best_df, _ = max(fcfs, key=lambda x: x[-1])
        return best_df