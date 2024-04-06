from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Type
from address_book.database.models import Contact, User
from address_book.schemas import ContactBase
from datetime import datetime


async def get_contacts(user: User, db: Session) -> List[Type[Contact]]:
    return db.query(Contact).filter(Contact.user_id == user.id).all()


async def get_contact(user: User, contact_id: int, db: Session) -> Type[Contact]:
    return db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()


async def create_contact(user: User, body: ContactBase, db: Session) -> str:
    contact = Contact(first_name=body.first_name, last_name=body.last_name, email=body.email, phone=body.phone,
                      birthday=body.birthday, user_id=user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)


async def update_contact(user: User, contact_id: int, body: ContactBase, db: Session) -> Contact | None:
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
    contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if contact:
        db.delete(contact)
        db.commit()
        return contact


async def search_contacts(user: User, query: str, db: Session) -> List[Type[Contact]]:
    return db.query(Contact).filter(Contact.user_id == user.id).filter(or_(Contact.first_name.like(f'%{query}%'), Contact.last_name.like(f'%{query}%'),
                                        Contact.email.like(f'%{query}%'))).all()


async def get_birthdays(user: User, db: Session) -> List[Type[Contact]]:
    contacts = db.query(Contact).filter(Contact.user_id == user.id).all()

    response = []

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
