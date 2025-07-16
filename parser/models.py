# parser/models.py
# from django.contrib.auth.models import User
# from django.db import models
# from djongo import models as djongo_models
from mongoengine import Document as MongoDocument, StringField, DateTimeField, BooleanField, FileField, ListField, ReferenceField, EmailField
import datetime

class UserDocument(MongoDocument):
    file = FileField(required=True)
    file_name = StringField(max_length=255)
    file_type = StringField(max_length=10)
    uploaded_at = DateTimeField(default=datetime.datetime.utcnow)
    is_processed = BooleanField(default=False)

    meta = {'collection': 'user_documents'}

    def clean(self):
        if self.file:
            self.file_name = getattr(self.file, 'name', '') or ''
            self.file_type = self.file_name.split('.')[-1].lower() if self.file_name else ''

class DocumentBatch(MongoDocument):
    documents = ListField(ReferenceField(UserDocument))
    result_file = FileField()
    custom_fields = ListField(StringField())
    strict_mode = BooleanField(default=False)
    result_format = StringField(choices=('csv', 'json'))
    status = StringField(choices=('pending', 'processing', 'completed', 'failed'), default='pending')
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    user = StringField(required=True)  # user_id from CustomUser

    meta = {'collection': 'document_batches'}

class CustomUser(MongoDocument):
    username = StringField(required=True, unique=True, max_length=150)
    email = EmailField(required=True, unique=True, max_length=255)
    password_hash = StringField(required=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {'collection': 'custom_users'}
