from django.contrib import admin
from apps.graphql_app.models import (
    Fruit, Color, Shape
)

# Register your models here


class FruitAdmin(admin.ModelAdmin):
    fields = (
        "name",
        "color",
        "shape",
    )

    model = Fruit


admin.site.register(Fruit)
admin.site.register(Color)
admin.site.register(Shape)