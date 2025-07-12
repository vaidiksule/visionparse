from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from .models import UserDocument, DocumentBatch
import os
import uuid

@login_required
def upload_and_parse_documents(request):
    # Get user's recent batches
    user_batches = DocumentBatch.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    if request.method == 'POST':
        # Handle multiple file uploads
        uploaded_files = request.FILES.getlist('documents')
        
        if not uploaded_files:
            messages.error(request, 'Please select at least one document to upload.')
            return render(request, 'parser/upload.html', {'user_batches': user_batches})
        
        # Validate file types
        allowed_types = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']
        valid_files = []
        
        for uploaded_file in uploaded_files:
            file_extension = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')
            if file_extension not in allowed_types:
                messages.warning(request, f'File "{uploaded_file.name}" has unsupported type (.{file_extension}). Skipping.')
                continue
            valid_files.append(uploaded_file)
        
        if not valid_files:
            messages.error(request, 'No valid files found. Please upload PDF or image files.')
            return render(request, 'parser/upload.html', {'user_batches': user_batches})
        
        # Create batch
        batch = DocumentBatch.objects.create(
            user=request.user,
            status='pending',
            result_format='xml'  # Default to XML for now
        )
        
        # Save user documents
        for uploaded_file in valid_files:
            uploaded_file.name = get_valid_filename(uploaded_file.name)
            user_doc = UserDocument.objects.create(
                user=request.user,
                file=uploaded_file
            )
            batch.documents.add(user_doc)
        
        # Mock AI processing (replace with actual AI API call later)
        batch.status = 'processing'
        batch.save()
        
        # Generate mock XML result
        mock_xml = generate_mock_xml(batch)
        batch.result_file.save(f'result_{batch.id}.xml', ContentFile(mock_xml))
        batch.status = 'completed'
        batch.save()
        
        messages.success(request, f'Successfully processed {len(valid_files)} documents!')
        return redirect('batch_result', batch_id=batch.id)
    
    return render(request, 'parser/upload.html', {'user_batches': user_batches})

@login_required
def batch_result(request, batch_id):
    batch = get_object_or_404(DocumentBatch, id=batch_id, user=request.user)
    return render(request, 'parser/batch_result.html', {'batch': batch})

@csrf_exempt
@login_required
def delete_document(request, doc_id):
    if request.method == 'POST':
        try:
            document = UserDocument.objects.get(id=doc_id, user=request.user)
            document.delete()
            return JsonResponse({'success': True})
        except UserDocument.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Document not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def generate_mock_xml(batch):
    """Generate mock XML result for demonstration"""
    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<invoice_data>
    <batch_info>
        <batch_id>{batch.id}</batch_id>
        <created_at>{batch.created_at}</created_at>
        <total_documents>{batch.documents.count()}</total_documents>
    </batch_info>
    <documents>'''
    
    for i, doc in enumerate(batch.documents.all(), 1):
        xml_content += f'''
        <document id="{i}">
            <filename>{doc.file_name}</filename>
            <file_type>{doc.file_type}</file_type>
            <uploaded_at>{doc.uploaded_at}</uploaded_at>
            <extracted_data>
                <invoice_number>INV-{batch.id:04d}-{i:03d}</invoice_number>
                <amount>${1000 + (i * 50)}.00</amount>
                <vendor>Vendor {i}</vendor>
                <date>2024-01-{i:02d}</date>
            </extracted_data>
        </document>'''
    
    xml_content += '''
    </documents>
</invoice_data>'''
    
    return xml_content
