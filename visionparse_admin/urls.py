from django.contrib import admin
from django.urls import path, include
from core.views import index, hello_world

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index),  # root route
    path('hello-world/', hello_world),  # root route
    # path('parser/', hello_world),  # root route

    path("__reload__/", include("django_browser_reload.urls")),
]
