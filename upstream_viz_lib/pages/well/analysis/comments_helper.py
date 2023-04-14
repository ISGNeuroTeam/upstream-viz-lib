from upstream_viz_lib.common.comments import Comments
from upstream_viz_lib.config import get_data_conf
from pandas import DataFrame

from upstream_viz_lib.pages.well.analysis.static import format_all_comments

data_config = get_data_conf()
comments_path = data_config["comments"]
DEFAULT_COMMENT_SALT = 0


def load_comments():
    return Comments(
        source=comments_path,
        keys=["__deposit", "__well_num"],
        salt=DEFAULT_COMMENT_SALT
    )


def filter_comments_by_deposit_and_well_num(df_comments: DataFrame, deposit: str, well_num: str) -> DataFrame:
    """
    upstream-viz  upstream-viz/pages/well/analysis/comments_helper.py 26
    Filter dataframe by deposit name and well num
    Args:
        df_comments (DataFrame): comments dataframe
        deposit (str): deposit name
        well_num (int): well num
    Returns:
        DataFrame: filtered dataframe
    """
    well_filter = (df_comments["__deposit"] == deposit) & (df_comments["__well_num"] == well_num)
    df_well_comments = df_comments[well_filter]
    return df_well_comments
