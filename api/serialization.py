from datetime import date, datetime
from decimal import Decimal


HIDDEN_FIELDS = {"contrasena_hash"}


def serialize_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def model_to_dict(model):
    if model is None:
        return None
    return {
        column.name: serialize_value(getattr(model, column.name))
        for column in model.__table__.columns
        if column.name not in HIDDEN_FIELDS
    }


