"""
Tools to build subqueries that produce model instances
"""
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.functions import JSONObject


def _model_fields(model, fields):
    """
    Return a set of the field names for the given model. If fields is __all__
    then return all the declared fields.
    """
    # TODO: the pk/id field should always be returned
    declared = {f.name for f in model._meta.get_fields()}
    if fields is None:
        return declared

    assert declared.issuperset(fields)
    return declared.intersection(fields)


class JSONModelField(models.JSONField):
    """
    Instantiate an actual model instance from a JSON object containing its fields.
    Any missing fields in the JSON object are marked as "deferred" (and will be
    loaded from the db on access).
    """
    # TODO: support the "pk" alias
    # TODO: support fk fields (recursive __ access)
    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model_class = model

    def from_db_value(self, value, expression, connection):
        value = super().from_db_value(value, expression, connection)
        if value is None:
            return None
        return self.instantiate_model_from_db_dict(value)

    def instantiate_model_from_db_dict(self, dbdict):
        declared = _model_fields(self._model_class, None)
        missing = declared.difference(dbdict.keys())

        kwargs = {
            k: self._model_class._meta.get_field(k).to_python(v)
            for k, v in dbdict.items()
        }
        deferred = dict.fromkeys(missing, models.DEFERRED)
        return self._model_class(**kwargs, **deferred)


def model_to_json(model, path="", fields=None):
    """
    Return a JSONObject containing all the fields from the given model accessible
    at the given path (an empty path corresponds to the current queryset's model).
    """
    prefix = "" if not path else (path + LOOKUP_SEP)
    fields = _model_fields(model, fields)
    return JSONObject(**{field: prefix + field for field in fields})


def ModelSubquery(queryset, fields=None):
    """
    Return a subquery that when annotated will produce an actual instance of the
    queryset's model.
    All fields on the model are loaded by default, use `fields=...` to specify
    and iterable of the field names you'd like to load. The missing fields will
    be marked as deferred.
    """
    jsonobj = model_to_json(queryset.model, fields=fields)
    return models.Subquery(
        queryset.values_list(jsonobj),
        output_field=JSONModelField(queryset.model)
    )
