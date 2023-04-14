from typing import Iterable, Dict, Tuple
from pandas import DataFrame, Series

from upstream_viz_lib.common.logger import logger
from upstream_viz_lib.common.comments import MergeCommentsError, Comments
from upstream_viz_lib.pages.well.analysis.criteria import criteria_list, get_criteria_by_id
from upstream_viz_lib.pages.well.analysis.static import format_analysis_table


def filter_well_daily_params_by_deposit(df: DataFrame, deposits: Iterable[str]) -> DataFrame:
    """
    # pages/well/analysis/render_analysis.py 39
    Filter well daily params table by deposits
    """
    deposit_filter = df["__deposit"].isin(deposits)
    return df[deposit_filter]


def join_comments(df: DataFrame, cmt: Comments):
    """
    # pages/well/analysis/render_analysis.py 59
    Merge DataFrame with comments
    """
    try:
        df = cmt.merge_comments(df)
    except MergeCommentsError as err:
        logger.error(err.message)
    return df


def get_all_dfs(df) -> Dict[str, Tuple[DataFrame, dict]]:
    """
    # pages/well/analysis/render_analysis.py 116
    Calculates dataframes for all criteria.
    Returns dict: key = criteria name, value = tuple(filtered dataframe, formatter for AgGrid.
    """

    all_dfs = {}
    for c in criteria_list:
        df_crit = df.query(c.formula) if c.formula is not None else df
        all_dfs[c.name] = (df_crit, format_analysis_table)
    return all_dfs


def get_recommendations(_df: DataFrame, _criteria: str, _well_period: int) -> Series:
    """
    # pages/well/analysis/render_analysis.py 138
    Adds recommendation column to dataframe
    Args:
        _df (DataFrame): daily well params dataframe
        _criteria (str): criteria id
        _well_period (int): well period

    Returns:
        Dataframe with recommend column
    """
    selected_criteria = get_criteria_by_id(_criteria)
    func, kwargs = selected_criteria.function, selected_criteria.kwargs
    kwargs["period"] = _well_period
    return _df.apply(lambda x: func(x, **kwargs), axis=1)
