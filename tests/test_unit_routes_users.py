import unittest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from address_book.routes.auth import router
from sqlalchemy.orm import Session
from address_book.routes.users import *
from datetime import datetime
from fastapi import UploadFile
import logging
logging.basicConfig(level=logging.ERROR)


class TestRoutesUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.client = TestClient(router)
        self.db = MagicMock(spec=Session)

    async def test_get_me(self):
        user = User(id=1, username='nesterovvlad@gmail.com', email='nesterovvlad@gmail.com', password='*4a&WLG,,LuU??G',
                    created_at=datetime.now(), avatar=None, refresh_token=None, confirmed=False)
        self.db.query().filter().first.return_value = user
        response =await read_users_me(current_user=user)
        self.assertEqual(User, type(response))

    async def test_update_avatar(self):
        user = User(id=1, username='testuser', email='test@example.com', password='password',
                    created_at=datetime.now(), avatar=None, refresh_token=None, confirmed=False)
        self.db.query().filter().first.return_value = user

        with open('avatar.jpg', "rb") as file:
            upload_file = UploadFile(filename="avatar.jpg", file=file)
            response = await update_avatar_user(file=upload_file, current_user=user, db=self.db)
        self.assertEqual(User, type(response))


if __name__ == '__main__':
    unittest.main()