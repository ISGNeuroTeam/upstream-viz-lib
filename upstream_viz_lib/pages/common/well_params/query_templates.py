INDEX_QUERY = """
| __SOURCE__ earliest=__TWS__ latest=__TWF__ __well_num="__WELL__" (__METRICS__)
| eval value=round(value, 1) """

EXTERNAL_DATA_QUERY = """
| __SOURCE__ 
| where (_time>=__TWS__ AND _time<__TWF__) AND __well_num="__WELL__" AND (__METRICS__)
| eval value=round(value, 1) """

DATA_QUERY = """
| #__SOURCE__# 
| where (_time>=#__TWS__# AND _time<#__TWF__#) AND __deposit="#__DEPOSIT__#" AND __well_num="#__WELL__#" AND (#__METRICS__#)
"""

QUERY_METRICS = """
| __SOURCE__
| stats count by __deposit, metric_long_name, metric_name """

WELL_STATES = """
| __SOURCE__
"""

# pump_query = f""" | {get_data_conf["well"]["pump"]}
#         | search __well_num="{selected_well}"
#         """

PUMP_PROPS = """
| #__SOURCE__#
| where __well_num = "#__WELL_NUM__#" AND __deposit = "#__DEPOSIT__#"
"""
