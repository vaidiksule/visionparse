from django.http import HttpResponse
from django.shortcuts import render 

def hello_world(request):
    return HttpResponse("Hello, World from Django on Render!".encode('utf-8'))


def index(request):
    return render(request, 'core/index.html')