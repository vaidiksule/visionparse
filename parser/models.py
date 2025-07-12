# parser/models.py
from django.contrib.auth.models import User
from django.db import models

class UserDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='user_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)
    is_processed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name
            self.file_type = self.file.name.split('.')[-1].lower()
        super().save(*args, **kwargs)

class DocumentBatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ])
    documents = models.ManyToManyField(UserDocument)
    result_file = models.FileField(upload_to='results/', null=True, blank=True)
    result_format = models.CharField(max_length=10, choices=[('xml', 'XML'), ('csv', 'CSV')])
