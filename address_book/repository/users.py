from libgravatar import Gravatar
from sqlalchemy.orm import Session
from typing import Type

from address_book.database.models import User
from address_book.schemas import UserModel


async def get_user_by_email(email: str, db: Session) -> Type[User]:
    """
        Retrieves first user by email.
        :param email: The email to retrieve user for
        :type email: str
        :param db: The database session.
        :type db: Session
        :return: User object.
        :rtype: Type[User]
    """
    return db.query(User).filter(User.email == email).first()


async def create_user(body: UserModel, db: Session) -> User:
    """
        Creates a new user in database
        :param body: User's object
        :type body: UserModel
        :param db: The database session.
        :type db: Session

        :return: User's object.
        :rtype: User
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as e:
        print(e)
    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: Session) -> None:
    """
        Updates user's authorization token in database
        :param user: User's object
        :type user: UserModel
        :param token: Token string
        :type token: str | None
        :param db: The database session.
        :type db: Session
    """
    user.refresh_token = token
    db.commit()


async def confirmed_email(email: str, db: Session) -> None:
    """
        Confirmes user's email in database
        :param email: email string
        :type email: str
        :param db: The database session.
        :type db: Session
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def update_avatar(email, url: str, db: Session) -> Type[User]:
    """
        Updates user's avatar
        :param email: email string
        :type email: str
        :param url: email string
        :type url: str
        :param db: The database session.
        :type db: Session
        
        :return: User's object.
        :rtype: Type[User]
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user
