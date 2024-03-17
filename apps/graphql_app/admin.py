from django.contrib import admin
from apps.graphql_app.models import (
    Fruit, Color, Shape, Recipe
)

# Register your models here


class RecipeAdmin(admin.ModelAdmin):
    filter_horizontal = ('fruits',)


admin.site.register(Fruit)
admin.site.register(Color)
admin.site.register(Shape)
admin.site.register(Recipe, RecipeAdmin)
