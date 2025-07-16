from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from parser.views import register_view, login_view, logout_view, upload_and_parse_documents
from core.views import home_view, hello_world
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('parser/', include('parser.urls')),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', home_view),  # root route
    path('hello-world/', hello_world),  # root route
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
