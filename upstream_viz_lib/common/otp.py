import re
import pandas as pd
from pandas.api.types import is_numeric_dtype, is_integer_dtype
from upstream_viz_lib.common.logger import logger
from upstream_viz_lib import config


def get_data(query: str, tws=0, twf=0, ttl=60) -> pd.DataFrame:
    return get_data_no_cache(query, tws, twf, ttl)


class QueryError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def get_data_no_cache(query: str, tws=0, twf=0, ttl=60) -> pd.DataFrame:
    """
    Run query on OT Platform.
    Return query result.
    Raise QueryError if cannot get result.
    """

    conn = config.get_rest_connector()
    logger.info(f"Run query: {query}")
    try:
        df = pd.DataFrame(
            conn.jobs.create(query, cache_ttl=ttl, tws=tws, twf=twf).dataset.load()
        )
        if "_time" in df.columns:
            df["dt"] = pd.to_datetime(df["_time"], unit="s")
    except Exception as err:
        raise QueryError(err)

    return df


def render_query(query_template: str, query_params: dict) -> str:
    """
    Replace tokens in query with query_params dict.

    :param query_template: Query template with tokens or placeholders.
    :param query_params: Dict with replacements.
    :return: Query ready to run.
    """
    return_query = query_template
    for k, v in query_params.items():
        return_query = return_query.replace(k, v)
    return return_query


def beta_render_query(query_template, options, token_prefix="__", token_suffix="__"):
    """Replace tokens in query with 'options' dict.
    Tokens descovered automatically with specified prefix and suffix.
    'Options' dict must contain keys with the same names as tokens (case-insensitive)."""

    def escape_chars(word: str):
        returned_word = word
        special_chars = """^$.|?*+()[]{}"""
        for char in special_chars:
            returned_word = returned_word.replace(char, f"""\\{char}""")
        return returned_word

    def wrap(word):
        prefix = escape_chars(token_prefix)
        suffix = escape_chars(token_suffix)
        logger.debug(f"Wrap word {word} with {prefix} and {suffix}")
        return f"{prefix}{word}{suffix}"

    # Collect all required tokens from query template. Check if all required tokens are in 'options' dict.
    regexp = wrap("(.+?)")
    required_keys = re.findall(regexp, query_template)
    is_missed = (k not in options.keys() for k in required_keys)
    if any(is_missed):
        raise KeyError(f"""Not enough params for query. 
        Required params: {required_keys}. 
        Received params: {options.keys()}""")

    query = query_template
    for key in required_keys:
        token = wrap(key)
        query = query.replace(token, str(options[key]))

    return query


def load_df(df: pd.DataFrame, path: str, write_format: str = "csv", mode: str = "overwrite"):
    """
    Send dataframe to OT Platform and write it to the external_data folder.
    Return result of corresponding OTL query
    """

    # If path was get from get_data.yaml, it likley contains 'path='
    path = get_path_from_string(path)

    cols_delimiter = "###"
    rows_delimiter = "&&&"

    rows = [
        cols_delimiter.join(str(v) for _, v in row.items())
        for row in df.to_dict(orient="records")
    ]

    df_as_string = rows_delimiter.join(rows)
    colnames = ",".join(col.replace(" ", "_") for col in df.columns)

    numeric_casts = []
    for col in df.columns:
        if is_numeric_dtype(df[col]):
            func = "floor" if is_integer_dtype(df[col]) else "tonumber"
            q = f"eval {col} = {func}({col})"
            numeric_casts.append(q)
    numeric_casts_joined = " | ".join(numeric_casts)

    query = f"""
        | makeresults count=1
        | eval _total_string = "{df_as_string}"
        | eval _split_string = split(_total_string, "{rows_delimiter}")
        | mvexpand _split_string
        | split _split_string cols={colnames} sep={cols_delimiter}
        | fields - _total_string, _split_string
        | {numeric_casts_joined}
        | repartition num=1
        | put mode={mode} format={write_format} path={path}
    """

    logger.info(f"Starting to write dataset: {path=}, {write_format=}, {mode=}")
    return get_data(query)


def get_path_from_string(string: str) -> str:
    return re.search("path=(.*?)(\s|$)", string).group(1) if "path=" in string else string
