import pandas as pd
import numpy as np


from os import path
from upstream_viz_lib import config
from upstream.nkt import NKTPartDict
from upstream.nkt import Solver

def read_nkt_dict(nkt_path: str) -> dict:
    nkt_df = pd.read_csv(nkt_path)
    nkt_dict = (
        nkt_df[nkt_df["PRICE_CORR"].notnull()][
            ["NAME", "QNKT", "LIQ", "DNKT0", "FMAX", "PRICE_CORR"]
        ]
        .set_index("NAME")
        .T.to_dict()
    )
    return {
        k: NKTPartDict(
            k, v["QNKT"], v["LIQ"], v["DNKT0"], v["FMAX"] * 1000, v["PRICE_CORR"]
        )
        for k, v in nkt_dict.items()
    }

def calculate_extra_fields(res_dict: list[dict]):
    # наименее прочная ступень, на нее приходится какая-то нагрузка (из поля load)
    weakest_max_load = min([part["max_load"] for part in res_dict])
    # текущая нагрузка на наименее прочную ступень
    weakest_load = max(
        [part["load"] for part in res_dict if part["max_load"] == weakest_max_load]
    )
    for part in res_dict:
        podryv = (part["load"] - weakest_load) + weakest_max_load
        part["podryv"] = part["max_load"] if podryv < weakest_max_load else podryv
        for key in ["load", "max_load", "weight", "podryv"]:
            part[key] = part[key] / 9806.65
    for (idx, part) in enumerate(res_dict):
        part["order"] = idx + 1
    return res_dict


def get_nkt(
    nkt_type: str,
    pump_weight:int,
    pump_nominal: str,
    ped_weight:int,
    cable_weight:float,
    p_head: int,
    pump_depth: int,
    packers: str,
    safety_limit: float,
    is_repaired: bool
    ) -> pd.DataFrame:

    data_folder = config.get_data_folder()
    nkt_dict_path = path.join(data_folder, "tubings.csv")
    nkt_part_dict = read_nkt_dict(nkt_dict_path)


    slv = Solver(nkt_part_dict)

    results = slv.solve(
            pump_weight=int(pump_weight),
            pump_nominal=int(pump_nominal),
            ped_weight=int(ped_weight),
            cable_weight=float(cable_weight),
            p_head=int(p_head),
            pump_depth=int(pump_depth),
            packers=[int(p.strip()) for p in packers.split(",")],
            safety_limit=float(safety_limit),
            eps_limit=0.02,
            keep="fit",
            is_repaired=is_repaired,
        )

    best, simple = results


    return pd.DataFrame(calculate_extra_fields(best if nkt_type == "best" else simple)) \
        .drop("id", axis=1) \
        .round({'max_load': 1, 'safety': 2,'load': 1,'weight': 1,'podryv': 1,})



def get_best_nkt(
    pump_weight:int,
    pump_nominal: str,
    ped_weight:int,
    cable_weight:float,
    p_head: int,
    pump_depth: int,
    packers: str,
    safety_limit: float,
    is_repaired: bool
    ) -> pd.DataFrame:
    return get_nkt("best", pump_weight, pump_nominal, ped_weight,cable_weight,p_head,pump_depth,packers,safety_limit,is_repaired)

def get_simple_nkt(
    pump_weight:int,
    pump_nominal: str,
    ped_weight:int,
    cable_weight:float,
    p_head: int,
    pump_depth: int,
    packers: str,
    safety_limit: float,
    is_repaired: bool
    ) -> pd.DataFrame:
    return get_nkt("simple", pump_weight, pump_nominal, ped_weight,cable_weight,p_head,pump_depth,packers,safety_limit,is_repaired)


def calculate_tubing_reliability(
    stages_types:list[str],
    stages_length: list[int],
    pump_weight:int,
    ped_weight:int,
    cable_weight:float,
    p_head: int,
    pump_depth: int
    ) -> pd.DataFrame:

    data_folder = config.get_data_folder()
    nkt_dict_path = path.join(data_folder, "tubings.csv")
    nkt_part_dict = read_nkt_dict(nkt_dict_path)

    slv = Solver(nkt_part_dict)

    filtered = [
        (t, int(length))
        for t, length in zip(stages_types, stages_length)
        if (t != "-") & (length != 0)
    ]

    if filtered:
        types, lengths = list(zip(*filtered))
        calculated_nkt = slv.calculate(
            pump_weight=int(pump_weight),
            ped_weight=int(ped_weight),
            cable_weight=float(cable_weight),
            p_head=int(p_head),
            pump_depth=int(pump_depth),
            types=types,
            lengths=lengths,
        )
        calculated_df = pd.DataFrame(calculate_extra_fields(calculated_nkt)).drop(
            "id", axis=1
        ).round({'max_load': 1, 'safety': 2,'load': 1,'weight': 1,'podryv': 1,})
        return calculated_df

    return pd.DataFrame()
