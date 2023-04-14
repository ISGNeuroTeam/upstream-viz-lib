from upstream_viz_lib.common.styler import get_numeric_style_with_precision, get_highlighter_by_condition, PRECISION_ZERO, PRECISION_ONE, \
    PRECISION_TWO
import upstream_viz_lib.config
from upstream_viz_lib.config import Color

data_folder = upstream_viz_lib.config.get_data_folder()


# stole from https://github.com/andfanilo/streamlit-echarts/blob/master/streamlit_echarts/frontend/src/utils.js Thanks andfanilo
class JsCode:
    def __init__(self, js_code: str):
        """Wrapper around a js function to be injected on gridOptions.
        code is not checked at all.
        set allow_unsafe_jscode=True on AgGrid call to use it.
        Code is rebuilt on client using new Function Syntax (https://javascript.info/new-function)

        Args:
            js_code (str): javascript function code as str
        """
        import re
        js_placeholder = "--x_x--0_0--"
        one_line_jscode = re.sub(r"\s+|\n+", " ", js_code)
        self.js_code = f"{js_placeholder}{one_line_jscode}{js_placeholder}"


economic_params = {
    "Netback": 16089,
    "Gasback": 619,
    "tax_rate_MPT": 10158,
    "energy_cost": 2.2,
    "specific_energy_inj": 4.4,
    "specific_energy_tr_g": 4.4,
    "specific_energy_tr_zh": 1.1,
    "specific_energy_tr_v": 0.0,
    "specific_energy_tr_n": 0.03,
    "CAPEX": 0.0,
    "burning_fine_rate": 853.0,
    "burning_perc": 6.5,
    "Gor": 50,
    "Period": 365,
    "perc": 0.99994,
    "process_loss": 0.0002,
    "ratio_inj_pro": 1.1,
    "unit_costs_n": 0,  # Удельные от нефти
    "average_TBR": 500,
    "revex_other": 0.0,  # Прочие расходы
    "semi_fixed": 1000,  # Условно-постоянные расходы
    "perc_g": 1.1,
    "outgo_inj": 0.0,
    "outgo_tr_g": 0.0,
    "outgo_prep": 0.0,
}


def highlight_k_flow():
    return JsCode(
        f"""
            function(params) {{
                red_color = "{Color.RED_LIGHT.value}";
                orange_color = "{Color.YELLOW_LIGHT.value}";
                if (params.value < 0.65) {{
                    return {{
                        'backgroundColor': red_color
                    }}
                }}
                if (params.value < 0.85) {{
                    return {{
                        'backgroundColor': orange_color
                    }}
                }}
            }};
        """
    )


format_analysis_table = {
    "__deposit": ("Месторождение", {"pinned": "left"}),
    "__pad_num": ("Куст", {"pinned": "left"}),
    "__well_num": ("Скв.", {"pinned": "left"}),
    "department": ("Цех", {}),
    "collection": ("ОП", {}),
    "recommended_event": ("Рекомендуемые мероприятия", {}),
    "pump_model": ("ЭЦН", {}),
    "date_installation": ("М/ж", {}),
    "pump_work_days": ("МРП", {}),
    "pump_depth": ("H сп.", PRECISION_ZERO),
    "shtr_debit": ("Qж", PRECISION_ZERO),
    "shtr_oil_debit": ("Qн", PRECISION_ONE),
    "water": ("Обв", PRECISION_ZERO),
    "h_din": ("H д.", PRECISION_ZERO),
    "p_input": ("Pпр", PRECISION_ONE),
    "p_zatrub": ("Pзатруб", PRECISION_ONE),
    "state_str": ("Режим", {}),
    "k_flow": ("К подачи", {
        **PRECISION_TWO,
        **{"cellStyle": highlight_k_flow()}
    }),
    # "times": ("Время работы", {}),
    "work_time": ("Цикл работы (мин.)", PRECISION_ZERO),
    "stop_time": ("Цикл простоя (мин.)", PRECISION_ZERO),
    "pump_enabled_by_day": ("Работа за сут(ч.)", PRECISION_ONE),
    "pump_disabled_by_day": ("Простой за сут(ч.)", PRECISION_ONE),
    "p_head": ("Pл", PRECISION_ONE),
    "p_buffer": ("Pбуф", PRECISION_ONE),
    "freqs": (
        "F Гц.",
        {
            "cellStyle": get_highlighter_by_condition(
                "== '0.0 / 0.0'", color=Color.YELLOW_LIGHT.value
            )
        },
    ),
    "comment": ("Примечание", {"editable": True, "type": ["numericColumn"]}),
    "comment_plan_event": ("Мероприятия: план", {"editable": True, "type": ["numericColumn"]}),
    "comment_completed_event": ("Мероприятия: выполнено", {"editable": True, "type": ["numericColumn"]}),
}

