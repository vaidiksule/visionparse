from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from parser.models import Document
from django.utils.text import get_valid_filename
import os

def upload_doc(request):
    documents = Document.objects.all().order_by('-uploaded_at')
    
    if request.method == 'POST':
        if 'document' in request.FILES:
            uploaded_file = request.FILES['document']

            
            # Validate file type
            allowed_types = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']
            file_extension = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')
            
            if file_extension not in allowed_types:
                messages.error(request, f'File type .{file_extension} is not supported. Please upload PDF or image files.')
                return render(request, 'parser/upload.html', {'documents': documents})
            
            # Create document record
            uploaded_file.name = get_valid_filename(uploaded_file.name)
            document = Document(file=uploaded_file)
            document.save()
            
            messages.success(request, f'Document "{document.file_name}" uploaded successfully!')
            return redirect('upload_doc')
    
    return render(request, 'parser/upload.html', {'documents': documents})

@csrf_exempt
def delete_document(request, doc_id):
    if request.method == 'POST':
        try:
            document = Document.objects.get(id=doc_id)
            document.delete()
            return JsonResponse({'success': True})
        except Document.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Document not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})
