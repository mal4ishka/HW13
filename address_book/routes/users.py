from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
from address_book.database.db import get_db
from address_book.database.models import User
from address_book.repository import users as repository_users
from address_book.services.auth import auth_service
from address_book.conf.config import settings
from address_book.schemas import UserDb

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    """
        Get the current user's information.

        :param current_user: The current authenticated user.
        :type current_user: User

        :return: The current user's information.
        :rtype: UserDb
    """
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)):
    """
        Update the current user's avatar.

        :param file: The avatar file to upload.
        :type file: UploadFile
        :param current_user: The current authenticated user.
        :type current_user: User
        :param db: The database session.
        :type db: Session

        :return: The updated user information.
        :rtype: UserDb
    """
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )

    r = cloudinary.uploader.upload(file.file, public_id=f'NotesApp/{current_user.username}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'NotesApp/{current_user.username}')\
                        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user
