from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from .models import UserDocument, DocumentBatch
import os
import uuid
import json
from parser.gemini_parser import extract_data_from_file
import xml.etree.ElementTree as ET
import openpyxl
from openpyxl.utils import get_column_letter
from io import BytesIO
import csv
from io import StringIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def get_or_create_default_user():
    """Get or create a default user for testing without authentication"""
    try:
        return User.objects.get(username='default_user')
    except User.DoesNotExist:
        return User.objects.create_user(
            username='default_user',
            email='default@example.com',
            password='defaultpass123'
        )

# @login_required  # TEMPORARILY COMMENTED OUT FOR TESTING
def upload_and_parse_documents(request):
    # TEMPORARY: Use default user instead of request.user
    default_user = get_or_create_default_user()
    
    # Get user's recent batches
    # user_batches = DocumentBatch.objects.filter(user=request.user).order_by('-created_at')[:5]  # ORIGINAL
    user_batches = DocumentBatch.objects.filter(user=default_user).order_by('-created_at')[:5]  # TEMPORARY
    
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
        
        # Get custom fields, strict mode, and result format from POST
        custom_fields = request.POST.getlist('custom_fields[]')
        strict_mode = bool(request.POST.get('strict_mode'))
        result_format = request.POST.get('result_format', 'xlsx')
        # Create batch
        batch = DocumentBatch.objects.create(
            user=default_user,  # TEMPORARY
            status='pending',
            result_format=result_format,
            custom_fields=custom_fields,
            strict_mode=strict_mode
        )
        
        # Save user documents
        for uploaded_file in valid_files:
            uploaded_file.name = get_valid_filename(uploaded_file.name)
            user_doc = UserDocument.objects.create(
                # user=request.user,  # ORIGINAL
                user=default_user,  # TEMPORARY
                file=uploaded_file
            )
            batch.documents.add(user_doc)
        
        # Mock AI processing (replace with actual AI API call later)
        batch.status = 'processing'
        batch.save()

        # Gemini API processing
        print(f"[Batch] Starting Gemini API processing for batch {batch.id}")
        all_data = []
        for doc in batch.documents.all():
            file_path = doc.file.path
            print(f"[Batch] Sending file to Gemini: {file_path}")
            prompt = build_gemini_prompt(custom_fields, strict_mode)
            extracted_json = extract_data_from_file(file_path, prompt=prompt)
            try:
                all_data.append(json.loads(extracted_json))
            except Exception as e:
                print(f"[Batch] Error loading JSON from Gemini response: {e}")
                all_data.append({})

        # Generate result file in selected format
        if result_format == 'xlsx':
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Invoices"
            if all_data and isinstance(all_data[0], dict):
                headers = list(all_data[0].keys())
                ws.append(headers)
                for item in all_data:
                    row = []
                    for h in headers:
                        v = item.get(h, "")
                        if isinstance(v, (list, dict)):
                            v = json.dumps(v, ensure_ascii=False)
                        row.append(v)
                    ws.append(row)
            else:
                ws.append(["No data extracted"])
            xlsx_io = BytesIO()
            wb.save(xlsx_io)
            xlsx_io.seek(0)
            batch.result_file.save(f'result_{batch.id}.xlsx', ContentFile(xlsx_io.read()))
        elif result_format == 'csv':
            csv_io = StringIO()
            if all_data and isinstance(all_data[0], dict):
                headers = list(all_data[0].keys())
                writer = csv.writer(csv_io)
                writer.writerow(headers)
                for item in all_data:
                    row = []
                    for h in headers:
                        v = item.get(h, "")
                        if isinstance(v, (list, dict)):
                            v = json.dumps(v, ensure_ascii=False)
                        row.append(v)
                    writer.writerow(row)
            else:
                writer = csv.writer(csv_io)
                writer.writerow(["No data extracted"])
            batch.result_file.save(f'result_{batch.id}.csv', ContentFile(csv_io.getvalue().encode('utf-8')))
        elif result_format == 'pdf':
            pdf_io = BytesIO()
            c = canvas.Canvas(pdf_io, pagesize=letter)
            width, height = letter
            y = height - 40
            if all_data and isinstance(all_data[0], dict):
                headers = list(all_data[0].keys())
                c.setFont("Helvetica-Bold", 12)
                for i, h in enumerate(headers):
                    c.drawString(40 + i*120, y, h)
                y -= 20
                c.setFont("Helvetica", 10)
                for item in all_data:
                    row = []
                    for h in headers:
                        v = item.get(h, "")
                        if isinstance(v, (list, dict)):
                            v = json.dumps(v, ensure_ascii=False)
                        row.append(str(v))
                    for i, v in enumerate(row):
                        c.drawString(40 + i*120, y, v[:30])
                    y -= 20
                    if y < 40:
                        c.showPage()
                        y = height - 40
            else:
                c.drawString(40, y, "No data extracted")
            c.save()
            pdf_io.seek(0)
            batch.result_file.save(f'result_{batch.id}.pdf', ContentFile(pdf_io.read()))
        batch.status = 'completed'
        batch.save()
        print(f"[Batch] Result file saved for batch {batch.id} as {result_format}")
        print(f"[Batch] Batch {batch.id} marked as completed.")
        
        messages.success(request, f'Successfully processed {len(valid_files)} documents!')
        return redirect('batch_result', batch_id=batch.id)
    
    return render(request, 'parser/upload.html', {'user_batches': user_batches})

