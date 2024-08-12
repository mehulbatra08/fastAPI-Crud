from fastapi import FastAPI, HTTPException, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session, joinedload
from starlette.requests import Request

app = FastAPI()
templates = Jinja2Templates(directory="templates")
models.Base.metadata.create_all(bind=engine)

# Pydantic Models
class PostBase(BaseModel):
    title: str
    content: str
    user_id: int

class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    pass

class PostCreate(PostBase):
    pass

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User Endpoints
@app.post("/users/", response_model=UserBase, status_code=status.HTTP_201_CREATED)
async def create_user(name: str = Form(...), db: Session = Depends(get_db)):
    db_user = models.User(name=name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return RedirectResponse(url='/', status_code=status.HTTP_302_FOUND)

@app.get("/users/", response_model=List[UserBase])
async def read_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

@app.get("/users/{user_id}", response_model=UserBase)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Post Endpoints
@app.get("/posts/{post_id}", response_class=HTMLResponse)
async def read_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse("post.html", {"request": request, "post": post})

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request, db: Session = Depends(get_db)):
    users = db.query(models.User).options(joinedload(models.User.posts)).all()
    posts = db.query(models.Post).all()
    return templates.TemplateResponse("index.html", {"request": request, "users": users, "posts": posts})

@app.get("/posts/create", response_class=HTMLResponse)
async def create_post_form(request: Request, db: Session = Depends(get_db)):
    users = db.query(models.User).all()  # Fetch all users to populate the dropdown
    return templates.TemplateResponse("post_create_form.html", {"request": request, "users": users})

@app.post("/posts/create", response_class=HTMLResponse)
async def create_post_form_submit(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    # Ensure the user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_post = models.Post(title=title, content=content, user_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    # Fetch updated data to render in the template
    users = db.query(models.User).all()
    posts = db.query(models.Post).all()
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts, "users": users})


@app.get("/posts/{post_id}/edit", response_class=HTMLResponse)
async def edit_post_form(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).options(joinedload(models.Post.owner)).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    users = db.query(models.User).all()
    return templates.TemplateResponse("post_edit_form.html", {"request": request, "post": post, "users": users})

@app.post("/posts/{post_id}/edit", response_class=RedirectResponse)
async def edit_post(post_id: int, title: str = Form(...), content: str = Form(...), user_id: int = Form(...), db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    post.title = title
    post.content = content
    post.user_id = user_id
    db.commit()
    return RedirectResponse(url='/', status_code=status.HTTP_302_FOUND)

@app.post("/posts/{post_id}/delete", response_class=RedirectResponse)
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return RedirectResponse(url='/', status_code=status.HTTP_302_FOUND)
