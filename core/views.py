from django.http import HttpResponse

def hello_world(request):
    return HttpResponse("Hello, World from Django on Render!".encode('utf-8'))