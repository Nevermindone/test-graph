# from typing import List
#
# import strawberry
# from strawberry import auto
#
# import strawberry_django
# from django.contrib.auth import get_user_model
#
# from . import models
#
#
# @strawberry_django.filter(models.Recipe)
# class Recipe:
#     id: auto
#     recipe_name: auto
#
#
# @strawberry_django.filter(models.Fruit)
# class FruitFilter:
#     id: auto
#     name: auto
#     recipe: Recipe
#
#
# @strawberry_django.type(
#     models.Fruit,
#     pagination=True,
#     filters=FruitFilter
# )
# class Fruit:
#     id: auto
#     name: auto
#     recipes: List['Recipe']
#     # recipes: list['Recipe'] = strawberry.field(resolver=get_recipes)
#     # @strawberry_django.field
#     # def recipes(self) -> List['Recipe']:
#     #     return models.Recipe.objects.filter(fruits__in=[self.id])
#
#
#
# @strawberry_django.type(
#     models.Recipe,
#     pagination=True,
# )
# class Recipe:
#     id: auto
#     recipe_name: auto
#     fruits: List[Fruit]
