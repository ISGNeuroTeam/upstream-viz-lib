'''
2022-12-06
'''

from ksolver.io.calculate_DF import calculate_DF


##  *  *  *  SUPPLEMENTARY FUNCTIONS  *  *  *

def filteroutWellPipes(df):
    """
    filters only <pipeline> system pipelines
    """
    return(df.loc[df.juncType != "oilwell", :])



def get_outlet_records(df):
    """
    converts pd.DataFrame with outlet nodes only to records
    
    Arguments:
    df: pd.DataFrame
    
    Returns:
    Dict
    """
    outlets_df = df[df["endIsOutlet"]].drop_duplicates(subset="node_id_end")
    outlets_records = outlets_df.to_dict(orient="records")
    return(outlets_records)



def get_default_pressure_values(outlet_records):
    """
    returns outlet records formatted for `options` variable inclusion
    
    Arguments:
    outlet_records: dict - records from pd.DataFrame with simple_parts filtered outlets only
                           keys: multiple (columns from dataframe), must contain:
                               "node_name_end": name of an outlet
                               "outletValue": pressure value at outlet
    
    Returns
    Dict: {name: {name: p} for record in records}
    """
    return({record["node_name_end"]:{"id": record["node_name_end"],
                                     "p": record["endValue"]} for record in outlet_records})



def squeeze_default_pressure_values(pressureValues):
    """
    reshapes pressureValues dict
        from {node_name: {"id": node_name,
                          "p" : pressure_value}}
        to   {node_name: pressure_value}
    """
    return({pressureValues[key]["id"]: pressureValues[key]["p"] for key in pressureValues.keys()})



def collect_state(
    ## --    
    df,
    ## "options" key:
    sidebarValues, liquidProperties, selected_dns,
    ## default values
    defaultEffDiamValue=0.9):
    """
    collects values for `state` variable, which is an aggregation 
        of streamlit.session_state with `options`
    
    Arguments:
    df: pd.DataFrame - hydraulic calculation input
    sidebarValues: dict
    liquidProperties: dict
    selected_dns: string
    
    Returns:
    Dict
    """
    outlet_records = get_outlet_records(df)
    defaultOutletPressureValues = get_default_pressure_values(outlet_records)
    
    state = {"defaults": {"eff_diam": {"id": "eff_diam", "value": defaultEffDiamValue}}}
    state["defaults"].update(defaultOutletPressureValues)
    
    state["options"] = {"liquid_properties": liquidProperties,
                        "selected_dns": selected_dns}
    state["options"].update(sidebarValues)
    return(state)



def beautify_result_df(df):
    """
    formats results table to be plotted
    
    Arguments:
    df: pd.DataFrame - results table
    
    Returns:
    pd.DataFrame - formatted results table
    """
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
    return(df)


def output_results(df):
    """
    returns calculation results:
        1: dataframe to show as AgGrid
        2 .. 6: deleted
        
    Arguments
    df: pd.DataFrame - hydraulic calculation results
    
    Returns:
    pd.DataFrame
    """
    wells_df = df[df["juncType"] == "oilwell"]
    draw_df = df[~df["node_id_start"].str.contains("PAD")].copy(deep=True)
    draw_df.loc[
        draw_df["node_id_start"].isin(wells_df["node_id_end"]), "startIsSource"
        ] = True

    # 1:
    df_toShow = beautify_result_df(draw_df)
    
    # 2:
    pass

    # 3,4,5,6:
    pass

    return(df_toShow)




##  *  *  *  CALCULATION FUNCTIONS  *  *  *

def clean(df):
    """
    filters out "oilwell"-type sections where pump model is unknown or is "Воронка"
    """
    only_pipes_mask = df["juncType"] != "oilwell"
    wells_with_pump_mask = (
        (df["juncType"] == "oilwell")
        & (df["model"].notna())
        & (df["model"] != "Воронка")
    )

    filter_mask = only_pipes_mask | wells_with_pump_mask
    df = df[filter_mask]
    df.dropna(subset=["node_id_start", "node_id_end"], how="any", inplace=True)
    return df.drop_duplicates()



def fill(df, options):
    """
    fills df for calculation with values needed
    """
    df = df.copy()
    
    for key, (value, _) in options["liquid_properties"].items():
        df[key] = float(value)

    for key, value in options["outlets_dict"].items():
        df.loc[df["node_name_end"] == key, "endValue"] = float(value)

    df["rs_schema_name"] = options["selected_dns"]
    df["effectiveD"] = options["eff_diam"]
    df["productivity"] = (
        df["productivity"].apply(lambda x: abs(x) if x != 0 else 0.01).fillna(0.01)
    )

    df["VolumeWater"] = df["VolumeWater"].astype(float)
    df["endIsOutlet"] = df["endIsOutlet"].fillna(False)
    df[["node_id_start", "node_id_end"]] = df[["node_id_start", "node_id_end"]].astype(
        str
    )

    return df.rename(
        columns={"__pad_num": "padNum", "__well_num": "wellNum", "d": "D", "s": "S"}
    )



def get_hcalc_results(df, state, data_folder):
    """
    performs hydraulic calculation 
    
    Arguments:
    df: pd.DataFrame - input data
    options: dict - input data
    data_folder: str - location to supplementary data for solver: inclination data, pumps table, etc.
    
    Returns:
    pd.DataFrame
    """
    ## Concat added pads
    dfCalc = df.copy()
    pass
    
    ## table calculation
    dfClean = clean(dfCalc)
    dfFilled = fill(dfClean, options=state["options"])
    dfResult, g = calculate_DF(dfFilled,
                               data_folder,
                               return_graph=True,
                               solver_params=dict(threshold=4.5))
    return(dfResult)














