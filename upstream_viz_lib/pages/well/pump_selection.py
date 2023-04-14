from upstream_viz_lib import config
import pandas as pd
from os import path
from typing import Tuple
import numpy as np
from upstream.pumpselection.hydraulics.oil_params import oil_params
from upstream.pumpselection.pumpselection.Lyapkov.PumpSelectionAuto import (
    PumpSelectionAuto,
)

data_folder = config.get_data_folder()


def get_pump_chart() -> pd.DataFrame:
    """
    _INSIDE_ app
    :return: DataFrame pump_chart from parquet
    """
    pump_path = path.join(data_folder, "pump_curve")
    pump_chart = pd.read_parquet(pump_path, engine="pyarrow")
    pump_chart["NominalQ"] = pump_chart["pumpModel"].apply(
        lambda x: float(x.split("-")[1])
    )
    return pump_chart


def get_nkt() -> pd.DataFrame:
    """
    _INSIDE_ app
    :return: DataFrame nkt from parquet
    """
    nkt_path = path.join(data_folder, "HKT")
    nkt = pd.read_parquet(nkt_path, engine="pyarrow")
    return nkt


def get_inclination() -> pd.DataFrame:
    """
    _INSIDE_ app
    :return: DataFrame inclination from parquet
    """

    inclination_path = path.join(data_folder, "inclination")
    inclination = pd.read_parquet(inclination_path, engine="pyarrow")

    return inclination


def get_well_list(inclination: pd.DataFrame) -> Tuple[np.ndarray, int]:
    """
    _INSIDE_ app
    """
    well_list = inclination.sort_values("wellNum")["wellNum"].unique()
    return well_list


def get_tubing(inclination: pd.DataFrame, nkt: pd.DataFrame, well_num: str) -> pd.DataFrame:
    """
    _INSIDE_ app
    """
    tubing = inclination[inclination["wellNum"] == well_num]
    tubing = tubing.sort_values("depth")
    tubing["Roughness"] = 3e-5
    tubing["IntDiameter"] = 0.57
    tubing["NKTlength"] = 10
    local_nkt = nkt[nkt["wellNum"] == well_num]
    for stageNum in local_nkt["stageNum"].unique():
        stage_nkt = local_nkt[local_nkt["stageNum"] == stageNum]
        stage_nkt = stage_nkt[stage_nkt["_time"] == stage_nkt["_time"].max()]
        tubing.loc[
            tubing["depth"] <= stage_nkt["stageLength"].iloc[0], "IntDiameter"
        ] = (stage_nkt["stageDiameter"].iloc[0] - 16) / 1000
    return tubing


def get_calc_params(row: pd.Series) -> oil_params:
    """
    _INSIDE_ app
    """
    calc_params = oil_params(
        dailyQ=row["dailyDebit"],
        saturationPressure=row["OilSaturationP"],
        plastT=row["PlastT"],
        gasFactor=row["GasFactor"],
        oilDensity=row["SepOilWeight"],
        waterDensity=row["PlastWaterWeight"],
        gasDensity=row["GasDensity"],
        oilViscosity=row["SepOilDynamicViscosity"],
        volumeWater=row["neftWellopVolumeWater"],
        volumeoilcoeff=row["VolumeOilCoeff"],
    )
    calc_params.ZaboiP = row["ZaboyP"]
    calc_params.WellheadP = row["WellheadP"]
    calc_params.perforation = row["perforation"]

    calc_params.adkuLiquidDebit = (
            row["dailyDebit"]
            * (
                    row["SepOilWeight"] * (1 - calc_params.volumewater_percent / 100)
                    + row["PlastWaterWeight"] * (calc_params.volumewater_percent / 100)
            )
            / 86400
    )
    return calc_params


def select_pump(calc_params,
                tubing: pd.DataFrame,
                pump_chart: pd.DataFrame,
                row: pd.Series,
                pump_depth: int,
                base_worktime: float,
                well_num: str,
                count_KES: bool) -> pd.DataFrame:
    """
    _INSIDE_ app
    :param calc_params:
    :param tubing:
    :param pump_chart:
    :param row:
    :param pump_depth:
    :param base_worktime:
    :param well_num:
    :param count_KES:
    :return: ready for display result Data Frame
    """
    df_result = pd.DataFrame(
        columns=[
            "wellNum",
            "pumpModel",
            "debit",
            "pressure",
            "InputP",
            "eff",
            "power",
            "Separator",
            "Hdyn",
            "intensity 0.2",
            "intensity 0.3",
            "Depth",
        ]
    )
    temp_result = PumpSelectionAuto(
        calc_params,
        tubing,
        pump_chart,
        row["PlastT"],
        calc_params.adkuLiquidDebit,
        basedepth=pump_depth,
        perforation=row["perforation"],
        ZaboiP=row["ZaboyP"],
        WellheadP=row["WellheadP"],
        RequiredDebit=row["dailyDebit"],
        check_for_kes=count_KES,
        working_period_min=base_worktime,
    )
    temp_result["wellNum"] = well_num
    df_result = pd.concat((df_result, temp_result))
    df_result = df_result.drop_duplicates(subset=["pumpModel", "Depth"])
    return df_result