help_fields = [
    "pump_model",
    "date_installation",
    "pump_work_days",
    "pump_depth",
    "shtr_debit",
    "shtr_oil_debit",
    "water",
    "h_din",
    "p_head",
    "p_buffer",
    "p_input",
    "p_zatrub",
    "k_flow",
    "work_time",
    "stop_time",
    "pump_enabled_by_day",
    "pump_disabled_by_day",
]

help_tooltip = """
state: Режим (periodic / const),\n\n
pump_nominal: Номинал ЭЦН,\n\n
k_flow: К подачи,\n\n
h_above_pump: Высота столба над ЭЦН,\n\n
shtr_debit: Qж ШТР,\n\n
shtr_oil_debit: Qн ШТР,\n\n
max_freq: Макс. частота,\n\n
water: Обводненность,\n\n
pump_work_days: Число дней со дня установки ЭЦН
"""

format_all_comments = {
    "__deposit": ("Месторождение", {"pinned": "left"}),
    "__well_num": ("Скв.", {"pinned": "left"}),
    "time": ("Время добавления", {}),
    "comment": ("Примечание", {}),
    "comment_plan_event": ("Мероприятия: план", {}),
    "comment_completed_event": ("Мероприятия: выполнено", {}),
}

format_compare_table = {
    "__deposit": ("Месторождение", {"pinned": "left"}),
    "__pad_num": ("Куст", {"pinned": "left"}),
    "__well_num": ("Скв", {"pinned": "left"}),
    "predict_mode_str": ("Расчетный режим", {}),
    "shtr_mode": ("Режим ШТР", {}),
    "work_time_calculated": ("Цикл работы", get_numeric_style_with_precision(0)),
    "stop_time_calculated": ("Цикл простоя", get_numeric_style_with_precision(0)),
    "work_time_shtr": ("Цикл работы (ШТР)", get_numeric_style_with_precision(0)),
    "stop_time_shtr": ("Цикл простоя(ШТР)", get_numeric_style_with_precision(0)),
    "freqs": ("Частоты", {}),
    "wellTechModeRemarks": ("Примечания ШТР", {}),
}

QUERY_WELLS_LIST_TEMPLATE = """ 
| __SOURCE__ 
| eval one = 1
| search __CRITERIA__=1 AND day="__DAY__" 
| eval crit_last = ceil((_time - coalesce(__CRITERIA___from, _time)) / 86400)
| sort -crit_last 
"""

QUERY_WELL_DAILY_PARAMS = """
| #__SOURCE__#
| search well_type="Нефтяные" AND (well_condition="В работе" OR well_condition="В накоплении/под циклической закачкой/")
| where day="#__DAY__#"
"""

QUERY_TECH_REGIMES = """
| #__SOURCE__#
| search __deposit="#__DEPOSIT__#" AND day="#__DAY__#" 
"""

QUERY_WELL_DETAILS = """ 
| __SOURCE__
| search __well_num="__well_num__"
| eval day_str = strftime(_time, "%Y-%m-%d")
| search day_str="__day_str__" 
"""

QUERY_POTENTIALS = """
| __SOURCE__ 
| rename max_freq as freq
| where day="__DATE__"
| where state="const"
| where potential_oil_rate_technical_limit > Q
"""

QUERY_ALL_COMMENTS = """
| __SOURCE__
| eval time = strftime(_time, "%Y-%m-%d %H:%M")
| sort _time
"""