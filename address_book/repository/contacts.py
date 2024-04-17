from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Type
from address_book.database.models import Contact, User
from address_book.schemas import ContactBase
from datetime import datetime


async def get_contacts(user: User, db: Session) -> List[Type[Contact]]:
    """
        Retrieves a list of contacts for a specific user.
        :param user: The user to retrieve contacts for
        :type user: User
        :param db: The database session.
        :type db: Session
        :return: A list of contacts.
        :rtype: List[Type[Contact]]
    """
    return db.query(Contact).filter(Contact.user_id == user.id).all()


async def get_contact(user: User, contact_id: int, db: Session) -> Type[Contact]:
    """
        Retrieves first contact for a specific user.
        :param user: The user to retrieve contact for
        :type user: User
        :param db: The database session.
        :type db: Session
        :return: A list of contacts.
        :rtype: Type[Contact]
    """
    return db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()


async def create_contact(user: User, body: ContactBase, db: Session):
    """
        Creates a new contact in database for a specific user
        :param user: The user to create contact for
        :type user: User
        :param body: body of the contact
        :type body: ContactBase
        :param db: The database session.
        :type db: Session
    """
    contact = Contact(first_name=body.first_name, last_name=body.last_name, email=body.email, phone=body.phone,
                      birthday=body.birthday, user_id=user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def update_contact(user: User, contact_id: int, body: ContactBase, db: Session) -> Contact | None:
    """
        Updates contact in database for a specific user
        :param user: The user to update contact for
        :type user: User
        :param contact_id: Contact's id from the database
        :type contact_id: int
        :param body: body of the contact
        :type body: ContactBase
        :param db: The database session.
        :type db: Session

        :return: Contact's object if found
        :rtype: Contact | None
    """
    contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone = body.phone
        contact.birthday = body.birthday
        contact.user_id = user.id
        db.commit()
        return contact


async def remove_contact(user: User, contact_id: int, db: Session) -> Type[Contact] | None:
    """
        Removes contact in database for a specific user
        :param user: The user to remove contact for
        :type user: User
        :param contact_id: Contact's id from the database
        :type contact_id: int
        :param db: The database session.
        :type db: Session

        :return: Contact's object if deleted
        :rtype: Type[Contact] | None
    """
    contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if contact:
        db.delete(contact)
        db.commit()
        return contact


async def search_contacts(user: User, query: str, db: Session) -> List[Type[Contact]]:
    """
        Retrieves a list of contacts for a specific user by search query. Function searches contacts only by Contact.first_name, Contact.last_name and Contact.email
        :param user: The user to retrieve contacts for
        :type user: User
        :param query: search query text
        :type query: str
        :param db: The database session.
        :type db: Session

        :return: A list of contacts.
        :rtype: List[Type[Contact]]
    """
    result = db.query(Contact).filter(Contact.user_id == user.id).filter(or_(Contact.first_name.like(f'%{query}%'),
                                        Contact.last_name.like(f'%{query}%'), Contact.email.like(f'%{query}%'))).all()
    if result:
        return result


async def get_birthdays(user: User, db: Session) -> List[Type[Contact]]:
    """
        Retrieves a list of contacts for a specific user that have birthday coming up in the next 7 days
        :param user: The user to retrieve contacts for
        :type user: User
        :param db: The database session.
        :type db: Session

        :return: A list of contacts.
        :rtype: List[Type[Contact]]
    """
    contacts = db.query(Contact).filter(Contact.user_id == user.id).all()

    response = []
    # for contact in contacts:
    #     print(contact.first_name, contact.last_name, contact.email, contact.phone, contact.birthday)

    if contacts:
        for contact in contacts:

            today = datetime.today()
            current_year = today.year
            next_year = current_year + 1

            contact_birthday = datetime.strptime(contact.birthday, "%Y-%m-%d")

            # substitute bday year to the current one to make possible to define if bday is ahead or in the past
            if (today.month == 12 and today.day in [26, 27, 28, 29, 30, 31]) and (
                    contact_birthday.month == 1 and contact_birthday.day in [1, 2, 3, 4, 5, 6]):
                bday = contact_birthday.replace(year=next_year)
            else:
                bday = contact_birthday.replace(year=current_year)

            # Calculate days before of after today to the bday. Positive means that bday is ahead. Negative - in the past
            delta = (bday - today).days

            # If delta is in range 0-6, then we have to add it to the final list
            if 0 <= delta <= 6:
                response.append(contact)

        return response