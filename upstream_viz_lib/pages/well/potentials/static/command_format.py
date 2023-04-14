from upstream_viz_lib.common.styler import get_highlighter_by_condition, PRECISION_ZERO, PRECISION_ONE, \
    PRECISION_TWO
from collections import OrderedDict
from upstream_viz_lib import config


FORMAT_DF = {
    "__pad_num": ("Куст", {"pinned": "left"}),
    "__well_num": ("Скв.", {"pinned": "left"}),
    "pump_model": ("УЭЦН", {}),
    "control_station_model": ("СУ", {}),
    "start_type": ("Пуск", {}),
    "Q": ("Qж", PRECISION_ZERO),
    "oilWellopCountedOilDebit": ("Qн", PRECISION_ONE),
    "water": ("H20 %", PRECISION_ZERO),
    "potential_oil_rate_technical_limit": (
        "Q тех.предел",
        PRECISION_ZERO,
    ),
    "p_input": ("Прием", PRECISION_ZERO),
    "P_bottom_hole_current": ("Забойное", PRECISION_ZERO),
    "P_bottom_hole_technical_limit": (
        "Забойное тех.предел",
        PRECISION_ZERO,
    ),
    "P_plast": ("Пластовое", PRECISION_ZERO),
    "P_zatrub": ("Затрубное", PRECISION_ZERO),
    "K_prod": ("K прод", PRECISION_TWO),
    "k_flow": (
        "К подачи",
        {
            **PRECISION_TWO,
            **{"cellStyle": get_highlighter_by_condition("< 0.8", color=config.YELLOW_COLOR)}
        },
    ),
    "mean_freq": ("Частота", PRECISION_ONE),
    "Loading": ("Загрузка", PRECISION_ONE),
    "H_perf": ("Глубина перфорации", PRECISION_ONE),
    "H_pump": ("Глубина спуска", PRECISION_ONE),
    "predict_mode_str": ("Текущий режим", {}),
    "FluidDensity": ("Плотность", PRECISION_ONE),
    "comment": ("Примечание", {"editable": True, "type": ["numericColumn"]}),
}

FORMAT_EVENTS = {
    "__well_num": ("Скв", {}),
    "__pad_num": ("Куст", {}),
    "q_event": ("Qж", PRECISION_ONE),
    "event": ("Рекомендуемое мероприятие", {}),
    "FCF_event": ("FCF мероприятия", PRECISION_ONE),
}

renames_dict = OrderedDict(
    {
        "padNum": "Номер куста",
        "wellNum": "Номер скважины",
        "pump_model": "Модель ЭЦН",
        "Q": "Qж",
        "potential_oil_rate_technical_limit": "Q тех.лимит",
        "P_bottom_hole_current": "Текущее забойное",
        "P_bottom_hole_technical_limit": "Забойное тех-предел",
        "P_plast": "Пластовое",
        "P_zatrub": "Затрубное",
        "P_saturation": "Давление насыщения",
        "K_prod": "Коэф продуктивности",
        "freq": "Частота",
        "H_perf": "Глубина перфорации",
        "H_pump": "Глубина спуска насоса",
        "regime": "Режим работы насоса",
        "Loading": "Загрузка",
        "water": "Обводненность",
        "FluidDensity": "Плотность жидкости",
        "oilWellopCountedOilDebit": "Qн",
        "H_pump_length": "Удлинение глубины насоса",
        "H_perf_length": "Удлинение глубины  перфорации",
        "ure": "УРЭ при текущих параметрах",
    }
)

