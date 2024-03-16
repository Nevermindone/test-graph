import strawberry_django
from strawberry import auto
from . import models


@strawberry_django.filter(models.Fruit)
class FruitFilter:
    id: auto
    name: auto
#
#
# @strawberry_django.order(models.Color)
# class ColorOrder:
#     id: auto
#     name: auto
#
#
# @strawberry_django.order(models.Fruit)
# class FruitOrder:
#     id: auto
#     name: auto
#     # color: ColorOrder


@strawberry_django.type(models.Fruit, filters=FruitFilter)
class Fruit:
    id: auto
    name: auto
    color: auto
    shape: auto


@strawberry_django.type(models.Color)
class Color:
    id: auto
    name: auto
    fruits: list['Fruit']
#
#
# @strawberry_django.type(models.Shape)
# class Shape:
#     id: auto
#     name: auto
#     fruits: list['Fruit']
