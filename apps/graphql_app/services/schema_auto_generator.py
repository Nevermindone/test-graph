import typing
from collections import defaultdict
from dataclasses import make_dataclass
from typing import List

import django.apps
import strawberry
import strawberry_django
from django.db.models import ManyToManyField
from strawberry import auto, field
from strawberry_django.optimizer import DjangoOptimizerExtension

from apps.graphql_app import models
from apps.graphql_app.helpers import _plural_from_single


class SchemaAutoGenerator:
    DEPTH = 10

    def __init__(self):
        self.app_models = django.apps.apps.get_models()
        # self.app_models = [models.Fruit, models.Recipe, models.Color, models.Shape]

    def make_schema(self):
        models_list = []
        lowercase_list = []

        dict_models_straw_filter_setup = {}
        dict_models_straw_models_setup = {}
        dict_models_straw_order_setup = {}
        dict_models_fields_setup = {}
        dict_filter_fields_setup = {}
        dict_orders_fields_setup = {}

        # CREATE DUMMY STRAWBERY MODELS
        for model in self.app_models:
            fields_for_class, fields_for_filter, fields_for_order, model_name = self._create_fields(model, set_relations=False)
            dict_models_fields_setup[model] = fields_for_class
            dict_filter_fields_setup[model] = fields_for_filter
            dict_orders_fields_setup[model] = fields_for_filter
            wrapped_model, wrapped_filter, wrapped_order = self._create_strawberry_model(
                fields_for_class=fields_for_class,
                fields_for_filter=fields_for_filter,
                fields_for_order=fields_for_order,
                strawberry_model_name=model_name,
                django_model=model,
            )
            dict_models_straw_models_setup[model] = wrapped_model
            dict_models_straw_filter_setup[model] = wrapped_filter
            dict_models_straw_order_setup[model] = wrapped_order
            models_list.append(wrapped_model)
            lowercase_list.append(model._meta.model_name)

        # MAKING STRAWBERRY DUMMIES INTERACT BY RELATIONS
        final_models_list = self._make_schema_depth(
            dict_models_straw_models_setup,
            dict_models_straw_filter_setup,
            dict_models_straw_order_setup,
            dict_models_fields_setup,
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
        return schema

    @staticmethod
    def _create_fields(model, set_relations=False):
        model_name = model.__name__
        if not set_relations:
            model_name = f"{model_name}SetupForRelations"

        model_fields = model._meta.get_fields()
        fields_for_class = {}
        fields_for_filter = {}
        fields_for_order = {}
        for model_field in model_fields:
            fields_for_filter.update({model_field.name: auto})
            fields_for_class.update({model_field.name: auto})
            fields_for_order.update({model_field.name: auto})
        return fields_for_class, fields_for_filter,fields_for_order, model_name

    @staticmethod
    def _create_strawberry_model(
            fields_for_class,
            fields_for_filter,
            fields_for_order,
            strawberry_model_name,
            django_model
    ):
        new_dataclass = type(strawberry_model_name, (), {'__annotations__': fields_for_class})
        # FILTER
        new_filter_dataclass = type(f"{strawberry_model_name}Filter", (), {'__annotations__': fields_for_filter})
        filters = strawberry_django.filter(django_model, lookups=True)
        filter_model = filters(new_filter_dataclass)

        # ORDER
        new_ordering_dataclass = type(f"{strawberry_model_name}Order", (), {'__annotations__': fields_for_order})
        order = strawberry_django.order(model=django_model)
        order_model = order(new_ordering_dataclass)

        # FINAL DATA CLASS
        wrapper = strawberry_django.type(model=django_model, filters=filter_model, order=order_model,
                                         pagination=True)
        straw_object = wrapper(new_dataclass)

        return straw_object, filter_model, order_model

    def _make_schema_depth(
        self,
        dict_models_straw_models_setup,
        dict_models_straw_filter_setup,
        dict_models_straw_order_setup,
        dict_models_fields_setup,
    ):
        counter = 1
        while counter <= self.DEPTH:
            dict_models_fields_setup, dict_filter_fields_setup, dict_orders_fields_setup = self._add_layer_to_fields(
                dict_models_straw_models_setup,
                dict_models_straw_filter_setup,
                dict_models_straw_order_setup,
                dict_models_fields_setup,
            )

            (dict_models_straw_models_setup,
             dict_models_straw_filter_setup,
             dict_models_straw_order_setup,
             final_models_list) = self._create_new_strawberry_models(
                dict_models_fields_setup,
                dict_filter_fields_setup,
                dict_orders_fields_setup,
                counter
            )
            counter+=1

        return final_models_list

    @staticmethod
    def _add_layer_to_fields(
            strawberry_models,
            strawberry_filters,
            strawberry_orders,
            models_fields_dict,
    ):
        new_filter_fields_dict = defaultdict(dict)
        new_order_fields_dict = defaultdict(dict)
        for model in models_fields_dict.keys():
            for model_field in model._meta.get_fields():
                relation = model_field.__dict__.get('related_model', None)
                if relation:
                    related_model = model_field.related_model
                    straw_model = strawberry_models[related_model]
                    straw_filter = strawberry_filters[related_model]
                    straw_order = strawberry_orders[related_model]
                    is_many_to_many = isinstance(model_field, ManyToManyField)
                    if is_many_to_many or model_field.__dict__.get('multiple'):
                        models_fields_dict[model][model_field.name] = List[straw_model]
                    else:
                        models_fields_dict[model][model_field.name] = straw_model
                    new_order_fields_dict[model].update({model_field.name: straw_order})
                    new_filter_fields_dict[model].update({model_field.name: typing.Optional[straw_filter]})

                else:
                    new_order_fields_dict[model].update({model_field.name: auto})
                    new_filter_fields_dict[model].update({model_field.name: auto})
        return models_fields_dict, new_filter_fields_dict, new_order_fields_dict

    def _create_new_strawberry_models(
            self,
            models_fields_dict,
            filter_fields_dict,
            order_fields_dict,
            counter
    ):
        final_models_list = []
        new_dict_models_straw_models_setup = {}
        new_dict_models_straw_filter_setup = {}
        new_dict_models_straw_order_setup = {}
        for model, fields in models_fields_dict.items():
            filter_fields = filter_fields_dict[model]
            order_fields = order_fields_dict[model]

            model_name = model.__name__
            if self.DEPTH - counter != 0:
                model_name += str(self.DEPTH - counter)

            wrapped_model, wrapped_filter, wrapped_order = self._create_strawberry_model(
                fields_for_class=fields,
                fields_for_filter=filter_fields,
                fields_for_order=order_fields,
                strawberry_model_name=model_name,
                django_model=model,
            )
            final_models_list.append(wrapped_model)
            new_dict_models_straw_models_setup[model] = wrapped_model
            new_dict_models_straw_filter_setup[model] = wrapped_filter
            new_dict_models_straw_order_setup[model] = wrapped_order
        return (new_dict_models_straw_models_setup,
                new_dict_models_straw_filter_setup,
                new_dict_models_straw_order_setup,
                final_models_list)
