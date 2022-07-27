from datetime import datetime,date
import sqlalchemy
from sqlalchemy.sql.expression import update
from sqlalchemy.sql.sqltypes import JSON, DateTime, Float
from fastapi import FastAPI, Depends, Path, Query, HTTPException, Request, Header, Form, Body
from fastapi.responses import HTMLResponse, ORJSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List, Type, Union
from pydantic import BaseModel, Field
import uvicorn
import requests
import json
import sys,os
#import databases #first installed: pip install databases[postgresql]
from database import SessionLocal, engine
from models import Book


description = """
Herein lies your personal, digital bookshelf.
Your very own cozy, magical nook of the internet to house and document all of your favorite paper worlds.

## Functionalities

* book widths prooportional to the length of the book
* tracks reading progress along the spin of the book
* choose your book and book case aesthetic (i.e. modern, antique, ancient, cozy, rainbow, color theme of your choosing)
* click on options: start/end date, ratings out of 5 ⭐️ (defaults = writing & story) w/user set template, notes (by pg or by thought)
* spotify wrapped like breakdown of reading stats (will  require: user input or exiting book api or webscraped in house database)
* "my monthly bookshelf"
* "my [YEAR] bookcase"
* "my biannual library" (library of the decade, of the half decade, the historical archives)

"""

# instantiate the api
app=FastAPI(title="The Bookshelf",
            description=description)

# include html file
templates = Jinja2Templates(directory="templates")
# include css file
app.mount("/static", StaticFiles(directory="static"), name="static")

# not yet sure what this is for will look into it
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#postgres database
db = SessionLocal()

# make schemas (i.e. our serializer that turns the input into json format)
class init_entry_base(BaseModel):
    #id:Optional[int]=None
    title:str
    author:str
    start_date:date #using datetime here gives you the hr:min:sec as well if u want it
    end_date:Optional[date]=None
    rating:Optional[str] = Field(
        None, title="The ratings of the book", max_length=300
    )
    notes:Optional[str] = Field(
        None, title="Notes on the book", max_length=300
    )
    class Config:
        orm_mode=True

    @classmethod
    def as_form(
        cls,
        title: str = Form(..., max_length=30),
        author: str = Form(...),
        start_date: date = Form(...),
        end_date: date = Form(None),
        rating: str = Form(None),
        notes: str = Form(None)
    ):
        class Config:
            orm_mode=True

        return cls(
            title=title,
            author=author,
            start_date=start_date,
            end_date=end_date,
            rating=rating,
            notes=notes
        )

class init_entry(init_entry_base):
    id:int
    # class Config:
    #     orm_mode=True

    @classmethod
    def as_form(
        cls,
        id: int,
        title: str = Form(...),
        author: str = Form(...),
        start_date: date = Form(...),
        end_date: date = Form(None),
        rating: str = Form(None),
        notes: str = Form(None)
    ):
        return cls(
            id=id,
            title=title,
            author=author,
            start_date=start_date,
            end_date=end_date,
            rating=rating,
            notes=notes
        )

class update_entry(BaseModel):
    #id:Optional[int]
    gettitle:str
    getauthor:Optional[str]
    getstart_date:Optional[date]
    getend_date:Optional[date]=None
    getrating:Optional[str] = Field(
        None, title="The ratings of the book", max_length=300
    )
    getnotes:Optional[str] = Field(
        None, title="Notes on the book", max_length=300
    )
    # class Config:
    #     orm_mode=True

    @classmethod
    def as_form(
        cls,
        gettitle: str = Form(...),
        getauthor: str = Form(None),
        getstart_date: date = Form(None),
        getend_date: date = Form(None),
        getrating: str = Form(None),
        getnotes: str = Form(None)
    ):
        return cls(
            gettitle=gettitle,
            getauthor=getauthor,
            getstart_date=getstart_date,
            getend_date=getend_date,
            getrating=getrating,
            getnotes=getnotes
        )

# index.html page endpoint
@app.get('/', response_class=HTMLResponse)
def home(request:Request):
    return templates.TemplateResponse("index.html",{"request":request})

