from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    
    # Relationship with Post
    posts = relationship("Post", back_populates="owner")

class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(5000))
    content = Column(String(20000))
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Relationship with User
    owner = relationship("User", back_populates="posts")
