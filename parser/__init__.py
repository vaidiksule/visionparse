from mongoengine import connect
from django.conf import settings

connect(
    db='visionparse',
    host=getattr(settings, 'MONGO_URI', 'mongodb://localhost:27017/visionparse')
)
