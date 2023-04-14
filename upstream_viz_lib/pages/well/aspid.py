import pandas as pd
import numpy as np
import os
from pandas import DataFrame
from scipy.optimize import least_squares

from upstream_viz_lib.common import otp
from upstream_viz_lib.common.logger import logger
from datetime import datetime, timedelta
import upstream_viz_lib.config as config
from upstream_viz_lib.pages.well.static.static_aspid import *


get_data_conf = config.get_data_conf()

niz_method_dict = {
    "NS": "Назарова - Сипачева",
    "SP": "Сипачева - Посевича"
}

niz_calc = {
    "least_squares": "scipy.least_squares",
    "mnk": "МНК"
}

well_aggregation = {
    "Нет": [False, False],
    "Усредненный": [QUERY_FOR_NIZ_ALL_WELLS_AVG, QUERY_GET_ALL_WELLS_AVG_INFO],
    "Суммарный": [QUERY_FOR_NIZ_ALL_WELLS_SUM, QUERY_GET_ALL_WELLS_SUM_INFO]
}


def update_static_data():
    try:
        query_wells = otp.render_query(
            QUERY_GET_ASPID_WELLS,
            {
                "__SOURCE__": get_data_conf["well"]["aspid"]
            }
        )
        wells = otp.get_data(query_wells)
        current_dir = os.path.dirname(os.getcwd())
        filepath = os.path.join(current_dir, 'upstream-viz', 'data', 'psn', 'aspid_wells.csv')
        wells.to_csv(filepath)
    except Exception as err:
        logger.error(str(err))


def get_well_data(well: str, all_wells: str) -> DataFrame:
    if all_wells:
        query_well_info = otp.render_query(
            all_wells,
            {
                "__SOURCE__": get_data_conf["well"]["aspid"]
            }
        )
    else:
        query_well_info = otp.render_query(
            QUERY_GET_WELL_INFO,
            {
                "__SOURCE__": get_data_conf["well"]["aspid"],
                "__PARAM__": f"{well}"
            }
        )
    df = otp.get_data(query_well_info)
    df['_time'] = df['month'].apply(lambda x: datetime.strptime(x, "%Y-%m"))
    return df


def fit_liquid(df_init, extrapolation, through_point, only_future, m):
    df, param = cut_dataframe(df_init, m, 'жидкости')
    Q_start = param[0]
    time_start = param[1]
    number_of_data = param[2]

    def liquid_func(x, a, b):
        return Q_start * (1 + a * b * (x - 1)) ** (-1 / b)

    time_end = df['_time'].max()
    Q_end = df[df['_time'] == time_end]['Объем жидкости']

    def liquid_fit_func(x, t, y):
        if through_point:
            x[0] = ((Q_end / Q_start) ** (-x[1]) - 1) / (x[1] * (number_of_data - 1))
        try:
            tt = (1 + x[0] * x[1] * (t - 1))
            l_res = Q_start * tt **(-1 / x[1]) - y
        except FloatingPointError: # workaround about floating point error
            l_res = Q_start * np.sign(tt) * np.abs(tt)**(-1 / x[1]) - y
        return l_res
    ydata = np.array(df[df['_time'] >= time_start]['Объем жидкости'])
    xdata = np.arange(1, ydata.size + 1)
    try:
        x0 = np.array([1.0, 1.0])
        res = least_squares(liquid_fit_func, x0, loss='soft_l1', ftol=1e-06, args=(xdata, ydata))
    except:
        logger.warning("Расчет жидкости: не удалось подобрать оптимальные параметры...")
        return pd.DataFrame()
    popt = res.x
    xdata_extra = np.arange(ydata.size + 1, ydata.size + 1 + extrapolation)
    future_time = []
    if only_future:
        fited_liquid = liquid_func(np.append(xdata[-1], xdata_extra), popt[0], popt[1])
        tdata = [list(df['_time'])[-1]]
    else:
        fited_liquid = liquid_func(np.append(xdata, xdata_extra), popt[0], popt[1])
        tdata = list(df[df['_time'] >= time_start]['_time'])
    for i in range(ydata.size + 1, ydata.size + 1 + extrapolation):
        future_time.append(tdata[-1] + timedelta(days=30))
        tdata.append(tdata[-1] + timedelta(days=30))
    return pd.DataFrame.from_dict({'_time': tdata, 'Объем жидкости': fited_liquid})

