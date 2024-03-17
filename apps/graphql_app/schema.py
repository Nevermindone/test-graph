import dataclasses

import strawberry
import strawberry_django
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


def model_to_dataclass(model):
    model_fields = model._meta.fields
    fields_for_class = {}
    fields_for_filter = {}
    for model_field in model_fields:
        relation = model_field.__dict__.get('related_model', None)
        if relation:
            # fields_for_class.update({model_field.name: list[str(relation.__name__)]})
            # print(relation.__name__)
            fields_for_class.update({model_field.name: auto})
        else:
            fields_for_class.update({model_field.name: auto})
            fields_for_filter.update({model_field.name: auto})
    # CREATING CLASSES FOR DATA, FILTERS, PAGINATION AND SORTING
    new_dataclass = type(model.__name__, (), {'__annotations__': fields_for_class})
    new_filter_dataclass = type(f"{model.__name__}Filter", (), {'__annotations__': fields_for_filter})
    new_ordering_dataclass = type(f"{model.__name__}Order", (), {'__annotations__': fields_for_filter})
    # FILTER
    filters = strawberry_django.filter(model=model, lookups=True)
    filter_model = filters(new_filter_dataclass)
    # ORDER
    order = strawberry_django.order(model=model)
    order_model = order(new_ordering_dataclass)
    # FINAL DATA CLASS
    wrapper = strawberry_django.type(model=model, filters=filter_model, order=order_model, pagination=True)

    return wrapper(new_dataclass)


app_models = django.apps.apps.get_models()
print(app_models)
models_list = []
lowercase_list = []

for model in app_models:
    wrapped_model = model_to_dataclass(model)
    import sys

    # this = sys.modules[__name__]
    # this.model._meta.model_name = wrapped_model
    models_list.append(wrapped_model)
    lowercase_list.append(model._meta.model_name)

list_of_tuples_for_query = []
for index in range(len(lowercase_list)):
    filed_name = _plural_from_single(lowercase_list[index])
    field_type = List[models_list[index]]
    list_of_tuples_for_query.append((filed_name, field_type, field(default=strawberry_django.field())))
wrapper_func = strawberry.type
Query = make_dataclass("Query", list_of_tuples_for_query)
wrapped_query = wrapper_func(Query)

# class Fruit:
#     id: auto
#     name: auto
#     color: 'Color'
#     shape: auto
#
# class Color:
#     id: auto
#     name: auto
#     fruits: 'Fruit'
#
#
# wrapper_func = strawberry_django.type(model=models.Fruit)
# fruit_wrapped = wrapper_func(Fruit)
# wrapper_func = strawberry_django.type(model=models.Color)
# color_wrapped = wrapper_func(Color)
# print(color_wrapped.__dict__)
#
#
# @strawberry.type
# class Query:
#     fruits: list[fruit_wrapped] = strawberry_django.field()
#     # fruit: Fruit = strawberry_django.field()
#     color: list[color_wrapped] = strawberry_django.field()


schema = strawberry.Schema(
    query=wrapped_query,
    extensions=[
        DjangoOptimizerExtension,  # not required, but highly recommended
    ],
)
