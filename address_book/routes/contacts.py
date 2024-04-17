from typing import List
from fastapi import APIRouter, HTTPException, Depends, status, Response
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session
from address_book.services.auth import auth_service
from address_book.database.db import get_db
from address_book.schemas import ContactBase, ContactResponse
from address_book.database.models import User
from address_book.repository import contacts as repository_contacts

router = APIRouter(prefix='/contacts')


@router.get("/get_all", response_model=List[ContactResponse])
async def read_contacts(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    contacts = await repository_contacts.get_contacts(current_user, db)
    return contacts


@router.get("/get/{contact_id}", response_model=ContactResponse)
async def read_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    contact = await repository_contacts.get_contact(current_user, contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/create", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def create_new(body: ContactBase, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
        Create a new contact for the current user.

        :param body: The contact data to create.
        :type body: ContactBase
        :param db: The database session.
        :type db: Session
        :param current_user: The current authenticated user.
        :type current_user: User

        :return: Response indicating the contact was created.
        :rtype: Response
    """
    await repository_contacts.create_contact(current_user, body, db)
    return Response(status_code=status.HTTP_201_CREATED, content='Contact successfully created')


@router.put("/update/{contact_id}", response_model=ContactResponse)
async def update_contact(body: ContactBase, contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
        Update an existing contact for the current user.

        :param body: The updated contact data.
        :type body: ContactBase
        :param contact_id: The ID of the contact to update.
        :type contact_id: int
        :param db: The database session.
        :type db: Session
        :param current_user: The current authenticated user.
        :type current_user: User

        :return: The updated contact.
        :rtype: ContactResponse
        """
    contact = await repository_contacts.update_contact(current_user, contact_id, body, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/delete/{contact_id}")
async def remove_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
        Delete a contact for the current user.

        :param contact_id: The ID of the contact to delete.
        :type contact_id: int
        :param db: The database session.
        :type db: Session
        :param current_user: The current authenticated user.
        :type current_user: User

        :return: Response indicating the contact was deleted.
        :rtype: str
    """
    contact = await repository_contacts.remove_contact(current_user, contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return 'Contact successfully deleted'


@router.get("/search")
async def search_contacts(query: str, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
        Search for contacts by a query string for the current user.

        :param query: The search query.
        :type query: str
        :param db: The database session.
        :type db: Session
        :param current_user: The current authenticated user.
        :type current_user: User

        :return: List of contacts matching the search query.
        :rtype: List[ContactResponse]
    """
    contacts = await repository_contacts.search_contacts(current_user, query, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nothing found")
    return contacts


@router.get("/search_birthdays")
async def search_birthdays(db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
        Search for contacts with birthdays for the current user.

        :param db: The database session.
        :type db: Session
        :param current_user: The current authenticated user.
        :type current_user: User

        :return: List of contacts with birthdays.
        :rtype: List[ContactResponse]
    """
    return await repository_contacts.get_birthdays(current_user, db)