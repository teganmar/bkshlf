from sqlalchemy.orm import declarative_base, session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
#import psycopg2

DATABASE_URL = "postgresql://postgres:password@localhost:5432/bookshelf"

engine=create_engine(DATABASE_URL, echo=True)

Base=declarative_base()

SessionLocal=sessionmaker(bind=engine)