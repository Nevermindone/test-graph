from typing import List

import strawberry
from strawberry import auto

import strawberry_django
from django.contrib.auth import get_user_model

from . import models


def magic(class_):
    cls = class_
    def new_field(self) -> List['Recipe']:
        return models.Recipe.objects.filter(**{f'fruits__in':[self.id]})
    setattr(cls, 'recipes', strawberry_django.field(new_field))
    return cls  # type: ignore


@strawberry_django.type(
    models.Fruit,
    pagination=True,
)
@magic
class Fruit:
    id: auto
    name: auto
    recipes: List['Recipe']
    # recipes: list['Recipe'] = strawberry.field(resolver=get_recipes)
    # @strawberry_django.field
    # def recipes(self) -> List['Recipe']:
    #     return models.Recipe.objects.filter(fruits__in=[self.id])

@strawberry_django.type(
    models.Recipe,
    pagination=True,
)
class Recipe:
    id: auto
    recipe_name: auto
    fruits: List[Fruit]
