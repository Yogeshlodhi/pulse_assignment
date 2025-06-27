from dateparser import parse

def is_within_range(date_str, start_date, end_date):
    parsed_date = parse(date_str)
    if not parsed_date:
        return False
    return start_date <= parsed_date.date() <= end_date

def normalize_date(date_str):
    parsed_date = parse(date_str)
    return parsed_date.date().isoformat() if parsed_date else None
