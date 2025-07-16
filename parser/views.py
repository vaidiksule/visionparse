from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from .models import UserDocument, DocumentBatch
import os
import json
from parser.gemini_parser import extract_data_from_file
from io import BytesIO, StringIO
import openpyxl
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from bson import ObjectId

# =========================
# Helper Functions
# =========================

def validate_uploaded_files(uploaded_files, allowed_types):
    valid_files = []
    for uploaded_file in uploaded_files:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')
        if file_extension in allowed_types:
            valid_files.append(uploaded_file)
    return valid_files

def build_gemini_prompt(custom_fields, strict):
    fields_text = ', '.join(custom_fields)
    if strict:
        return f"Extract only the following fields from this document: {fields_text}. Return as JSON."
    else:
        return f"Extract the following fields from this document: {fields_text}. You can also include any other useful data. Return as JSON."

def save_user_documents(valid_files):
    user_docs = []
    for uploaded_file in valid_files:
        uploaded_file.name = get_valid_filename(uploaded_file.name)
        user_doc = UserDocument()
        user_doc.file.put(uploaded_file, filename=uploaded_file.name)
        user_doc.save()
        user_docs.append(user_doc)
    return user_docs

def generate_result_file(batch_id, all_data, result_format):
    if result_format == 'csv':
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
        return (f'result_{str(batch_id)}.csv', csv_io.getvalue().encode('utf-8'))
    elif result_format == 'json':
        json_io = StringIO()
        json.dump(all_data, json_io, ensure_ascii=False, indent=2)
        return (f'result_{str(batch_id)}.json', json_io.getvalue().encode('utf-8'))
    else:
        raise ValueError("Unsupported format")

def process_documents_with_gemini(documents, custom_fields, strict_mode):
    all_data = []
    prompt = build_gemini_prompt(custom_fields, strict_mode)
    for doc in documents:
        file_obj = doc.file  # mongoengine FileField returns a file-like object
        extracted_json = extract_data_from_file(file_obj, prompt=prompt)
        try:
            all_data.append(json.loads(extracted_json))
        except Exception as e:
            print(f"[Batch] Error loading JSON from Gemini response: {e}")
            all_data.append({})
    return all_data

# =========================
# Views
# =========================

def upload_and_parse_documents(request):
    user_batches = DocumentBatch.objects.order_by('-created_at').limit(5)

    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('documents')
        allowed_types = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']
        valid_files = validate_uploaded_files(uploaded_files, allowed_types)
        if not valid_files:
            messages.error(request, 'No valid files found. Please upload PDF or image files.')
            return render(request, 'parser/upload.html', {'user_batches': user_batches})

        custom_fields = request.POST.getlist('custom_fields[]')
        strict_mode = bool(request.POST.get('strict_mode'))
        result_format = request.POST.get('result_format', 'csv')
        if result_format not in ['csv', 'json']:
            messages.error(request, 'Invalid result format selected. Please choose CSV or JSON.')
            return render(request, 'parser/upload.html', {'user_batches': user_batches})
        user_docs = save_user_documents(valid_files)

        batch = DocumentBatch(
            documents=user_docs,
            status='processing',
            result_format=result_format,
            custom_fields=custom_fields,
            strict_mode=strict_mode
        )
        batch.save()

        all_data = process_documents_with_gemini(user_docs, custom_fields, strict_mode)
        try:
            filename, file_bytes = generate_result_file(batch.id, all_data, result_format)
            batch.result_file.put(file_bytes, filename=filename)
            batch.status = 'completed'
            batch.save()
            messages.success(request, f"Successfully processed {len(valid_files)} documents!")
        except Exception as e:
            batch.status = 'failed'
            batch.save()
            messages.error(request, f"Failed to generate result file: {e}")
        return redirect('batch_result', batch_id=str(batch.id))

    return render(request, 'parser/upload.html', {'user_batches': user_batches, 'allowed_formats': ['csv', 'json']})

def batch_result(request, batch_id):
    batch = DocumentBatch.objects(id=ObjectId(batch_id)).first()
    if not batch:
        return JsonResponse({'success': False, 'error': 'Batch not found'}, status=404)
    return render(request, 'parser/batch_result.html', {'batch': batch})

@csrf_exempt
def delete_document(request, doc_id):
    if request.method == 'POST':
        doc = UserDocument.objects(id=ObjectId(doc_id)).first()
        if doc:
            doc.delete()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Document not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def download_batch_result(request, batch_id, format):
    batch = DocumentBatch.objects(id=ObjectId(batch_id)).first()
    if not batch:
        return JsonResponse({'success': False, 'error': 'Batch not found'}, status=404)

    if format not in ['csv', 'json']:
        return JsonResponse({'success': False, 'error': 'Invalid format'}, status=400)

    all_data = process_documents_with_gemini(batch.documents, batch.custom_fields, batch.strict_mode)
    filename, file_bytes = generate_result_file(batch.id, all_data, format)
    content_type = {
        'csv': 'text/csv',
        'json': 'application/json',
    }.get(format, 'application/octet-stream')

    return FileResponse(BytesIO(file_bytes), as_attachment=True, filename=filename, content_type=content_type)
