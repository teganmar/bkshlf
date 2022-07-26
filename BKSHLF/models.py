from datetime import datetime
from database import Base
from sqlalchemy import String,Boolean,Integer,Column,Text,Float,UniqueConstraint,DateTime,Date

#these are postgreSQL "models"
class Book(Base):
    __tablename__='books'
    #id = Column(Integer, index=True, primary_key=True)
    title=Column(String, primary_key=True, nullable=False)
    author=Column(String, nullable=False)
    start_date=Column(Date, nullable=False)
    end_date=Column(Date, nullable=True)
    rating=Column(Text)
    notes=Column(Text)

    def __repr__(self) -> str:
        return f"<Book name:{self.title} author:{self.author}>"

