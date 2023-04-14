from dataclasses import dataclass, field
from typing import Callable, List, Optional
from upstream.analysis import recommended_events

from upstream_viz_lib.pages.well.analysis.static import data_folder, economic_params


@dataclass
class Criteria:
    id: str
    name: str
    formula: Optional[str]
    conditions: List[str]
    function: Optional[Callable] = None
    kwargs: dict = field(default_factory=dict)


criteria_list = [
    Criteria(id="crit_all", name="Весь фонд", formula=None, conditions=[]),

    Criteria(
        id="crit_adjust_kes",
        name="Корректировка периодического режима",
        formula=""" state=='periodic' and k_flow<0.5 """,
        conditions=["скважина работает в периодическом режиме", "коэффициент подачи насоса < 0.5",],
        function=recommended_events.get_event_crit_adjust_kes,  # TODO Заменить work_time_counted на work_time внутри
    ),

    Criteria(
        id="crit_kes",
        name="Перевод в КЭС",
        formula=""" state=='const' and pump_nominal<=125 and h_above_pump<400 and k_flow<0.8 """,
        conditions=[
            "скважина работает в постоянном режиме",
            "номинальная производильность ЭЦН <= 125",
            "высота столба жидкости над ЭЦН < 400м",
            "дебит жидкости < 80% от номинала ЭЦН",
        ],
        function=recommended_events.get_event_crit_kes,
    ),

    Criteria(
        id="crit_right",
        name="Приведение в соответствие (правая зона)",
        formula=""" k_flow>1.3 and pump_nominal>160 and shtr_oil_debit<50 and max_freq>=55 """,
        conditions=[
            "дебит жидкости > 130% от номинальной производительности",
            "номинальная производительность >= 160",
            "дебит нефти < 50т",
            "Частота ЭЦН > 55Гц",
        ],
        function=recommended_events.get_event_crit_right,
        kwargs={"data_folder": data_folder, "economic_params": economic_params},
    ),

    Criteria(
        id="crit_up",
        name="Приподъем",
        formula=""" pump_nominal>250 and h_above_pump>800 and water>80 and pump_work_days>700 """,
        conditions=[
            "номинальная производительность ЭЦН >= 250",
            "высота столба жидкости над ЭЦН > 800м",
            "обводненность > 80%",
            "время от запуска насоса > 700дн",
        ],
        function=recommended_events.get_event_crit_up,
        kwargs={"data_folder": data_folder, "economic_params": economic_params},
    ),

    Criteria(
        id="crit_pritok",
        name="Смена ЭЦН по притоку",
        formula=""" state=='const' and pump_nominal>=160 and h_above_pump<400 and k_flow<0.8 """,
        conditions=[
            "скважина работает в постоянном режиме",
            "номинальная производительность ЭЦН >= 160",
            "высота столбы жидкости над ЭЦН < 400м",
            "дебит жидкости составляет менее 80% от номинала насоса",
        ],
        # function=recommended_events.get_event_crit_pritok,
        kwargs={"data_folder": data_folder, "economic_params": economic_params},
    ),

    Criteria(
        id="crit_technology",
        name="Смена ЭЦН по технологии",
        formula=""" state=='const' and k_flow<0.8 and h_above_pump>400 """,
        conditions=[
            "скважина работает в постоянном режиме",
            "высота столба жидкости над ЭЦН >= 400м",
            "дебит жидкости < 80% от номинала насоса",
        ],
    ),

    Criteria(
        id="crit_shtuz",
        name="Штуцирование",
        formula=""" state=='const' and p_buffer-p_linear>3 """,
        conditions=[
            "буферное давление > линейного давления на 3атм и более",
            "скважина работает в постоянном режиме",
        ],
        function=recommended_events.get_event_crit_shtuz,
        kwargs={"data_folder": data_folder, "economic_params": economic_params},
    ),

    Criteria(
        id="crit_left_nrh",
        name="В левой зоне НРХ",
        formula=""" k_flow<0.8 """,
        conditions=["дебит жидкости < 80% от номинала насоса"],
        function=recommended_events.get_event_crit_left_nrh
    )
]


def get_criteria_by_id(_id: str) -> Optional[Criteria]:
    return next((c for c in criteria_list if c.id == _id), None)
