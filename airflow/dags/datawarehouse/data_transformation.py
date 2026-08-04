from datetime import timedelta, datetime

def parse_duration(duration_str: str):
    # remove what we don't need
    duration_transformed = duration_str.replace("P", "").replace("T", "")

    components = ["D", "H", "M", "S"]

    values = {
        "D": 0,
        "H": 0,
        "M": 0,
        "S": 0
    }

    for c in components:
        if c in duration_str:
            value, duration_transformed = duration_transformed.split(c)
            values[c] = int(value)

    total_duration = timedelta(
        days=values["D"], hours=values["H"], minutes=values["M"], seconds=values["S"]
    )

    return total_duration

def transform_data(row):
    # this row is from the staging table/raw layer
    duration_td = parse_duration(row["Duration"])
    row["Duration"] = (datetime.min + duration_td).time()

    row["Video_Type"] = "Shorts" if duration_td.total_seconds() <= 60 else "Normal"

    return row