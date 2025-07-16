from mongoengine import connect
from decouple import config

connect(
    db="visionparse",
    host=config("MONGO_URI")
)
