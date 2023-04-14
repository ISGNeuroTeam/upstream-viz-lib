from typing import Dict, List, Optional


def render_agg_query(value_field: str, dimensions: Optional[List[str]] = None) -> dict:
    """
    # pages/common/widgets/chart_options.py 8
    Render three otl aggregation queries
    Args:
        value_field (str): column name to calculate aggregation
        dimensions: list of columns used as dimensions
    Returns:
        dict: Dictionary with queries
    """
    dims_as_str = ", ".join(dimensions) if dimensions is not None else ""
    agg_query = f"""
     eval _time = 3600 * floor(_time / 3600) 
    | stats $func$({value_field}) as {value_field} by _time, metric_long_name {dims_as_str}
    """

    aggregations: Dict[str, str] = {
        "Исходные значения": "",
        "Среднее за час": agg_query.replace("$func$", "mean"),
        "Максимум за час": agg_query.replace("$func$", "max"),
        "Минимум за час": agg_query.replace("$func$", "min"),
    }
    return aggregations

