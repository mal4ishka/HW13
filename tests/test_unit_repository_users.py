import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from address_book.database.models import Contact, User
from address_book.schemas import *
from address_book.repository.users import *
from datetime import datetime


class TestRepositoryUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, username='username', email='email@gmail.com', password='password',
                         created_at=datetime.now(), avatar='str', refresh_token='str', confirmed=False)

    async def test_get_user_by_email_found(self):
        user = User()
        self.session.query().filter().first.return_value = user
        result = await get_user_by_email(email='str', db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_email_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_user_by_email(email='str', db=self.session)
        self.assertIsNone(result)

    async def test_create_user(self):
        user_data = UserModel(username='username', email='email@example.com', password='password')
        avatar_url = 'http://example.com/avatar.jpg'
        gravatar_mock = MagicMock()
        gravatar_mock.get_image.return_value = avatar_url
        with patch('address_book.repository.users.Gravatar', return_value=gravatar_mock):
            result = await create_user(body=user_data, db=self.session)
            self.assertIsNotNone(result)
            self.assertEqual(result.username, user_data.username)
            self.assertEqual(result.email, user_data.email)
            self.assertEqual(result.avatar, avatar_url)

    async def test_update_token(self):
        await update_token(user=self.user, token='new_token', db=self.session)

    async def test_confirm_email(self):
        await confirmed_email(email=self.user.email, db=self.session)

    async def test_update_avatar(self):
        self.session.query().filter().first.return_value = self.user
        updated_user = await update_avatar(email=self.user.email, url=self.user.avatar, db=self.session)

        self.assertEqual(updated_user.avatar, self.user.avatar)
        self.session.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()