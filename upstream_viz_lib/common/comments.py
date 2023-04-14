import re
from datetime import datetime
from typing import Optional

import numpy as np
from pandas import DataFrame

from upstream_viz_lib.common import otp
from upstream_viz_lib.common.logger import logger
from upstream_viz_lib.common.otp import QueryError

COMMENT_COLS = ["comment", "comment_plan_event", "comment_completed_event"]
SERVICE_COLS = ["_time", "source", "user"]


class MergeCommentsError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SaveCommentsError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Comments:
    def __init__(self, source: str, keys: list = None, salt: int = 0):
        self.source = source
        self.keys = ["__deposit"] if keys is None else keys
        self.salt = salt

        self.get_last_comments_query = f"""
        | {source}
        | eval salt = {self.salt}
        | eval day = strftime(_time, "%d.%m.%y")
        | foreach comment* [ | eval <<FIELD>> = if(<<FIELD>>="-", null, day + ": " + <<FIELD>>) ]
        | sort _time
        | eval filldown_group = md5({' + '.join(keys)})
        | filldown comment, comment_plan_event, comment_completed_event by filldown_group
        | latestrow _time=_time by filldown_group
        | stats count, min(*) as * by _time, filldown_group
        """

        self.get_all_comments_query = f"""
        | {source}
        | eval salt = {self.salt}
        | eval time = strftime(_time, "%Y-%m-%d %H:%M")
        | sort _time
        """

        self.df_comments: Optional[DataFrame] = self.get_data()
        self.path: str = self.get_path_from_source()

    def get_path_from_source(self) -> str:
        return re.search("path=(.*?)(\s|$)", self.source).group(1) if "path=" in self.source else self.source

    def get_data(self) -> Optional[DataFrame]:
        try:
            _df = otp.get_data(self.get_last_comments_query)
            logger.debug(f"Load df_comments:\n{_df.to_markdown(index=False)}")
            return _df
        except Exception as err:
            logger.error(f"Failed to read dataset from query: {err}")
            return None

    def get_all_comments(self):
        return otp.get_data(self.get_all_comments_query)

    def merge_comments(self, df: DataFrame) -> DataFrame:
        if any(col for col in self.keys if col not in df.columns):
            msg = f"Not enough columns to join. Columns in join: {self.keys}, column in dataframe: {df.columns}"
            raise MergeCommentsError(msg)

        try:
            return df.merge(self.df_comments, how="left", on=self.keys)
        except Exception as err:
            logger.error(err)
            raise MergeCommentsError(err)

    @staticmethod
    def remove_dates(s: str) -> str:
        """Removes patterns like '02.12.2022: ' from comments"""

        groups = re.findall("\d{2}\.\d{2}\.\d{2}:\s", s)
        return s.replace(''.join(groups), "")

    def save_comments(self, df_new_comments: DataFrame, source: str, user: str) -> Optional[DataFrame]:
        cols = self.keys + COMMENT_COLS

        # New df  must contain _time + columns from `self.keys
        if any(col not in df_new_comments.columns for col in self.keys):
            msg = f"Not enough required columns. Required columns: {self.keys}, " \
                  f"column in dataframe: {df_new_comments.columns}"
            logger.error(msg)
            raise SaveCommentsError(msg)

        # if one or more comment_cols does not exist in df_new_comments, create them and fill them with np.nan
        for col in COMMENT_COLS:
            if col not in df_new_comments.columns:
                df_new_comments[col] = ""

        # Remove rows with no commments: all comment* fields are in ("-", "", na)
        _df: DataFrame = df_new_comments[cols]
        _df[COMMENT_COLS] = _df[COMMENT_COLS].replace(["-", ""], np.nan)
        _df = (
            _df
            .dropna(how="all", subset=COMMENT_COLS)
            .fillna("-")
        )

        # Compare with loaded df_comments, keep only changed rows
        try:
            _df = (
                _df
                .merge(self.df_comments[cols].assign(existed=True), how="left", on=cols)
                .query("existed.isna()")
                .drop("existed", axis=1)
            )
        except Exception as err:
            logger.error(err)
            raise SaveCommentsError(err)

        # Add _time, source, and user columns
        _df["_time"] = int(datetime.now().timestamp())
        _df["source"] = source
        _df["user"] = user

        # Remove leading dates from comments
        for col in COMMENT_COLS:
            _df[col] = _df[col].apply(self.remove_dates)

        write_cols = cols + SERVICE_COLS

        # Write changed rows in append mode.
        try:
            df_to_save = _df[write_cols]
            logger.debug(f"Dataframe with new comments to append:\n{df_to_save.to_markdown(index=False)}")
            return otp.load_df(df_to_save, path=self.path, write_format="parquet", mode="append")
        except QueryError as e:
            logger.error(f"Cannot save comments due to error in query execution: {e}")
            raise SaveCommentsError(e)
