import typing

import strawberry
import strawberry_django
from django.db.models import ManyToManyField
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry import auto

from . import models
from dataclasses import make_dataclass, field
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
DEPTH = 10

def _plural_from_single(s):
    return s.rstrip('y') + 'ies' if s.endswith('y') else s + 's'


def create_strawberry_model(fields_for_class, fields_for_filter, strawberry_model_name, django_model):
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
    wrapper = strawberry_django.type(model=django_model, filters=new_filter_dataclass, order=order_model,
                                     pagination=True)

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


def create_new_strawberry_models(
    models_fields_dict,
    filter_fields_dict,
    counter
):
    final_models_list = []
    new_dict_models_straw_models_setup = {}
    new_dict_models_straw_filter_setup = {}
    for model, fields in models_fields_dict.items():
        filter_fields = filter_fields_dict[model]
        model_name = model.__name__
        if DEPTH-counter != 0:
            model_name += str(DEPTH-counter)

        wrapped_model, wrapped_filter, wrapped_order = create_strawberry_model(
            fields_for_class=fields,
            fields_for_filter=filter_fields,
            strawberry_model_name=model_name,
            django_model=model,
        )
        final_models_list.append(wrapped_model)
        new_dict_models_straw_models_setup[model] = wrapped_model
        new_dict_models_straw_filter_setup[model] = wrapped_filter
    return new_dict_models_straw_models_setup, new_dict_models_straw_filter_setup, final_models_list


def add_layer_to_fields(
        strawberry_models,
        strawberry_filters,
        models_fields_dict,
        filter_fields_dict
):
    for model in models_fields_dict.keys():
        for model_field in model._meta.get_fields():
            relation = model_field.__dict__.get('related_model', None)
            if relation:
                related_model = model_field.related_model
                straw_model = strawberry_models[related_model]
                straw_filter = strawberry_filters[related_model]
                is_many_to_many = isinstance(model_field, ManyToManyField)
                if is_many_to_many or model_field.__dict__.get('multiple'):
                    models_fields_dict[model][model_field.name] = List[straw_model]
                else:
                    models_fields_dict[model][model_field.name] = straw_model
                filter_fields_dict[model][model_field.name] = typing.Optional[straw_filter]
            else:
                filter_fields_dict[model][model_field.name] = auto
    return models_fields_dict, filter_fields_dict


# app_models = django.apps.apps.get_models()
app_models = [models.Fruit, models.Recipe, models.Color, models.Shape]
models_list = []
lowercase_list = []

dict_models_fields_setup = {}
dict_models_straw_filter_setup = {}
dict_models_straw_models_setup = {}
dict_filter_fields_setup = {}

# CREATE DUMMY STRAWBERY MODELS
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


def make_schema_depth(
    dict_models_straw_models_setup,
    dict_models_straw_filter_setup,
    dict_models_fields_setup,
    dict_filter_fields_setup
):
    counter = 1
    while counter<=DEPTH:
        dict_models_fields_setup, dict_filter_fields_setup = add_layer_to_fields(
            dict_models_straw_models_setup,
            dict_models_straw_filter_setup,
            dict_models_fields_setup,
            dict_filter_fields_setup
        )
        print(dict_models_straw_filter_setup)
        dict_models_straw_models_setup,dict_models_straw_filter_setup, final_models_list = create_new_strawberry_models(
            dict_models_fields_setup,
            dict_filter_fields_setup,
            counter
        )
        counter+=1

    return final_models_list


final_models_list = make_schema_depth(
    dict_models_straw_models_setup,
    dict_models_straw_filter_setup,
    dict_models_fields_setup,
    dict_filter_fields_setup
)
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