FORMAT_FREQUENCY = {
    "__pad_num": ("Куст", {"pinned": "left"}),
    "__well_num": ("Скважина", {"pinned": "left"}),
    "Q": ("Qж, м3/сут", PRECISION_ZERO),
    "oilWellopCountedOilDebit": ("Qн, т/сут", PRECISION_ONE),
    "water": ("Обв., %", PRECISION_ZERO),
    "pump_model": ("Модель ЭЦН", {}),
    "control_station_model": ("СУ", {}),
    "start_type": ("Пуск", {}),
    "k_flow": (
        "К подачи",
        {
            **PRECISION_TWO,
            **{"cellStyle": get_highlighter_by_condition("< 0.8", color=config.YELLOW_COLOR)}
        },
    ),
    "P_bottom_hole_current": (
        "Р забойное, атм",
        PRECISION_ONE,
    ),
    "H_pump": (
        "Глубина спуска, м",
        PRECISION_ZERO,
    ),
    "P_plast": ("Р пласт, атм", PRECISION_ZERO),
    "K_prod": ("K прод", PRECISION_TWO),
    "mean_freq": ("Частота, Гц", PRECISION_ONE),
    "Loading": ("Загрузка, %", PRECISION_ONE),
    "ure": ("УРЭ, кВтсут/т.ж.", PRECISION_ONE),
    "FCF текущий": ("FCF, руб.", PRECISION_ONE),
    "freq_optimal": ("Частота опт.", PRECISION_ONE),
    "Q_freq_optimal": ("Qж_опт", PRECISION_ZERO),
    "Q_n_freq_optimal": ("Qн_опт", PRECISION_ONE),
    "P_bottom_hole_freq_optimal": (
        "Забойное давление опт.",
        PRECISION_ONE,
    ),
    "Loading_optimal": (
        "Загрузка опт.",
        PRECISION_ONE,
    ),
    "FCF оптимальный": ("FCF опт.", PRECISION_ONE),
    "diff_Q_freq": ("Прирост Qж", PRECISION_ZERO),
    "diff_Q_oil_freq": ("Прирост Qн", PRECISION_ONE),
    "diff_FCF_freq": ("Прирост FCF", PRECISION_ONE),
}

FORMAT_PUMP = {
    "__pad_num": ("Куст", {"pinned": "left"}),
    "__well_num": ("Скважина", {"pinned": "left"}),
    "pump_model": ("Модель ЭЦН", {}),
    "H_pump": (
        "Глубина спуска, м",
        PRECISION_ZERO,
    ),
    "Q": ("Qж, м3/сут", PRECISION_ZERO),
    "oilWellopCountedOilDebit": ("Qн, т/сут", PRECISION_ONE),
    "water": ("Обв., %", PRECISION_ZERO),
    "P_bottom_hole_current": (
        "Р забойное, атм",
        PRECISION_ONE,
    ),
    "ure": ("УРЭ, кВтсут/т.ж.", PRECISION_ONE),
    "FCF текущий": ("FCF, руб.", PRECISION_ONE),
    "Рекомендуемый УЭЦН": ("Рекомендуемый УЭЦН", {}),
    "potential_oil_rate_technical_limit": (
        "Qж насос",
        PRECISION_ZERO,
    ),
    "Q_n_new_esp": ("Qн насос", PRECISION_ONE),
    "P_bottom_hole_technical_limit": (
        "Р забойное насос",
        PRECISION_ONE,
    ),
    "FCF насос": ("FCF насос", PRECISION_ONE),
    "ure_new_esp": ("УРЭ насос", PRECISION_ONE),
    "diff_Q_esp": ("Прирост Qж", PRECISION_ZERO),
    "diff_Q_oil_esp": ("Прирост Qн", PRECISION_ONE),
    "diff_FCF_esp": ("Прирост FCF", PRECISION_ONE),
    "diff_ure_esp": ("Прирост УРЭ", PRECISION_ONE),
}

# TODO Move first line of query to get_data.yaml
QUERY_POTENTIALS = """
| readFile format=parquet path=FS/mechfond/potential_rate 
| where day="$date$"
| where state="const"
| where potential_oil_rate_technical_limit > Q
"""
SUM_DEBIT = """
 | readFile format=parquet path=FS/mechfond/totals
 | where day="$date$"
"""
SUM_OILDEBIT = """
 | readFile format=parquet path=FS/mechfond/totals
 | where day="$date$"
"""
SUM_POWER = """
 | readFile format=parquet path=FS/mechfond/totals
 | where day="$date$"
"""

HELP_POTENTIALS = """Для каждой скважины расчитывается технический предел добычи, исходня из следующих условий: (1) 
давление на приеме ЭЦН не менее 30 атм.; (2) высота столба жидкости над ЭЦН не менее 300 м. По этим условиям 
рассчитывается минимально допустимое забойное давление и максимальная добыча (потенциал). Строится виртуальная модель скважины, 
моделируется раскрутка с учетом указанных ограничений и замена ЭЦН. Выбирается мероприятие с максимальным 
экономическим эффектом """
