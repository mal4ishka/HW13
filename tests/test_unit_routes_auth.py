import unittest
from fastapi import BackgroundTasks, Request
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from address_book.repository import users as repository_users
from address_book.routes.auth import router, signup, login, updatee_token, confirmedd_email, request_email
from address_book.repository.users import *
from fastapi import HTTPException, status
from address_book.services.auth import auth_service
from address_book.conf.config import settings
from jose import jwt
from sqlalchemy.orm import Session
import logging
logging.basicConfig(level=logging.ERROR)


class TestRoutesAuth(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.client = TestClient(router)
        self.db = MagicMock(spec=Session)

    async def test_signup_success(self):
        body = UserModel(username='testuser', email='test@example.com', password='password')
        new_user_db = User(id=1, username='testuser', email='test@example.com', password='password',
                           created_at=datetime.now(), avatar=None, refresh_token=None, confirmed=False)
        background_tasks = BackgroundTasks()
        request = MagicMock(spec=Request)
        request.base_url = 'http://example.com'

        self.db.query().filter().first.return_value = None
        self.db.commit.return_value = None
        repository_users.create_user.return_value = new_user_db
        response_data = await signup(body=body, background_tasks=background_tasks, request=request, db=self.db)

        self.assertIsNotNone(response_data)
        self.assertEqual(response_data.username, new_user_db.username)
        self.assertEqual(response_data.email, new_user_db.email)

    async def test_signup_user_already_exists(self):
        body = UserModel(username='testuser', email='test@example.com', password='password')
        new_user_db = User(id=1, username='testuser', email='test@example.com', password='password',
                           created_at=datetime.now(), avatar=None, refresh_token=None, confirmed=False)
        background_tasks = BackgroundTasks()
        request = MagicMock(spec=Request)
        request.base_url = 'http://example.com'

        self.db.query().filter().first.return_value = new_user_db
        self.db.commit.return_value = None
        repository_users.create_user.return_value = new_user_db

        with self.assertRaises(HTTPException) as cm:
            await signup(body=body, background_tasks=background_tasks, request=request, db=self.db)

        self.assertEqual(cm.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(cm.exception.detail, "Account already exists")

    async def test_login_success(self):
        user = User(id=1, username='testuser', email='test@example.com', password='password', created_at=datetime.now(),
                    avatar=None, refresh_token=None, confirmed=True)
        user.password = auth_service.get_password_hash(user.password)
        self.db.query().filter().first.return_value = user
        body = User(username='testuser', password='password')
        response = await login(body=body, db=self.db)
        self.assertEqual(dict, type(response))

    async def test_login_wrong_password(self):
        user = User(id=1, username='testuser', email='test@example.com', password='password', created_at=datetime.now(),
                    avatar=None, refresh_token=None, confirmed=True)
        user.password = auth_service.get_password_hash(user.password)
        self.db.query().filter().first.return_value = user
        body = User(username='testuser', password='password1')

        with self.assertRaises(HTTPException) as context:
            await login(body=body, db=self.db)

        self.assertEqual(context.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(context.exception.detail, "Invalid password")

    async def test_login_email_not_confirmed(self):
        user = User(id=1, username='testuser', email='test@example.com', password='password', created_at=datetime.now(),
                    avatar=None, refresh_token=None, confirmed=False)
        user.password = auth_service.get_password_hash(user.password)
        self.db.query().filter().first.return_value = user
        body = User(username='testuser', password='password')

        with self.assertRaises(HTTPException) as context:
            await login(body=body, db=self.db)

        self.assertEqual(context.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(context.exception.detail, "Email not confirmed")

    async def test_login_user_not_found(self):
        self.db.query().filter().first.return_value = None
        body = User(username='testuser', password='password', email='email@gmail.com')

        with self.assertRaises(HTTPException) as context:
            await login(body=body, db=self.db)

        self.assertEqual(context.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(context.exception.detail, "Invalid email")

    async def test_refresh_token(self):
        user = User(id=1, username='testuser', email='test@example.com', password='password', created_at=datetime.now(),
                    avatar=None, refresh_token='token', confirmed=True)
        self.db.query().filter().first.return_value = user

        payload = {
            'sub': user.email,
            'scope': 'refresh_token',
            'exp': datetime.utcnow() + timedelta(minutes=15),
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        user.refresh_token = token
        response_data = await updatee_token(credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token), db=self.db)
        self.assertIn("access_token", response_data)
        self.assertIn("refresh_token", response_data)
        self.assertEqual(response_data["token_type"], "bearer")

    async def test_confirm_user_email_success(self):
        user = User(id=1, username='testuser', email='test@example.com', password='password', created_at=datetime.now(),
                    avatar=None, refresh_token='token', confirmed=False)
        self.db.query().filter().first.return_value = user

        payload = {
            'sub': user.email,
            'scope': 'refresh_token',
            'exp': datetime.utcnow() + timedelta(minutes=30),
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        user.refresh_token = token
        response_data = await confirmedd_email(token=token, db=self.db)
        self.assertEqual(response_data, {'message': 'Email confirmed'})

    async def test_confirm_user_email_already_confirmed(self):
        user = User(id=1, username='testuser', email='test@example.com', password='password', created_at=datetime.now(),
                    avatar=None, refresh_token='token', confirmed=True)
        self.db.query().filter().first.return_value = user

        payload = {
            'sub': user.email,
            'scope': 'refresh_token',
            'exp': datetime.utcnow() + timedelta(minutes=30),
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        user.refresh_token = token
        response_data = await confirmedd_email(token=token, db=self.db)
        self.assertEqual(response_data, {"message": "Your email is already confirmed"})

    async def test_confirm_user_email_not_found(self):
        user = User(id=1, username='testuser', email='test@example.com', password='password', created_at=datetime.now(),
                    avatar=None, refresh_token='token', confirmed=True)
        self.db.query().filter().first.return_value = None

        payload = {
            'sub': user.email,
            'scope': 'refresh_token',
            'exp': datetime.utcnow() + timedelta(minutes=30),
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        user.refresh_token = token

        with self.assertRaises(HTTPException) as context:
            await confirmedd_email(token=token, db=self.db)

        self.assertEqual(context.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(context.exception.detail, "Verification error")

    async def test_email_confirmed(self):
        user = User(id=1, username='testuser', email='test@example.com', password='password', created_at=datetime.now(),
                    avatar=None, refresh_token='token', confirmed=True)
        self.db.query().filter().first.return_value = user
        background_tasks = BackgroundTasks()
        request = MagicMock(spec=Request)
        request.base_url = 'http://example.com'
        response_data = await request_email(body=user, background_tasks=background_tasks, request=request, db=self.db)
        self.assertEqual(response_data, {'message': 'Your email is already confirmed'})

    async def test_email_not_confirmed(self):
        user = User(id=1, username='testuser', email='test@example.com', password='password', created_at=datetime.now(),
                    avatar=None, refresh_token='token', confirmed=False)
        self.db.query().filter().first.return_value = user
        background_tasks = BackgroundTasks()
        request = MagicMock(spec=Request)
        request.base_url = 'http://example.com'
        response_data = await request_email(body=user, background_tasks=background_tasks, request=request, db=self.db)
        self.assertEqual(response_data, {"message": "Check your email for confirmation."})


if __name__ == '__main__':
    unittest.main()