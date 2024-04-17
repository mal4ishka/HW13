import unittest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from address_book.routes.auth import router
from sqlalchemy.orm import Session
from address_book.routes.contacts import *
from datetime import datetime
from address_book.database.models import Contact
import logging
logging.basicConfig(level=logging.ERROR)


class TestRoutesContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.client = TestClient(router)
        self.db = MagicMock(spec=Session)
        self.user = User(id=1, username='username', email='email@gmail.com', password='password',
                    created_at=datetime.now(), avatar=None, refresh_token=None, confirmed=False)
        self.contact = Contact(id=1, first_name='first_name', last_name='last_name', email='email@gamil.com',
                          phone='1111111111', birthday='1986-04-23', user_id=self.user.id)

    async def test_read_contacts_found(self):
        self.db.query().filter().all.return_value = self.contact
        response = await read_contacts(db=self.db, current_user=self.user)
        self.assertEqual(response, self.contact)

    async def test_read_contacts_not_found(self):
        self.db.query().filter().all.return_value = None
        response = await read_contacts(db=self.db, current_user=self.user)
        self.assertEqual(response, None)

    async def test_read_contact_found(self):
        self.db.query().filter().first.return_value = self.contact
        response = await read_contact(contact_id=self.contact.id, db=self.db, current_user=self.user)
        self.assertEqual(response, self.contact)

    async def test_read_contact_not_found(self):
        self.db.query().filter().first.return_value = None

        with self.assertRaises(HTTPException) as context:
            await read_contact(contact_id=self.contact.id, db=self.db, current_user=self.user)

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Contact not found")

    async def test_create_contact(self):
        self.db.query().filter().all.return_value = self.contact
        result = await create_new(body=self.contact, current_user=self.user, db=self.db)
        self.assertEqual(result.status_code, 201)

    async def test_update_contact_found(self):
        contact_new = ContactBase(first_name='first_name', last_name='last_name', email='email@gamil.com',
                              phone='1111111111', birthday='2222-22-22')
        self.db.query().filter().first.return_value = self.contact
        response = await update_contact(body=contact_new, contact_id=1, current_user=self.user, db=self.db)
        self.assertIsNotNone(response)

    async def test_update_contact_not_found(self):
        contact_new = ContactBase(first_name='first_name', last_name='last_name', email='email@gamil.com',
                              phone='1111111111', birthday='2222-22-22')
        self.db.query().filter().first.return_value = None
        with self.assertRaises(HTTPException) as context:
            await update_contact(body=contact_new, contact_id=1, current_user=self.user, db=self.db)

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Contact not found")

    async def test_remove_contact_found(self):
        self.db.query().filter().first.return_value = self.contact
        response = await remove_contact(contact_id=self.contact.id, db=self.db, current_user=self.user)
        self.assertEqual(response, 'Contact successfully deleted')

    async def test_remove_contact_not_found(self):
        self.db.query().filter().first.return_value = None
        with self.assertRaises(HTTPException) as context:
            await remove_contact(contact_id=self.contact.id, db=self.db, current_user=self.user)

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Contact not found")

    async def test_search_contacts_found(self):
        self.db.query().filter().filter().all.return_value = self.contact
        response = await search_contacts(query='first_name', db=self.db, current_user=self.user)
        self.assertIsNotNone(response)

    async def test_search_contacts_not_found(self):
        self.db.query().filter().filter().all.return_value = None

        with self.assertRaises(HTTPException) as context:
            await search_contacts(query='test', db=self.db, current_user=self.user)

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Nothing found")

    async def test_search_birthdays_found(self):
        self.db.query().filter().all.return_value = self.contact
        response = await search_birthdays(current_user=self.user, db=self.db)
        self.assertEqual([self.contact], response)

    async def test_search_birthdays_not_found(self):
        self.db.query().filter().all.return_value = None
        response = await search_birthdays(current_user=self.user, db=self.db)
        self.assertIsNone(response)


if __name__ == '__main__':
    unittest.main()