# CREATE
@app.post('/create-book', response_model=init_entry_base, status_code=200)#response_model=init_entry_base,
#FORM VERSION
# def create_entry(id: int = None,
#                  title:str = Form(...),
#                  author:str = Form(...), 
#                  start_date:date = Form(...), 
#                  end_date:date = Form(None), 
#                  rating: str = Form(None), 
#                  notes: str = Form(None)):

# new_book=Book(
#         id=id,
#         title=title,
#         author=author,
#         start_date=start_date,
#         end_date=end_date,
#         rating=rating,
#         notes=notes
#     )

#db_book=db.query(Book).filter(Book.title==title).first()
def create_entry(formData: init_entry_base = Depends(init_entry_base.as_form)):
    
    # new_book=Book(
    #     # id=id,
    #     title=formData.title,
    #     author=formData.author,
    #     start_date=formData.start_date,
    #     end_date=formData.end_date,
    #     rating=formData.rating,
    #     notes=formData.notes
    # )
    db_book = db.query(Book).filter(Book.title==formData.title).first()

    if db_book is not None:
        raise HTTPException(status_code=400, detail="book already exists")

    new_book=Book(
        # id=id,
        title=formData.title,
        author=formData.author,
        start_date=formData.start_date,
        end_date=formData.end_date,
        rating=formData.rating,
        notes=formData.notes
    )
    # print(new_book)
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    
    return new_book 

# READ
@app.get("/entries", response_model=List[init_entry_base],status_code=200)
def get_all_entries():
    books = db.query(Book).all()
    return books

def is_subsequence(A, B):
    it = iter(A)
    return all(x in it for x in B) #returns boolean value indicating if B is in A
@app.get("/get-book/{title}", response_model=init_entry_base)
def get_book_by_title(title:str):
    titles = [r.title for r in db.query(Book.title).all()]
    for t in titles:
        if is_subsequence(t, title):
            db_book=db.query(Book).filter(Book.title == t).first()
    #db_book=db.query(Book).filter(Book.title.contains(title)).first()
    if db_book is None:
        raise HTTPException(status_code=400, detail="book does not exist")
    return db_book

# UPDATE
@app.put("/update-book", status_code=200)
def update_book(book: update_entry = Depends(update_entry.as_form)):#(book:update_entry):
    titles = [r.title for r in db.query(Book.title).all()]
    for t in titles:
        if is_subsequence(t, book.gettitle):
            db_book=db.query(Book).filter(Book.title == t).first()
    #db_book=db.query(Book).filter(Book.title.contains(book.gettitle)).first()
    if db_book is None:
        raise HTTPException(status_code=400, detail="book does not exist")

    # if ((book.title != None) and (db_book.title != book.title)) or (db_book.title == None):
    #     db_book.title = book.title
    
    if ((book.getauthor != None) and (db_book.author != book.getauthor)) or (db_book.author == None):
        db_book.author = book.getauthor

    if ((book.getstart_date != None) and (db_book.start_date != book.getstart_date)) or (db_book.start_date == None):
        db_book.start_date = book.getstart_date

    if ((book.getend_date != None) and (db_book.end_date != book.getend_date)) or (db_book.end_date == None):
        db_book.end_date = book.getend_date

    if ((book.getrating != None) and (db_book.rating != book.getrating)) or (db_book.rating == None):
        db_book.rating = book.getrating

    if ((book.getnotes != None) and (db_book.notes != book.getrating)) or (db_book.notes == None):
        db_book.notes = book.getnotes

    db.commit()
    return db_book


# DELETE
@app.delete("/delete-book/{title}")
def del_by_title(title:str):
    titles = [r.title for r in db.query(Book.title).all()]
    for t in titles:
        if is_subsequence(t, title):
            db_book=db.query(Book).filter(Book.title == t).first()
    #db_book=db.query(Book).filter(Book.title==title).first()
    if db_book is None:
        raise HTTPException(status_code=400, detail="book does not exist")
    db.delete(db_book)
    db.commit()
    return f"{title} was deleted from the database"

if __name__ == "__main__":
    #uvicorn.run("main:app", host='127.0.0.1', port=8301,reload=True)
    uvicorn.run("main:app", host='0.0.0.0', port=5000,reload=True, debug=True)
