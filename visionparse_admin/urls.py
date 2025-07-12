from django.contrib import admin
from django.urls import path, include
from core.views import index, hello_world
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index),  # root route
    path('hello-world/', hello_world),  # root route
    path('parser/', include('parser.urls')),

    path("__reload__/", include("django_browser_reload.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