# @login_required  # TEMPORARILY COMMENTED OUT FOR TESTING
def batch_result(request, batch_id):
    # batch = get_object_or_404(DocumentBatch, id=batch_id, user=request.user)  # ORIGINAL
    default_user = get_or_create_default_user()
    batch = get_object_or_404(DocumentBatch, id=batch_id, user=default_user)  # TEMPORARY
    return render(request, 'parser/batch_result.html', {'batch': batch})

@csrf_exempt
# @login_required  # TEMPORARILY COMMENTED OUT FOR TESTING
def delete_document(request, doc_id):
    if request.method == 'POST':
        try:
            # document = UserDocument.objects.get(id=doc_id, user=request.user)  # ORIGINAL
            default_user = get_or_create_default_user()
            document = UserDocument.objects.get(id=doc_id, user=default_user)  # TEMPORARY
            document.delete()
            return JsonResponse({'success': True})
        except UserDocument.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Document not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def build_gemini_prompt(custom_fields, strict):
    fields_text = ', '.join(custom_fields)
    if strict:
        return f"Extract only the following fields from this document: {fields_text}. Return as JSON."
    else:
        return f"Extract the following fields from this document: {fields_text}. You can also include any other useful data. Return as JSON."

def generate_result_file(batch, all_data, result_format):
    # Returns (filename, file_bytes)
    import openpyxl
    import json
    from io import BytesIO, StringIO
    import csv
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    if result_format == 'xlsx':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Invoices"
        if all_data and isinstance(all_data[0], dict):
            headers = list(all_data[0].keys())
            ws.append(headers)
            for item in all_data:
                row = []
                for h in headers:
                    v = item.get(h, "")
                    if isinstance(v, (list, dict)):
                        v = json.dumps(v, ensure_ascii=False)
                    row.append(v)
                ws.append(row)
        else:
            ws.append(["No data extracted"])
        xlsx_io = BytesIO()
        wb.save(xlsx_io)
        xlsx_io.seek(0)
        return (f'result_{batch.id}.xlsx', xlsx_io.read())
    elif result_format == 'csv':
        csv_io = StringIO()
        if all_data and isinstance(all_data[0], dict):
            headers = list(all_data[0].keys())
            writer = csv.writer(csv_io)
            writer.writerow(headers)
            for item in all_data:
                row = []
                for h in headers:
                    v = item.get(h, "")
                    if isinstance(v, (list, dict)):
                        v = json.dumps(v, ensure_ascii=False)
                    row.append(v)
                writer.writerow(row)
        else:
            writer = csv.writer(csv_io)
            writer.writerow(["No data extracted"])
        return (f'result_{batch.id}.csv', csv_io.getvalue().encode('utf-8'))
    elif result_format == 'pdf':
        pdf_io = BytesIO()
        c = canvas.Canvas(pdf_io, pagesize=letter)
        width, height = letter
        y = height - 40
        if all_data and isinstance(all_data[0], dict):
            headers = list(all_data[0].keys())
            c.setFont("Helvetica-Bold", 12)
            for i, h in enumerate(headers):
                c.drawString(40 + i*120, y, h)
            y -= 20
            c.setFont("Helvetica", 10)
            for item in all_data:
                row = []
                for h in headers:
                    v = item.get(h, "")
                    if isinstance(v, (list, dict)):
                        v = json.dumps(v, ensure_ascii=False)
                    row.append(str(v))
                for i, v in enumerate(row):
                    c.drawString(40 + i*120, y, v[:30])
                y -= 20
                if y < 40:
                    c.showPage()
                    y = height - 40
        else:
            c.drawString(40, y, "No data extracted")
        c.save()
        pdf_io.seek(0)
        return (f'result_{batch.id}.pdf', pdf_io.read())
    else:
        raise ValueError("Unsupported format")

def download_batch_result(request, batch_id, format):
    default_user = get_or_create_default_user()
    batch = get_object_or_404(DocumentBatch, id=batch_id, user=default_user)
    # Try to load all_data from the batch's documents
    all_data = []
    for doc in batch.documents.all():
        file_path = doc.file.path
        prompt = build_gemini_prompt(batch.custom_fields, batch.strict_mode)
        from parser.gemini_parser import extract_data_from_file
        extracted_json = extract_data_from_file(file_path, prompt=prompt)
        try:
            all_data.append(json.loads(extracted_json))
        except Exception as e:
            all_data.append({})
    filename, file_bytes = generate_result_file(batch, all_data, format)
    content_type = {
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv',
        'pdf': 'application/pdf',
    }.get(format, 'application/octet-stream')
    return FileResponse(BytesIO(file_bytes), as_attachment=True, filename=filename, content_type=content_type)
