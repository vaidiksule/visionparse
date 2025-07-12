from django.contrib import admin
from django.urls import path
from core.views import hello_world

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', hello_world),  # root route
    # path('parser/', hello_world),  # root route
]
