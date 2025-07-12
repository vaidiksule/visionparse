from django.db import models
import os
from django.core.validators import FileExtensionValidator

class Document(models.Model):
    file = models.FileField(
        upload_to='documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=10, blank=True)
    
    def save(self, *args, **kwargs):
        if self.file and self.file.name:
            self.file_name = os.path.basename(self.file.name)
            ext = os.path.splitext(self.file.name)[1].lower().replace('.', '')
            self.file_type = ext
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.file_name or "Untitled Document"
    
    @property
    def is_image(self):
        return self.file_type in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']
    
    @property
    def is_pdf(self):
        return self.file_type == 'pdf'
