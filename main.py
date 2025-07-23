from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import ToDo
from pydantic import BaseModel

app = FastAPI()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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

@app.get("/")
def read_root():
    return {"message": "Welcome to ToDo API"}

@app.post("/todos/", response_model=ToDoResponse)
def create_todo(todo: ToDoCreate, db: Session = Depends(get_db)):
    db_todo = ToDo(**todo.dict())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.get("/todos/", response_model=list[ToDoResponse])
def read_todos(db: Session = Depends(get_db)):
    return db.query(ToDo).all()

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
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = db.query(ToDo).filter(ToDo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="ToDo not found")
    db.delete(db_todo)
    db.commit()
    return {"message": "ToDo deleted"}
