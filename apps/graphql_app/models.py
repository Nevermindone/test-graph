from django.db import models





class Fruit(models.Model):
    """A tasty treat"""
    name = models.CharField(
        max_length=20,
    )
    color = models.ForeignKey(
        "Color",
        on_delete=models.CASCADE,
        related_name="fruits",
        blank=True,
        null=True,
    )
    shape = models.ForeignKey(
        "Shape",
        on_delete=models.CASCADE,
        related_name="fruits",
        blank=True,
        null=True,
    )


class Color(models.Model):
    name = models.CharField(
        max_length=20,
        help_text="field description",
    )


class Shape(models.Model):
    name = models.CharField(
        max_length=20,
        help_text="field description",
    )


class Recipe(models.Model):
    recipe_name = models.CharField(max_length=100)
    fruits = models.ManyToManyField(Fruit, related_name='recipes')
