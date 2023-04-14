import pandas as pd
import streamlit as st

from common.lib import dataframe_to_excel

DEFAULT_ECONOMICS_PARAMETRS = {
    "perc": 99.994,
    "process_loss": 0.0002,
    "Netback": 16089,
    "Gor": 34.8,
    "Gasback": 619,
    "perc_g": 1.1,
    "tax_rate_MPT": 10158,
    "semi_fixed": 1000,
    "ratio_inj_pro": 1.1,
    "specific_energy_inj": 4.4,
    "specific_energy_tr_n": 0.03,
    "specific_energy_tr_zh": 1.1,
    "specific_energy_tr_v": 0.0,
    "specific_energy_tr_g": 4.4,
    "energy_cost": 2.2,
    "unit_costs_n": 0.0,
    "outgo_inj": 0.0,
    "outgo_prep": 0.0,
    "outgo_tr_g": 0.0,
    "revex_other": 0.0,
    "average_TBR": 500,
    "burning_fine_rate": 853.0,
    "burning_perc": 6.5,
    "CAPEX": 0.0,
}


def sidebar():
    params = {}
    criterions = {}
    with st.sidebar:
        uploaded_file = st.file_uploader("Загрузите файл с экономическими параметрами")

        df_econom_param = pd.Series(DEFAULT_ECONOMICS_PARAMETRS).to_frame()
        df_econom_param = df_econom_param.rename(columns={0: "Значение"})
        df_econom_param.index.name = "Переменная"

        st.download_button(
            label="Скачать файл с предустановленными экономическимим параметрами",
            data=dataframe_to_excel(df_econom_param),
            file_name="default_param.xlsx",
        )
        if uploaded_file is not None:
            dataframe = pd.read_csv(uploaded_file, delimiter=";", decimal=",")
            economic_parametrs = dataframe.set_index("Переменная")["Значение"].to_dict()
        else:
            economic_parametrs = DEFAULT_ECONOMICS_PARAMETRS

        with st.form("Параметры экономики"):
            with st.expander("Экономические параметры"):
                params["Netback"] = st.number_input(
                    "Netback (тыс. руб./т.ж.)",
                    min_value=float(0),
                    max_value=float(100000),
                    value=float(economic_parametrs["Netback"]),
                )  # в чем измеряется
                params["Gasback"] = st.number_input(
                    "Gasback (руб./тыс.м3)",
                    min_value=float(0),
                    max_value=float(100000),
                    value=float(economic_parametrs["Gasback"]),
                )  # в чем измеряется
                params["tax_rate_MPT"] = st.number_input(
                    "Налог на добычу (тыс.руб)",
                    min_value=float(0),
                    max_value=float(100000),
                    value=float(economic_parametrs["tax_rate_MPT"]),
                )  # в чем измеряет# В чем измеряется??
                params["energy_cost"] = st.number_input(
                    "Стоимость электроэнергии (руб/(кВт*ч)",
                    min_value=float(0),
                    max_value=float(1000),
                    value=float(economic_parametrs["energy_cost"]),
                )  # в чем измеряет
                params["process_loss"] = st.number_input(
                    "Технологические потери нефти(%)",
                    min_value=float(0),
                    max_value=float(100),
                    value=float(economic_parametrs["process_loss"]),
                )
            with st.expander("Энергетические параметры"):
                params["specific_energy_inj"] = st.number_input(
                    "УРЭ на ППД (кВТ*ч/м3)",
                    min_value=float(0),
                    max_value=float(200),
                    value=float(economic_parametrs["specific_energy_inj"]),
                )  # Квт.* часrevex_other/т.ж
                params["specific_energy_tr_g"] = st.number_input(
                    "УРЭ на транспортировку и сбор ПНГ",
                    min_value=float(0),
                    max_value=float(200),
                    value=float(economic_parametrs["specific_energy_tr_g"]),
                )  # Квт.* часrevex_other/т.ж
                params["specific_energy_tr_zh"] = st.number_input(
                    "УРЭ на транспортировку жидкости(кВт*ч/тн.)",
                    min_value=float(0),
                    max_value=float(200),
                    value=float(economic_parametrs["specific_energy_tr_zh"]),
                )  # Квт.* часrevex_other/т.ж
                params["specific_energy_tr_v"] = st.number_input(
                    "УРЭ на транспортировку воды (кВт*ч/м3)",
                    min_value=float(0),
                    max_value=float(200),
                    value=float(economic_parametrs["specific_energy_tr_v"]),
                )  # Квт.* часrevex_other/т.ж
                params["specific_energy_tr_n"] = st.number_input(
                    "УРЭ на подготовку, транспортировку и внешнюю транспортировку (кВт*ч/тн.н.)",
                    min_value=float(0),
                    max_value=float(200),
                    value=float(economic_parametrs["specific_energy_tr_n"]),
                )

            with st.expander("Прочие расходы и затраты"):
                params["CAPEX"] = st.number_input(
                    "CAPEX (руб.)",
                    min_value=float(0),
                    max_value=float(100000),
                    value=float(economic_parametrs["CAPEX"]),
                )  # в чем измеряется
                params["semi_fixed"] = st.number_input(
                    "Условно-постоянные от СДФ (руб.)",
                    min_value=float(0),
                    max_value=float(100000),
                    value=float(economic_parametrs["semi_fixed"]),
                )
                params["revex_other"] = st.number_input(
                    "Прочие единовременные расходы (руб.)",
                    min_value=float(0),
                    max_value=float(100000),
                    value=float(economic_parametrs["revex_other"]),
                )  # в чем измеряется
                params["outgo_inj"] = st.number_input(
                    " Переменные расходы по ППД (руб.)",
                    min_value=float(0),
                    max_value=float(100000),
                    value=float(economic_parametrs["outgo_inj"]),
                )  # в чем измеряется
                params["outgo_tr_g"] = st.number_input(
                    " Переменные расходы по сбор и трасп. ПНГ (руб.)",
                    min_value=float(0),
                    max_value=float(100000),
                    value=float(economic_parametrs["outgo_tr_g"]),
                )  # в чем измеряется
                params["outgo_prep"] = st.number_input(
                    "Переменные расходы на подготовку, транспорт нефти и коммерч.(руб.)",
                    min_value=float(0),
                    max_value=float(100000),
                    value=float(economic_parametrs["outgo_prep"]),
                )  # в чем измеряется
            with st.expander("Параметры сжигания ПНГ"):
                params["burning_fine_rate"] = st.number_input(
                    "Штрафы за сжигание ПНГ (руб./тыс.м3.)",
                    min_value=float(0),
                    max_value=float(1000),
                    value=float(economic_parametrs["burning_fine_rate"]),
                )
                params["burning_perc"] = (
                    st.number_input(
                        "Сверхнормативное сжингание ПНГ (%)",
                        min_value=float(0),
                        max_value=float(200),
                        value=float(economic_parametrs["burning_perc"]),
                    )
                    / 100
                )
                params["perc_g"] = st.number_input(
                    "Процент реализации ПНГ (%)",
                    min_value=float(0),
                    max_value=float(1000),
                    value=float(economic_parametrs["perc_g"]),
                )

            params["Gor"] = st.number_input(
                "Газовый фактор (м3/т)",
                min_value=float(0),
                max_value=float(150),
                value=float(economic_parametrs["Gor"]),
            )  # в чем измеряется

            params["Period"] = st.number_input(
                "Период расчета (дн.)", min_value=1, max_value=1000, value=365
            )  # в чем измеряется
            params["perc"] = (
                st.number_input(
                    "Процент падения добычи (%)",
                    min_value=float(0),
                    max_value=float(100),
                    value=float(economic_parametrs["perc"]),
                    step=0.0001,
                    format="%.4f",
                )
                / 100
            )  # в чем измеряется

            params["ratio_inj_pro"] = 1.1
            params["unit_costs_n"] = 0  # Удельные от нефти
            params["average_TBR"] = 500

            criterions["crit1"] = st.checkbox("Забойное не ниже тех.предела")
            criterions["crit2"] = st.checkbox("Загрузка не более 95%", value=True)
            criterions["crit3"] = st.checkbox("Рабочая точка УЭЦН в оптимальной зоне", value=True)
            st.form_submit_button("Установить параметры")
    return params, criterions
