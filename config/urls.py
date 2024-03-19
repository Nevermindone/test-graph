from django.urls import include, path
from django.contrib import admin


urlpatterns = [
    path("app2/admin/", admin.site.urls),
    path('app2/graphql/', include('apps.graphql_app.urls')),
]

