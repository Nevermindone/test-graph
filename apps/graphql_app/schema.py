import dataclasses

import strawberry
import strawberry_django
from django.db.models import ForeignKey
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry import auto

from . import models
# from .types import Fruit, Color
from dataclasses import dataclass, make_dataclass, asdict, field
import django.apps
from typing import List


# @strawberry.type
# class Query:
#     fruits: list[Fruit] = strawberry_django.field()
#     # fruit: Fruit = strawberry_django.field()
#     # color: Color = strawberry_django.field()
#
#
# schema = strawberry.Schema(
#     query=Query,
#     extensions=[
#         DjangoOptimizerExtension,  # not required, but highly recommended
#     ],
# )

"""

DEVELOPMENT

"""





def _plural_from_single(s):
    return s.rstrip('y') + 'ies' if s.endswith('y') else s + 's'


def model_to_dataclass(model, set_relations=False):

    model_name = model.__name__
    if not set_relations:
        model_name = f"{model_name}Relation"

    model_fields = model._meta.fields
    fields_for_class = {}
    fields_for_filter = {}
    for model_field in model_fields:
        relation = model_field.__dict__.get('related_model', None)
        if relation and set_relations:
            fields_for_class.update(
                {model_field.name: wrapped_models_dict[model_field.__dict__['related_model'].__name__]}
            )
        else:
            fields_for_class.update({model_field.name: auto})
            fields_for_filter.update({model_field.name: auto})
    # CREATING CLASSES FOR DATA, FILTERS, PAGINATION AND SORTING
    new_dataclass = type(model_name, (), {'__annotations__': fields_for_class})
    new_filter_dataclass = type(f"{model_name}Filter", (), {'__annotations__': fields_for_filter})
    new_ordering_dataclass = type(f"{model_name}Order", (), {'__annotations__': fields_for_filter})
    # FILTER
    filters = strawberry_django.filter(model=model, lookups=True)
    filter_model = filters(new_filter_dataclass)
    # ORDER
    order = strawberry_django.order(model=model)
    order_model = order(new_ordering_dataclass)
    # FINAL DATA CLASS
    wrapper = strawberry_django.type(model=model, filters=filter_model, order=order_model, pagination=True)

    return wrapper(new_dataclass), {model.__name__: wrapper(new_dataclass)}


app_models = django.apps.apps.get_models()
models_list = []
lowercase_list = []
wrapped_models_dict = {}

for model in app_models:
    wrapped_model, wrapped_model_dict = model_to_dataclass(model)
    models_list.append(wrapped_model)
    lowercase_list.append(model._meta.model_name)
    wrapped_models_dict.update(wrapped_model_dict)

models_list = []
for model in app_models:
    wrapped_model, _ = model_to_dataclass(model, set_relations=True)
    models_list.append(wrapped_model)

list_of_tuples_for_query = []
for index in range(len(lowercase_list)):
    filed_name = _plural_from_single(lowercase_list[index])
    field_type = List[models_list[index]]
    list_of_tuples_for_query.append((filed_name, field_type, field(default=strawberry_django.field())))
wrapper_func = strawberry.type
Query = make_dataclass("Query", list_of_tuples_for_query)
wrapped_query = wrapper_func(Query)


schema = strawberry.Schema(
    query=wrapped_query,
    extensions=[
        DjangoOptimizerExtension,  # not required, but highly recommended
    ],
)
