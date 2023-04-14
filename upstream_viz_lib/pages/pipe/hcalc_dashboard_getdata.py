'''

'''

from upstream_viz_lib import config
from upstream_viz_lib.common import otp

from upstream_viz_lib.pages.pipe import pipeline_production_static as stc
from upstream_viz_lib.pages.pipe import hcalc_dashboard_static as stc2


def get_hcalc_data(field_name, scheme_name, date):
    """
    returns dataframe - input data for hydraulic calculation

    Arguments:
    field_name: str - field name taken from selectbox (not used before all input data formatted/prepared)
    scheme_name: str - scheme name (inside selected field) taken from selectbox
    date: str/int - date calculation to be done on (not used right now, just to be not hardcoded)

    Returns:
    pd.DataFrame
    """
    query = otp.render_query(query_template=stc.QUERY_TEMPLATE_calc_data,
                             query_params={"__SOURCE__": config.get_data_conf()["pipe"]["calc_wells"], # config.get_conf("get_data.yaml")["pipe"]["calc_wells"],
                                           "__FIELD_NAME__": field_name,
                                           "__SCHEME_NAME__": scheme_name,
                                           "__TIME__": date})
    dfCalc = otp.get_data(query)
    return(dfCalc)



def get_prediction_data(field_name, scheme_name, date):
    """
    
    """
    query = otp.render_query(query_template=stc.QUERY_TEMPLATE_prediction_noModes,
                             query_params={"__SOURCE__": config.get_data_conf()["pipe"]["pipe_prediction"], # config.get_conf("get_data.yaml")["pipe"]["pipe_prediction"],
                                           "__FIELD_NAME__": field_name,
                                           "__SCHEME_NAME__": scheme_name,
                                           "__TIME__": date})    
    dfResult = otp.get_data(query)
    return(dfResult)    



def get_dns_load(q: float, selected_dns: str, only_working: bool = False):
    """
    
    """
    is_work_mask = (
        """where is_work=1 OR device_type="ДНС" """
        if only_working
        else "___ # No filter ___ "
    )
    query_load = stc2.QUERY_TEMPLATE_dns_load.replace(
        "__FILTER_IS_WORK__", is_work_mask
    )
    df_load = otp.get_data(query_load)
    df_load = df_load[df_load["address"] == selected_dns.lstrip("НС ")]
    df_load["current_load_rate"] = 100 * df_load["current_debit"] / df_load["prod"]
    df_load["predict_load_rate"] = 100 * q / df_load["prod"]
    df_load["device_type"] = df_load["device_type"].replace(
        {
            "О": "Отстойники нефти",
            "НГС": "Нефтегазовые сепараторы",
            "РВС": "Резервуары РВС",
        }
    )
    return df_load



def get_field_names():
    query_field_names = otp.render_query(query_template=stc2.QUERY_TEMPLATE_field_names,
                                         query_params={})
    return(otp.get_data(query_field_names))



def get_scheme_names(field_name):
    query_scheme_names = otp.render_query(query_template=stc2.QUERY_TEMPLATE_scheme_names,
                                          query_params={"__FIELD_NAME__": field_name})
    return(otp.get_data(query_scheme_names))












