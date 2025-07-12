from django.urls import path
from .views import upload_doc, delete_document

urlpatterns = [
    path('', upload_doc, name='upload_doc'),
    path('delete/<int:doc_id>/', delete_document, name='delete_document'),
]
