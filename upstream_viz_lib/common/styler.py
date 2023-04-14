import dataclasses
import pandas as pd
import locale
from typing import List

locale.setlocale(locale.LC_ALL, "")

MIN_TABLE_HEIGHT = 500

query_comments = """
| #__SOURCE__# 
"""


class JsCode:
    def __init__(self, js_code: str):
        """Wrapper around a js function to be injected on gridOptions.
        code is not checked at all.
        set allow_unsafe_jscode=True on AgGrid call to use it.
        Code is rebuilt on client using new Function Syntax (https://javascript.info/new-function)

        Args:
            js_code (str): javascript function code as str
        """
        import re
        js_placeholder = "--x_x--0_0--"
        one_line_jscode = re.sub(r"\s+|\n+", " ", js_code)
        self.js_code = f"{js_placeholder}{one_line_jscode}{js_placeholder}"


def value_with_locale(value, precision: int = 0) -> str:
    return locale.format_string(f"%10.{precision}f", value, grouping=True).replace(",", " ")


@dataclasses.dataclass
class Formatter:
    short_name: str
    rus_name: str
    format: str = None


def style_df(df: pd.DataFrame, style_dict: dict):
    styles = __to_formatter(style_dict)
    cols = [f.short_name for f in styles if f.short_name in df.columns]
    rename_cols = {f.short_name: f.rus_name for f in styles}
    format_cols = {f.rus_name: f.format for f in styles if f.format}
    return df[cols].rename(rename_cols, axis=1).style.format(format_cols)


def __to_formatter(style_dict: dict) -> List[Formatter]:
    return [Formatter(k, v[0], v[1]) for k, v in style_dict.items()]


def get_highlighter_by_condition(condition, color):
    return JsCode(
        f"""
        function(params) {{
            color = "{color}";
            if (params.value {condition}) {{
                return {{
                    'backgroundColor': color
                }}
            }}
        }};
        """
    )


def get_numeric_style_with_precision(precision: int) -> dict:
    return {"type": ["numericColumn", "customNumericFormat"], "precision": precision}


PRECISION_ZERO = get_numeric_style_with_precision(0)
PRECISION_ONE = get_numeric_style_with_precision(1)
PRECISION_TWO = get_numeric_style_with_precision(2)
