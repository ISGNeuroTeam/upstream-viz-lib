from datetime import date, timedelta, datetime


from upstream_viz_lib.config import get_data_conf

actual_at_conf: str = get_data_conf().get("actual_at", "today")


def get_actual_date(date_conf: str) -> date:
    """
    Returns the last timestamp of the correct data in storage.
    This timestamp is specified in get_data.yaml.

    :param date_conf:
        date[str] from config file
    :return:
    """
    if date_conf == "today":
        return date.today()
    elif date_conf == "yesterday":
        return date.today() - timedelta(days=1)
    else:
        return datetime.strptime(date_conf, "%Y-%m-%d").date()



