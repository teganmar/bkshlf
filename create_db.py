from database import Base,engine
from models import Book

# ran this small script in separate terminal before running API 
# to create the database for the API to connect to

print("Creating database....")

Base.metadata.create_all(engine)