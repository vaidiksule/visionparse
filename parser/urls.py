from django.urls import path
from .views import upload_and_parse_documents, batch_result, delete_document, download_batch_result, register_view, login_view, logout_view

urlpatterns = [
    path('', upload_and_parse_documents, name='upload_doc'),
    path('result/<str:batch_id>/', batch_result, name='batch_result'),
    path('delete/<str:doc_id>/', delete_document, name='delete_document'),
    path('download/<str:batch_id>/<str:format>/', download_batch_result, name='download_batch_result'),
]

urlpatterns += [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
