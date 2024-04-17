from sqlalchemy import Column, Integer, String, func, UniqueConstraint, Boolean
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint('first_name', 'last_name', 'user_id', name='unique_contact_user'),
    )
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String(10))
    birthday = Column(String)
    user_id = Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), default=None)
    user = relationship('User', backref="notes")

    def __iter__(self):
        yield self


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column('crated_at', DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)

    def to_dict(self):
        return {'user':
                        {
                            "id": self.id,
                            "username": self.username,
                            "email": self.email,
                            "created_at": self.created_at,
                            "avatar": self.avatar,
                            "refresh_token": self.refresh_token,
                            "confirmed": self.confirmed
                        }
                }

    def __str__(self):
        return f"id={self.id}, username={self.username}, email={self.email}, created_at={self.created_at}, avatar={self.avatar}, refresh_token={self.refresh_token}, confirmed={self.confirmed}"