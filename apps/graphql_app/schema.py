import typing

import strawberry
import strawberry_django
from django.db.models import ManyToManyField
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry import auto

from . import models
from dataclasses import  make_dataclass, field
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
    # FILTER
    new_filter_dataclass = type(f"{strawberry_model_name}Filter", (), {'__annotations__': fields_for_filter})

    filters = strawberry_django.filter(django_model, lookups=True)
    filter_model = filters(new_filter_dataclass)

    # ORDER
    new_ordering_dataclass = type(f"{strawberry_model_name}Order", (), {'__annotations__': fields_for_filter})
    order = strawberry_django.order(model=django_model)
    order_model = order(new_ordering_dataclass)


    # FINAL DATA CLASS
    wrapper = strawberry_django.type(model=django_model, filters=new_filter_dataclass, order=order_model, pagination=True)

    return wrapper(new_dataclass), filter_model, order_model


def create_fields(model, set_relations=False):

    model_name = model.__name__
    if not set_relations:
        model_name = f"{model_name}SetupForRelations"

    model_fields = model._meta.get_fields()
    fields_for_class = {}
    fields_for_filter = {}
    for model_field in model_fields:
        relation = model_field.__dict__.get('related_model', None)
        # if not relation:
        #     fields_for_class.update({model_field.name: auto})
        fields_for_filter.update({model_field.name: auto})
        fields_for_class.update({model_field.name: auto})
    return fields_for_class, fields_for_filter, model_name


app_models = django.apps.apps.get_models()
# app_models = [models.Fruit, models.Recipe, models.Color, models.Shape]
models_list = []
lowercase_list = []

dict_models_fields_setup = {}
dict_models_straw_filter_setup = {}
dict_models_straw_models_setup = {}
dict_filter_fields_setup = {}


#CREATE DUMMY STRAWBERY MODELS
for model in app_models:
    fields_for_class, fields_for_filter, model_name = create_fields(model, set_relations=False)
    dict_models_fields_setup[model] = fields_for_class
    dict_filter_fields_setup[model] = fields_for_filter
    wrapped_model, wrapped_filter, wrapped_order = create_strawberry_model(
        fields_for_class=fields_for_class,
        fields_for_filter=fields_for_filter,
        strawberry_model_name=model_name,
        django_model=model,
    )
    dict_models_straw_models_setup[model] = wrapped_model
    dict_models_straw_filter_setup[model] = wrapped_filter
    models_list.append(wrapped_model)
    lowercase_list.append(model._meta.model_name)

# MAKING STRAWBERRY DUMMIES INTERACT BY RELATIONS
for model in dict_models_fields_setup.keys():
    for model_field in model._meta.get_fields():
        relation = model_field.__dict__.get('related_model', None)
        if relation:
            related_model = model_field.related_model
            straw_model = dict_models_straw_models_setup[related_model]
            straw_filter = dict_models_straw_filter_setup[related_model]
            is_many_to_many = isinstance(model_field, ManyToManyField)
            if is_many_to_many or model_field.__dict__.get('multiple'):
                dict_models_fields_setup[model][model_field.name] = List[straw_model]
            else:
                dict_models_fields_setup[model][model_field.name] = straw_model
            dict_filter_fields_setup[model][model_field.name] = typing.Optional[straw_filter]
        else:
            dict_filter_fields_setup[model][model_field.name] = auto

# PREPARING MODELS TO BE INSERTED IN QUERY
final_models_list = []
for model, fields in dict_models_fields_setup.items():
    filter_fields = dict_filter_fields_setup[model]
    fields_for_class, fields_for_filter, model_name = create_fields(model, set_relations=True)
    wrapped_model,_,_ = create_strawberry_model(
        fields,
        filter_fields,
        model_name,
        model
    )
    final_models_list.append(wrapped_model)


# FORM QUERY AND SCEMA
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