def get_liquid_param_df(df_init, through_point,m):
    df, param = cut_dataframe(df_init, m, 'жидкости')
    Q_start = param[0]
    time_start = param[1]
    number_of_data = param[2]

    time_end = df['_time'].max()
    Q_end = df[df['_time'] == time_end]['Объем жидкости']

    def liquid_fit_func(x, t, y):
        if through_point:
            x[0] = ((Q_end / Q_start) ** (-x[1]) - 1) / (x[1] * (number_of_data - 1))
        try:
            tt = (1 + x[0] * x[1] * (t - 1))
            l_res = Q_start * tt **(-1 / x[1]) - y
        except FloatingPointError: # workaround about floating point error
            l_res = Q_start * np.sign(tt) * np.abs(tt)**(-1 / x[1]) - y
        return l_res
    ydata = np.array(df[df['_time'] >= time_start]['Объем жидкости'])
    xdata = np.arange(1, ydata.size + 1)
    try:
        x0 = np.array([1.0, 1.0])
        res = least_squares(liquid_fit_func, x0, loss='soft_l1', ftol=1e-06, args=(xdata, ydata))
    except:
        logger.warning("Расчет жидкости: не удалось подобрать оптимальные параметры...")
        return pd.DataFrame.from_dict(
            {'k1': [0], 'k2': [0],
             'Начальный период': [time_start], 'Начальный дебит': [Q_start],
             'Успех расчета': [False]
            }
        )
    popt = res.x

    liquid_param = pd.DataFrame.from_dict(
            {'k1': [popt[0]], 'k2': [popt[1]],
             'Начальный период': [time_start.strftime('%Y-%m')], 'Начальный дебит': [Q_start],
             'Успех расчета': [res.success]}
        )
    return liquid_param

def get_future_liquid(df_init, extrapolation, through_point, only_future, m):
    df, param = cut_dataframe(df_init, m, 'жидкости')
    Q_start = param[0]
    time_start = param[1]
    number_of_data = param[2]

    def liquid_func(x, a, b):
        return Q_start * (1 + a * b * (x - 1)) ** (-1 / b)

    time_end = df['_time'].max()
    Q_end = df[df['_time'] == time_end]['Объем жидкости']

    def liquid_fit_func(x, t, y):
        if through_point:
            x[0] = ((Q_end / Q_start) ** (-x[1]) - 1) / (x[1] * (number_of_data - 1))
        try:
            tt = (1 + x[0] * x[1] * (t - 1))
            l_res = Q_start * tt **(-1 / x[1]) - y
        except FloatingPointError: # workaround about floating point error
            l_res = Q_start * np.sign(tt) * np.abs(tt)**(-1 / x[1]) - y
        return l_res
    ydata = np.array(df[df['_time'] >= time_start]['Объем жидкости'])
    xdata = np.arange(1, ydata.size + 1)
    try:
        x0 = np.array([1.0, 1.0])
        res = least_squares(liquid_fit_func, x0, loss='soft_l1', ftol=1e-06, args=(xdata, ydata))
    except:
        logger.warning("Расчет жидкости: не удалось подобрать оптимальные параметры...")
        return [[0, 0], Q_start, time_start, False]
    popt = res.x
    xdata_extra = np.arange(ydata.size + 1, ydata.size + 1 + extrapolation)
    future_liquid = liquid_func(xdata_extra, popt[0], popt[1])
    future_time = []
    if only_future:
        tdata = [list(df['_time'])[-1]]
    else:
        tdata = list(df[df['_time'] >= time_start]['_time'])
    for i in range(ydata.size + 1, ydata.size + 1 + extrapolation):
        future_time.append(tdata[-1] + timedelta(days=30))
        tdata.append(tdata[-1] + timedelta(days=30))

    return pd.DataFrame.from_dict({'_time': future_time, 'Объем жидкости': future_liquid})


