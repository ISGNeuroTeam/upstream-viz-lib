import upstream_viz_lib.config as config
import pandas as pd
from upstream_viz_lib.common.logger import logger

# эти две функции из библиотеки солвера
# отдельно их перенести сюда не получится: внутри них используются другие функции и методы солвера
# по сути все равно придется переносить всю библиотеку
from ksolver.io.calculate_DF import calculate_PPD_from_nodes_edges_df
from ksolver.tools.HE2_schema_maker import split_nodes_df_to_groups

html_folder = config.get_conf()["data"]["html"]


# Это основная функция
# принимает на вход ДФ узлов и ребер, получаемые из OTL-запросов
# сейчас можно эти ДФ взять из csv файлов в ППД-шной папке tests
#
def app(df_edges, df_nodes, eff_diam=0.46, use_coord=False, coordinate_scaling=6):
    # Задается эффективный диаметр
    df_edges["effectiveD"] = eff_diam

    # Разделение ДФ узлов на:
    # 1) узлы, которые принимают воду из окр. среды (inlets),
    # 2) узлы, которые выбрасывают воду в окр. среду (outlets),
    # 3) внутренние узлы, которые непосредственно с окр. средой не связаны (juncs)
    df_inlets, df_outlets, df_jncs = split_nodes_df_to_groups(df_nodes)

    # сздесь берутся ГУ, введенные пользователем
    inlets_dict = get_bounds_from_sidebar(df_inlets, "Граничные условия на КНС")
    outlets_dict = get_bounds_from_sidebar(df_outlets, "Граничные условия на скважинах")

    # ГУ, введенные пользователем, правильно (как нужно солверу) записываются в массив узлов
    df_nodes_with_sidebar = get_proper_bound_df(df_nodes, inlets_dict, outlets_dict)

    # Запуск солвера
    try:
        df_nodes_rez, df_edges_rez, g = calculate_PPD_from_nodes_edges_df(
            df_nodes_with_sidebar, df_edges
        )
        return df_nodes_rez, df_edges_rez, g
    except Exception as e:
        logger.error(e)
        return 0


def get_bounds_from_sidebar(df_bound: pd.DataFrame, form_name: str) -> dict:
    return_dict = {}
    for row in df_bound.sort_values("node_name").to_dict(orient="records"):
        return_dict.update(get_single_bound(row))
    return return_dict


def get_single_bound(row: dict) -> dict:
    pq_dict = {"P": "Давление", "Q": "Закачка"}
    name, value = row["node_name"], row["value"]
    kind = "P"  # или "Q" из pq_dict
    return {name: {"kind": kind, "value": value}}


def get_proper_bound_df(df_nodes, inlets_dict, outlets_dict):
    df_nodes_with_sidebar = df_nodes.copy()
    for name, bound in {**inlets_dict, **outlets_dict}.items():
        try:
            kind, value = bound["kind"], bound["value"]
            mask = df_nodes_with_sidebar["node_name"] == name
            df_nodes_with_sidebar.loc[mask, "kind"] = kind
            df_nodes_with_sidebar.loc[mask, "value"] = float(value)
        except ValueError as err:
            logger(err)
    return df_nodes_with_sidebar
