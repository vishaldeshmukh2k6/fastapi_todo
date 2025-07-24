from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
from models import ToDo
from pydantic import BaseModel
from starlette.status import HTTP_303_SEE_OTHER


app = FastAPI()
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    todos = db.query(ToDo).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "todos": todos,
        "api_links": {
            "List All": "/todos/",
            "Create": "/todos/",
            "Read by ID": "/todos/{todo_id}",
            "Update": "/todos/{todo_id}",
            "Delete": "/todos/{todo_id}"
        }
    })

@app.post("/add", response_class=HTMLResponse)
def add_todo(title: str = Form(...), description: str = Form(...), db: Session = Depends(get_db)):
    new_todo = ToDo(title=title, description=description)
    db.add(new_todo)
    db.commit()
    return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)

@app.post("/delete/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(ToDo).filter(ToDo.id == todo_id).first()
    if todo:
        db.delete(todo)
        db.commit()
    return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)

class ToDoCreate(BaseModel):
    title: str
    description: str

class ToDoResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool

    class Config:
        from_attributes = True

@app.get("/todos/", response_model=list[ToDoResponse])
def read_todos(db: Session = Depends(get_db)):
    return db.query(ToDo).all()

@app.post("/todos/", response_model=ToDoResponse)
def create_todo(todo: ToDoCreate, db: Session = Depends(get_db)):
    db_todo = ToDo(**todo.dict())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.get("/todos/{todo_id}", response_model=ToDoResponse)
def read_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(ToDo).filter(ToDo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="ToDo not found")
    return todo

@app.put("/todos/{todo_id}", response_model=ToDoResponse)
def update_todo(todo_id: int, todo: ToDoCreate, db: Session = Depends(get_db)):
    db_todo = db.query(ToDo).filter(ToDo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="ToDo not found")
    db_todo.title = todo.title
    db_todo.description = todo.description
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.delete("/todos/{todo_id}")
def delete_api(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(ToDo).filter(ToDo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="ToDo not found")
    db.delete(todo)
    db.commit()
    return {"message": "ToDo deleted"}
