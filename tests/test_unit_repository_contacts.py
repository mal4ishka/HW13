import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from address_book.database.models import Contact, User
from address_book.schemas import *
from address_book.repository.contacts import (
    get_contacts,
    get_contact,
    create_contact,
    remove_contact,
    update_contact,
    search_contacts,
    get_birthdays
)


class TestRepositoryContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_get_contacts(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.query().filter().all.return_value = contacts
        result = await get_contacts(user=self.user, db=self.session)
        self.assertEqual(result, contacts)

    async def test_get_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_get_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_create_contact(self):
        contact = Contact(first_name="first_name", last_name="last_name", email="email@gmail.com", phone="0957800062",
                          birthday="1986-03-17", user_id=self.user.id)
        self.session.query().filter().all.return_value = contact
        result = await create_contact(body=contact, user=self.user, db=self.session)
        self.assertEqual(result.first_name, contact.first_name)
        self.assertEqual(result.last_name, contact.last_name)
        self.assertEqual(result.email, contact.email)
        self.assertEqual(result.phone, contact.phone)
        self.assertEqual(result.birthday, contact.birthday)
        self.assertEqual(result.user_id, self.user.id)
        self.assertTrue(hasattr(result, "id"))

    async def test_remove_contact_found(self):
        contact = Contact()
        self.session.query().filter().first.return_value = contact
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_remove_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_update_contact_found(self):
        contact = Contact(first_name="first_name", last_name="last_name", email="email@gmail.com", phone="0957800062",
                          birthday="1986-03-17", user_id=self.user.id)
        self.session.query().filter().first.return_value = contact
        self.session.commit.return_value = None
        result = await update_contact(contact_id=self.user.id, body=contact, user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_update_note_not_found(self):
        contact = Contact(first_name="first_name", last_name="last_name", email="email@gmail.com", phone="0957800062",
                          birthday="1986-03-17", user_id=self.user.id)
        self.session.query().filter().first.return_value = None
        self.session.commit.return_value = None
        result = await update_contact(contact_id=self.user.id, body=contact, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_search_contacts_found(self):
        contact = Contact(first_name="first_name", last_name="last_name", email="email@gmail.com", phone="0957800062",
                          birthday="1986-03-17", user_id=self.user.id)
        self.session.query().filter().filter().all.return_value = contact
        self.session.commit.return_value = None
        result = await search_contacts(query='test', user=self.user, db=self.session)
        self.assertEqual(result, contact)

    async def test_search_contacts_not_found(self):
        contact = Contact(first_name="first_name", last_name="last_name", email="email@gmail.com", phone="0957800062",
                          birthday="1986-03-17", user_id=self.user.id)
        self.session.query().filter().filter().all.return_value = None
        self.session.commit.return_value = None
        result = await search_contacts(query='email', user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_search_birthdays_found(self):
        contact = Contact(first_name="first_name", last_name="last_name", email="email@gmail.com", phone="0957800062",
                          birthday="1986-04-23", user_id=self.user.id)
        self.session.query().filter().all.return_value = contact
        self.session.commit.return_value = None
        result = await get_birthdays(user=self.user, db=self.session)
        self.assertEqual(result, [contact])

    async def test_search_birthdays_not_found(self):
        contact = Contact(first_name="first_name", last_name="last_name", email="email@gmail.com", phone="0957800062",
                          birthday="1986-03-17", user_id=self.user.id)
        self.session.query().filter().all.return_value = None
        self.session.commit.return_value = None
        result = await get_birthdays(user=self.user, db=self.session)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()