def get_data_for_niz(df: DataFrame) -> DataFrame:
    res = df[['Объем жидкости', 'Объем нефти', 'Объем воды']].cumsum()
    res['Время'] = df['day'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d"))
    return res


def correlation(x, y):
    return ((x - x.mean()) * (y - y.mean())).sum() / np.sqrt(((x - x.mean()) ** 2).sum() * ((y - y.mean()) ** 2).sum())


def MNK(x, y):
    n = x.size
    delta = n * (x ** 2).sum() - (x.sum()) ** 2
    a = (n * (x * y).sum() - x.sum() * y.sum()) / delta
    b = ((x ** 2).sum() * y.sum() - x.sum() * (x * y).sum()) / delta
    return [a, b]


def niz_func(x, a, b):
    return a * x + b


def niz_fit_func(x, t, y):
    return x[0] * t + x[1] - y


def get_xdata_ydata(df: DataFrame, calc_method: str):
    if calc_method == "SP":
        xdata = np.array(df['Объем жидкости'])
        ydata = np.array(df['Объем жидкости'] / df['Объем нефти'])
    elif calc_method == "NS":
        xdata = np.array(df['Объем воды'])
        ydata = np.array(df['Объем жидкости'] / df['Объем нефти'])
    else:
        xdata = ydata = np.empty(len(df.index))

    xdata = xdata[~np.isnan(xdata)]
    ydata = ydata[~np.isnan(ydata)]
    return xdata, ydata


def calc_niz(df: DataFrame, calc_method: str, fit_method: str):
    xdata, ydata = get_xdata_ydata(df, calc_method)

    if fit_method == 'least_squares':
        try:
            x0 = np.array([1.0, 1.0])
            res = least_squares(niz_fit_func, x0, loss='soft_l1', ftol=1e-08, args=(xdata, ydata))
            popt = res.x
        except Exception as err:
            ydata_fit = f"Расчет НИЗ: не удалось подобрать оптимальные параметры...: {err}"
            return pd.DataFrame.from_dict(
                {
                    'xdata': xdata,
                    'ydata': ydata,
                    'ydata_fit': ydata_fit
                }
            )
    elif fit_method == 'mnk':
        popt = MNK(xdata, ydata)
    else:
        ydata_fit = f"Некорректный fit_method"
        return pd.DataFrame.from_dict(
            {
                'xdata': xdata,
                'ydata': ydata,
                'ydata_fit': ydata_fit
            }
        )

    ydata_fit = niz_func(xdata, popt[0], popt[1])

    return pd.DataFrame.from_dict(
        {
            'xdata': xdata,
            'ydata': ydata,
            'ydata_fit': ydata_fit
        }
    )


def calc_niz_params(df: DataFrame, calc_method: str, fit_method: str):
    xdata, ydata = get_xdata_ydata(df, calc_method)

    if fit_method == 'least_squares':
        try:
            x0 = np.array([1.0, 1.0])
            res = least_squares(niz_fit_func, x0, loss='soft_l1', ftol=1e-08, args=(xdata, ydata))
            popt = res.x
            success = res.success
        except Exception as err:
            niz_param = pd.DataFrame.from_dict(
                {'НИЗ': [np.abs(1 / -1)], 'Накопленная нефть': [df['Объем нефти'].max()],
                 'a': [-1], 'b': [-1], 'Корреляция': [-1],
                 'Успех расчета': [False]}
            )
            return niz_param
    elif fit_method == 'mnk':
        popt = MNK(xdata, ydata)
        success = True
    else:
        niz_param = pd.DataFrame.from_dict(
            {'НИЗ': [np.abs(1 / -1)], 'Накопленная нефть': [df['Объем нефти'].max()],
             'a': [-1], 'b': [-1], 'Корреляция': [-1],
             'Успех расчета': [False]}
        )
        return niz_param

    pcov = correlation(xdata, ydata)

    niz_param = pd.DataFrame.from_dict(
        {'НИЗ': [np.abs(1 / popt[0])], 'Накопленная нефть': [df['Объем нефти'].max()],
         'a': [popt[0]], 'b': [popt[1]], 'Корреляция': [pcov],
         'Успех расчета': [success]}
    )
    return niz_param


def fit_watercut(df_init, niz, extrapolation, only_future, m):
    df, param = cut_dataframe(df_init, m, 'обводненности')
    time_start = param[1]
    zdata = np.array(df[df['_time'] >= time_start]['Объем жидкости'])
    ydata = np.array(df[df['_time'] >= time_start]['Объем нефти'])
    xdata = np.arange(1, ydata.size + 1)

    xdata = xdata[~np.isnan(xdata)]
    ydata = ydata[~np.isnan(ydata)]


    def kory(x, a, b, c):
        return (1 - x) ** a / ((1 - x) ** a + c * x ** b)

    def fit_func(x, t, y):
        v1_list = []
        for i in t:
            temp = ydata[1:i].sum() / niz
            v1_list.append(temp)
        v1 = np.array(v1_list)
        k1 = kory(v1, x[0], x[1], x[2])
        v2 = v1 + zdata * k1 / 2 / niz
        k2 = kory(v2, x[0], x[1], x[2])
        v3 = v1 + zdata * k2 / 2 / niz
        k3 = kory(v3, x[0], x[1], x[2])
        v4 = v1 + zdata * k3 / 2 / niz
        k4 = kory(v4, x[0], x[1], x[2])
        return zdata * (k1 + 2 * k2 + 2 * k3 + k4) / 6 - y
    try:
        x0 = np.array([1.0, 1.0, 1.0])
        res = least_squares(fit_func, x0, loss='soft_l1', ftol=1e-06, args=(xdata, ydata))
        popt = res.x
    except:
        logger.warning("Расчем обводненности: не удалось определить оптимальные параметры...")
        return [[0, 0, 0], False]

    def watercut_func(x, a, b, c):
        RF_list = []
        for i in x:
            temp = ydata[1:i].sum() / niz
            RF_list.append(temp)
        RF = np.array(RF_list)
        return c * RF ** b / ((1 - RF) ** a + c * RF ** b)
    xdata_extra = np.arange(ydata.size + 1, ydata.size + 1 + extrapolation)
    future_time = []
    if only_future:
        fitdata= watercut_func(np.append(xdata[-1], xdata_extra), popt[0], popt[1], popt[2])
        tdata = [list(df['_time'])[-1]]
    else:
        fitdata= watercut_func(np.append(xdata, xdata_extra), popt[0], popt[1], popt[2])
        tdata = list(df[df['_time'] >= time_start]['_time'])
    for i in range(ydata.size + 1, ydata.size + 1 + extrapolation):
        future_time.append(tdata[-1] + timedelta(days=30))
        tdata.append(tdata[-1] + timedelta(days=30))
    return pd.DataFrame.from_dict({'_time': tdata, 'Обводненность': fitdata * 100})


def get_future_watercut(df_init, niz, extrapolation, only_future, m):
    df, param = cut_dataframe(df_init, m, 'обводненности')
    time_start = param[1]
    zdata = np.array(df[df['_time'] >= time_start]['Объем жидкости'])
    ydata = np.array(df[df['_time'] >= time_start]['Объем нефти'])
    xdata = np.arange(1, ydata.size + 1)

    xdata = xdata[~np.isnan(xdata)]
    ydata = ydata[~np.isnan(ydata)]


    def kory(x, a, b, c):
        return (1 - x) ** a / ((1 - x) ** a + c * x ** b)

    def fit_func(x, t, y):
        v1_list = []
        for i in t:
            temp = ydata[1:i].sum() / niz
            v1_list.append(temp)
        v1 = np.array(v1_list)
        k1 = kory(v1, x[0], x[1], x[2])
        v2 = v1 + zdata * k1 / 2 / niz
        k2 = kory(v2, x[0], x[1], x[2])
        v3 = v1 + zdata * k2 / 2 / niz
        k3 = kory(v3, x[0], x[1], x[2])
        v4 = v1 + zdata * k3 / 2 / niz
        k4 = kory(v4, x[0], x[1], x[2])
        return zdata * (k1 + 2 * k2 + 2 * k3 + k4) / 6 - y
    try:
        x0 = np.array([1.0, 1.0, 1.0])
        res = least_squares(fit_func, x0, loss='soft_l1', ftol=1e-06, args=(xdata, ydata))
        popt = res.x
    except:
        logger.warning("Расчем обводненности: не удалось определить оптимальные параметры...")
        return pd.DataFrame()

    def watercut_func(x, a, b, c):
        RF_list = []
        for i in x:
            temp = ydata[1:i].sum() / niz
            RF_list.append(temp)
        RF = np.array(RF_list)
        return c * RF ** b / ((1 - RF) ** a + c * RF ** b)
    xdata_extra = np.arange(ydata.size + 1, ydata.size + 1 + extrapolation)
    future_watercut = watercut_func(xdata_extra, popt[0], popt[1], popt[2])
    future_time = []
    if only_future:
        tdata = [list(df['_time'])[-1]]
    else:
        tdata = list(df[df['_time'] >= time_start]['_time'])
    for i in range(ydata.size + 1, ydata.size + 1 + extrapolation):
        future_time.append(tdata[-1] + timedelta(days=30))
        tdata.append(tdata[-1] + timedelta(days=30))

    return pd.DataFrame.from_dict({'_time': future_time, 'Обводненность': future_watercut * 100})


def get_watercut_param(df_init, niz, m):
    df, param = cut_dataframe(df_init, m, 'обводненности')
    time_start = param[1]
    zdata = np.array(df[df['_time'] >= time_start]['Объем жидкости'])
    ydata = np.array(df[df['_time'] >= time_start]['Объем нефти'])
    xdata = np.arange(1, ydata.size + 1)

    xdata = xdata[~np.isnan(xdata)]
    ydata = ydata[~np.isnan(ydata)]


    def kory(x, a, b, c):
        return (1 - x) ** a / ((1 - x) ** a + c * x ** b)

    def fit_func(x, t, y):
        v1_list = []
        for i in t:
            temp = ydata[1:i].sum() / niz
            v1_list.append(temp)
        v1 = np.array(v1_list)
        k1 = kory(v1, x[0], x[1], x[2])
        v2 = v1 + zdata * k1 / 2 / niz
        k2 = kory(v2, x[0], x[1], x[2])
        v3 = v1 + zdata * k2 / 2 / niz
        k3 = kory(v3, x[0], x[1], x[2])
        v4 = v1 + zdata * k3 / 2 / niz
        k4 = kory(v4, x[0], x[1], x[2])
        return zdata * (k1 + 2 * k2 + 2 * k3 + k4) / 6 - y
    try:
        x0 = np.array([1.0, 1.0, 1.0])
        res = least_squares(fit_func, x0, loss='soft_l1', ftol=1e-06, args=(xdata, ydata))
        popt = res.x
    except:
        logger.warning("Расчем обводненности: не удалось определить оптимальные параметры...")
        return pd.DataFrame.from_dict(
            {'corey_oil': [0], 'corey_water': [0],
             'm_ef': [0], 'Успех расчета': [False]}
        )

    watercut_param = pd.DataFrame.from_dict(
            {'corey_oil': [popt[0]], 'corey_water': [popt[1]],
             'm_ef': [popt[2]], 'Успех расчета': [res.success]}
        )
    return watercut_param

def fit_oil(df_init, liquid_param, watercut_param, niz, extrapolation, only_future, m):
    df, param = cut_dataframe(df_init, m, 'нефти')
    Q_start = param[0]
    time_start = param[1]
    ydata = np.array(df[df['_time'] >= time_start]['Объем нефти'])
    xdata = np.arange(1, ydata.size + 1)

    def liquid_func(x, a, b):
        return Q_start * (1 + a * b * (x - 1)) ** (-1 / b)

    def watercut_func(x, a, b, c):
        RF_list = []
        for i in x:
            temp = ydata[1:i].sum() / niz
            RF_list.append(temp)
        RF = np.array(RF_list)
        return c * RF ** b / ((1 - RF) ** a + c * RF ** b)
    xdata_extra = np.arange(ydata.size + 1, ydata.size + 1 + extrapolation)
    future_time = []
    if only_future:
        fited_liquid = liquid_func(np.append(xdata[-1], xdata_extra), liquid_param[0], liquid_param[1])
        fited_watercut = watercut_func(np.append(xdata[-1], xdata_extra),
                                       watercut_param[0], watercut_param[1], watercut_param[2])
        tdata = [list(df['_time'])[-1]]
    else:
        fited_liquid = liquid_func(np.append(xdata, xdata_extra), liquid_param[0], liquid_param[1])
        fited_watercut = watercut_func(np.append(xdata, xdata_extra),
                                       watercut_param[0], watercut_param[1], watercut_param[2])
        tdata = list(df[df['_time'] >= time_start]['_time'])
    for i in range(ydata.size + 1, ydata.size + 1 + extrapolation):
        future_time.append(tdata[-1] + timedelta(days=30))
        tdata.append(tdata[-1] + timedelta(days=30))
    oil = fited_liquid * (1 - fited_watercut)

    fit_df = pd.DataFrame.from_dict({'_time': tdata, 'Объем нефти': oil})
    return fit_df

def get_future_oil(df_init, liquid_param, watercut_param, niz, extrapolation, only_future, m):
    df, param = cut_dataframe(df_init, m, 'нефти')
    Q_start = param[0]
    time_start = param[1]
    ydata = np.array(df[df['_time'] >= time_start]['Объем нефти'])

    def liquid_func(x, a, b):
        return Q_start * (1 + a * b * (x - 1)) ** (-1 / b)

    def watercut_func(x, a, b, c):
        RF_list = []
        for i in x:
            temp = ydata[1:i].sum() / niz
            RF_list.append(temp)
        RF = np.array(RF_list)
        return c * RF ** b / ((1 - RF) ** a + c * RF ** b)
    xdata_extra = np.arange(ydata.size + 1, ydata.size + 1 + extrapolation)
    future_liquid = liquid_func(xdata_extra, liquid_param[0], liquid_param[1])
    future_watercut = watercut_func(xdata_extra, watercut_param[0], watercut_param[1], watercut_param[2])
    future_oil = future_liquid * (1 - future_watercut)
    future_time = []
    if only_future:
        tdata = [list(df['_time'])[-1]]
    else:
        tdata = list(df[df['_time'] >= time_start]['_time'])
    for i in range(ydata.size + 1, ydata.size + 1 + extrapolation):
        future_time.append(tdata[-1] + timedelta(days=30))
        tdata.append(tdata[-1] + timedelta(days=30))
    return pd.DataFrame.from_dict({'_time': future_time, 'Объем нефти': future_oil})

def cut_dataframe(df, m, calc_what):
    Q_start = df['Объем жидкости'].max()
    time_start = df[df['Объем жидкости'] == Q_start]['_time'].min()
    N = df[df['_time'] >= time_start]['Объем жидкости'].count()
    if (N < 4) or ((N - m > 0) and (N - m < 4)):
        logger.warning(f"Расчет {calc_what}: очень мало данных!!!")
        return df, [Q_start, time_start, N]
    if N - m <= 0:
        logger.warning(f"Расчет {calc_what}: слишком большой срез!!! => Нет данных для расчета")
        return df, [Q_start, time_start, N]
    if N - m >= 4:
        res = df[df['_time'] >= time_start]
        res.drop(res.tail(m).index, inplace=True)
        return res, [Q_start, time_start, N-m]


