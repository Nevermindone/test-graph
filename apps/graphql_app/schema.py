import dataclasses

import strawberry
import strawberry_django
from django.db.models import ManyToManyField
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry import auto

from . import models
from .types import Fruit, Recipe
from dataclasses import dataclass, make_dataclass, asdict, field
import django.apps
from typing import List


# @strawberry.type
# class Query:
#     fruits: List[Fruit] = strawberry_django.field()
#     recipes: List[Recipe] = strawberry_django.field()
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


def create_strawberry_model(fields_for_class, fields_for_filter,  strawberry_model_name, django_model):
    new_dataclass = type(strawberry_model_name, (), {'__annotations__': fields_for_class})
    new_filter_dataclass = type(f"{strawberry_model_name}Filter", (), {'__annotations__': fields_for_filter})
    new_ordering_dataclass = type(f"{strawberry_model_name}Order", (), {'__annotations__': fields_for_filter})
    # FILTER
    filters = strawberry_django.filter(model=django_model, lookups=True)
    filter_model = filters(new_filter_dataclass)
    # ORDER
    order = strawberry_django.order(model=django_model)
    order_model = order(new_ordering_dataclass)
    # FINAL DATA CLASS
    wrapper = strawberry_django.type(model=django_model, filters=filter_model, order=order_model, pagination=True)

    return wrapper(new_dataclass), {django_model.__name__: wrapper(new_dataclass)}


def create_fields(model, set_relations=False):

    model_name = model.__name__
    if not set_relations:
        model_name = f"{model_name}SetupForRelations"

    model_fields = model._meta.get_fields()
    fields_for_class = {}
    fields_for_filter = {}
    for model_field in model_fields:
        relation = model_field.__dict__.get('related_model', None)

        is_many_to_many = isinstance(model_field, ManyToManyField)
        if relation and set_relations and not is_many_to_many:
            fields_for_class.update(
                {model_field.name: wrapped_models_dict[model_field.__dict__['related_model'].__name__]}
            )
        elif relation and set_relations and is_many_to_many:
            fields_for_class.update(
                {model_field.name: List[wrapped_models_dict[model_field.__dict__['related_model'].__name__]]}
            )
        else:
            fields_for_class.update({model_field.name: auto})
            fields_for_filter.update({model_field.name: auto})

    return fields_for_class, fields_for_filter, model_name


app_models = django.apps.apps.get_models()
# app_models = [models.Fruit, models.Recipe, models.Color, models.Shape]
models_list = []
lowercase_list = []
wrapped_models_dict = {}
many_to_many_backwards = []

dict_models_fields_setup = {}
dict_models_straw_models_setup = {}
dict_models_fields_filters = {}

for model in app_models:
    fields_for_class, fields_for_filter, model_name = create_fields(model, set_relations=False)
    dict_models_fields_setup[model] = fields_for_class
    dict_models_fields_filters[model] = fields_for_filter
    wrapped_model, wrapped_model_dict = create_strawberry_model(
        fields_for_class=fields_for_class,
        fields_for_filter=fields_for_filter,
        strawberry_model_name=model_name,
        django_model=model,
    )
    dict_models_straw_models_setup[model] = wrapped_model
    models_list.append(wrapped_model)
    lowercase_list.append(model._meta.model_name)
    wrapped_models_dict.update(wrapped_model_dict)

for model in dict_models_fields_setup.keys():
    for model_field in model._meta.get_fields():
        relation = model_field.__dict__.get('related_model', None)

        if relation:
            related_model = model_field.related_model
            straw_model = dict_models_straw_models_setup[related_model]
            dict_models_fields_setup[model][model_field.name] = List[straw_model]

dict_models_fields_final = {}
dict_models_straw_models_final = {}
final_models_list = []
for model, fields in dict_models_fields_setup.items():
    fields_for_class, fields_for_filter, model_name = create_fields(model, set_relations=False)
    wrapped_model, wrapped_model_dict = create_strawberry_model(
        fields,
        dict_models_fields_filters[model],
        model.__name__,
        model
    )
    dict_models_straw_models_final
    final_models_list.append(wrapped_model)



list_of_tuples_for_query = []
for index in range(len(lowercase_list)):
    filed_name = _plural_from_single(lowercase_list[index])
    field_type = List[final_models_list[index]]
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
