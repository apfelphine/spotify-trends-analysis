from app.models.trends import TrendEntry


def add_date_filter(statement, from_date, to_date):
    if from_date is not None:
        statement = statement.where(TrendEntry.date >= from_date)
    if to_date is not None:
        statement = statement.where(TrendEntry.date <= to_date)
    return statement
