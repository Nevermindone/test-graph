from django.urls import include, path
from django.contrib import admin


urlpatterns = [
    path("admin/", admin.site.urls),
    path('graphql/', include('apps.graphql_app.urls')),
]

