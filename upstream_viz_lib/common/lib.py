import io
from typing import Any
import pandas as pd
from pandas import DataFrame


def dataframes_to_excel(dfs: dict):
    """Ex.: {"Анализ фонда": (df, formatter), "Перевод в КЭС": (df1, formatter1), ...}"""
    output = io.BytesIO()
    writer = pd.ExcelWriter(output)

    for sheet_name, (df, formatter) in dfs.items():
        df = prepare_df(df, formatter)
        sheet_name_cropped = sheet_name[:31]  # name of Excel sheet cannot be longer than 31 chars
        df.to_excel(writer, index=False, sheet_name=sheet_name_cropped)
        writer = adjust_column_widths(writer, sheet_name_cropped, df)

    writer.save()
    return output.getvalue()


def dataframe_to_excel(df: pd.DataFrame, format_dict=None, sheet_name: str = "Анализ фонда"):
    output = io.BytesIO()

    df = prepare_df(df, format_dict)
    writer = pd.ExcelWriter(output)
    sheet_name_cropped = sheet_name[:31]  # name of Excel sheet cannot be longer than 31 chars
    df.to_excel(writer, index=False, sheet_name=sheet_name_cropped)

    writer = adjust_column_widths(writer, sheet_name_cropped, df)
    writer.save()
    return output.getvalue()


def prepare_df(df: DataFrame, format_dict: dict) -> DataFrame:
    """Rename and filter columns, round values"""

    if format_dict is None:
        return df

    rename_dict = {}
    cols = []
    for k, (new_name, formatter) in format_dict.items():
        if k in df.columns:
            cols.append(k)
            if "precision" in formatter:
                df[k] = df[k].apply(lambda x: safe_round(x, formatter["precision"]))

        rename_dict[k] = new_name

    return df[cols].rename(rename_dict, axis=1)


def adjust_column_widths(writer, sheet_name_cropped, df):
    """Autoadjust column widths
    Credits: https://stackoverflow.com/a/40535454"""

    worksheet = writer.sheets[sheet_name_cropped]
    for idx, col in enumerate(df.columns):
        series = df[col]
        max_len = max(
            series.astype(str).map(len).max(),  # len of the longest item
            len(str(series.name)),  # len of the column name
        ) + 2
        worksheet.set_column(idx, idx, max_len)  # 'xlsxwriter' lib required
    return writer


def safe_round(value: Any, precision: int = 0) -> Any:
    try:
        numeric_val = float(value)
        return round(numeric_val, precision)
    except ValueError as _:
        return value
