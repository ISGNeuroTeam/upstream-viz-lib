'''
2022-12-20
'''

# import locale

from upstream_viz_lib.pages.pipe import pipeline_production as ppr
from upstream_viz_lib.pages.pipe import hcalc_dashboard_getdata as dta


##  ##

# def value_with_locale(value, precision=0):
#     return locale.format_string(f"%10.{precision}f", value, grouping=True)


def filter_df_toShow_noCalc(df):
    return(df.loc[df["juncType"] != "oilwell", :] \
             .sort_values("node_name_start"))


def output_grid(df):
    """
    returns dataframe to show as aggrid
    based on `results.show_grid`
    """
    mdf = df.copy()
    mdf = ppr.beautify_result_df(mdf)
    return(mdf)


def output_dns_load(df, selected_dns, getDnsLoadFn=dta.get_dns_load, only_working=True):
    """
    based on `results.show_dns_load`

    Arguments:
    df: pd.DataFrame - results of hydraulic calculation
    selected_dns: str - selected pipeline subsystem
    getDnsLoadFn: types.FunctionType - function to compute DNS load, accepts arguments
                                                q: float - DNS flow rate, m3/day
                                                selected_dns: str
                                                only_working: bool, default False
    only_working: bool

    Returns:
        1: dataframe with object loads
        2: flow rate metric (scalar)
        3: debit metric (scalar)
        4: load metric (scalar)
    """
    df = df.copy()
    result_df = ppr.beautify_result_df(df)
    result_df["qn_m3_day"] = result_df.apply(
        lambda row: (1 - row["res_watercut_percent"] / 100) * row["X_m3_day"], axis=1
    )
    result_dns_q = result_df[result_df["endIsOutlet"] == 1]["X_m3_day"].sum()
    result_dns_qn = result_df[result_df["endIsOutlet"] == 1]["qn_m3_day"].sum()
    df_load = getDnsLoadFn(q=result_dns_q,
                           selected_dns=selected_dns,
                           only_working=only_working)
    dns_predict = df_load[df_load["device_type"] == "ДНС"].to_dict(orient="records")[0]

    oil_density = dns_predict["oil_density_counted"]
    predict_qn = result_dns_qn * oil_density

    # 1:
    df_dns_load = df_load[df_load["device_type"] != "ДНС"].sort_values("device_type")
    # 2:
    # metric_q = value_with_locale(result_dns_q, precision=1)    
    metric_q = result_dns_q
    # 3:
    #TBD metric_qn = value_with_locale(predict_qn, precision=1)
    metric_qn = predict_qn
    # 4:
    #TBD metric_load = value_with_locale(dns_predict["predict_load_rate"], precision=2)
    metric_load = dns_predict["predict_load_rate"]

    ##
    return(df_dns_load, metric_q, metric_qn, metric_load)


def output_results(df, options, getDnsLoadFn=dta.get_dns_load):
    """
    returns calculation results:
        1: dataframe to show as AgGrid
        2: dataframe to be used to draw graph
        3: dataframe with loads
        4: metric for flow rate
        5: metric for debit
        6: metric for load
    """
    wells_df = df[df["juncType"] == "oilwell"]
    draw_df = df[~df["node_id_start"].str.contains("PAD")].copy(deep=True)
    draw_df.loc[
        draw_df["node_id_start"].isin(wells_df["node_id_end"]), "startIsSource"
    ] = True

    # 1:
    df_toShow = output_grid(draw_df)
    
    # 2:
    df_toDraw = draw_df.copy()

    # 3,4,5,6:
    df_dnsLoad, metric_q, metric_qn, metric_load = output_dns_load(df=draw_df,
                                                                   selected_dns=options["selected_dns"].lstrip("НС "),
                                                                   getDnsLoadFn=getDnsLoadFn,
                                                                   only_working=options["only_working"])

    return(df_toShow, df_toDraw, df_dnsLoad, metric_q, metric_qn, metric_load)