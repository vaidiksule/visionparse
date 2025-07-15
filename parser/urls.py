from django.urls import path
from .views import upload_and_parse_documents, batch_result, delete_document

urlpatterns = [
    path('', upload_and_parse_documents, name='upload_doc'),
    path('result/<int:batch_id>/', batch_result, name='batch_result'),
    path('delete/<int:doc_id>/', delete_document, name='delete_document'),
    path('download/<int:batch_id>/<str:format>/', views.download_batch_result, name='download_batch_result'),
]
