from pandas import DataFrame

from upstream_viz_lib.pages.well.analysis.beautify import is_different_modes


def filter_only_diffs(df_compare: DataFrame):
    """
    # pages/well/analysis/render_compare.py 48
    Filter dataframe by condition df["predict_mode_str"] != df["shtr_mode"]
    Args:
        df_compare (): tech regimes dataframe
    Returns:
        Filtered Dataframe
    """
    return df_compare[is_different_modes(df_compare)]
