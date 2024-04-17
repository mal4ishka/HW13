import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from address_book.database.models import User
from address_book.services.auth import Auth
from datetime import datetime, timedelta
from jose import jwt
from address_book.conf.config import settings
from fastapi import HTTPException, status
import logging
logging.basicConfig(level=logging.ERROR)


class TestServicesAuth(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.auth = Auth()
        self.auth.SECRET_KEY = settings.SECRET_KEY
        self.auth.ALGORITHM = settings.ALGORITHM

    async def test_verify_password_correct(self):
        hashed_password = self.auth.pwd_context.hash("password123")
        assert Auth().verify_password("password123", hashed_password) is True

    async def test_verify_password_incorrect(self):
        hashed_password = self.auth.pwd_context.hash("password123")
        assert Auth().verify_password("wrongpassword", hashed_password) is False

    async def test_get_password_hash(self):
        password = "password123"
        hashed_password = self.auth.get_password_hash(password)
        assert Auth().verify_password(password, hashed_password) is True

    async def test_create_access_token(self):
        data = {"sub": "user@example.com"}
        expires_delta = 3600
        encoded_access_token = await self.auth.create_access_token(data, expires_delta)
        decoded_token = jwt.decode(encoded_access_token, self.auth.SECRET_KEY, algorithms=[self.auth.ALGORITHM])
        assert decoded_token["sub"] == "user@example.com"

    async def test_decode_refresh_token_valid(self):
        token_data = {"sub": "user@example.com", "scope": "refresh_token"}
        token = jwt.encode(token_data, self.auth.SECRET_KEY, algorithm=self.auth.ALGORITHM)
        decoded_email = await self.auth.decode_refresh_token(token)
        assert decoded_email == "user@example.com"

    def test_decode_refresh_token_invalid_scope(self):
        token_data = {"sub": "user@example.com", "scope": "access_token"}
        token = jwt.encode(token_data, self.auth.SECRET_KEY, algorithm=self.auth.ALGORITHM)
        try:
            self.auth.decode_refresh_token(token)
        except HTTPException as e:
            assert e.status_code == status.HTTP_401_UNAUTHORIZED
            assert e.detail == "Invalid scope for token"

    def test_decode_refresh_token_invalid_token(self):
        token = "invalid_token"
        try:
            self.auth.decode_refresh_token(token)
        except HTTPException as e:
            assert e.status_code == status.HTTP_401_UNAUTHORIZED
            assert e.detail == "Could not validate credentials"

    async def test_get_current_user_valid_token(self):
        token_data = {"sub": "user@example.com", "scope": "access_token"}
        token = jwt.encode(token_data, self.auth.SECRET_KEY, algorithm=self.auth.ALGORITHM)

        mock_db = MagicMock(spec=Session)
        user = User(id=1, username='testuser', email='user@example.com', password='password',
                         created_at=datetime.now(), avatar=None, refresh_token=None, confirmed=False)
        mock_db.query(User).filter().first.return_value = user
        result = await self.auth.get_current_user(token=token, db=mock_db)
        assert result == user

    async def test_get_current_user_invalid_token(self):
        token = "invalid_token"
        mock_db = MagicMock(spec=Session)
        try:
            await self.auth.get_current_user(token=token, db=mock_db)
        except HTTPException as e:
            assert e.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_current_user_no_email_in_token(self):
        token_data = {"sub": None, "scope": "access_token"}
        token = jwt.encode(token_data, self.auth.SECRET_KEY, algorithm=self.auth.ALGORITHM)
        mock_db = MagicMock(spec=Session)
        try:
            await self.auth.get_current_user(token=token, db=mock_db)
        except HTTPException as e:
            assert e.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_create_email_token(self):
        data = {'sub': 'email@email.com'}
        expire = datetime.utcnow() + timedelta(days=7)
        data.update({"iat": datetime.utcnow(), "exp": expire})
        token = await self.auth.create_email_token(data)
        decoded_token = jwt.encode(data, self.auth.SECRET_KEY, algorithm=self.auth.ALGORITHM)
        assert token == decoded_token

    async def test_get_email_from_token_success(self):
        payload = {
            'sub': 'email@gmail.com',
            'scope': 'refresh_token',
            'exp': datetime.utcnow() + timedelta(minutes=30),
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        email = await Auth().get_email_from_token(token=token)
        self.assertEqual(payload['sub'], email)

    async def test_get_email_from_token_failed(self):
        payload = {
            'sub': 'email@gmail.com',
            'scope': 'refresh_token',
            'exp': datetime.utcnow() + timedelta(minutes=30),
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        payload['sub'] = 'email1@gmail.com'
        email = await Auth().get_email_from_token(token=token)
        self.assertNotEqual(payload['sub'], email)


if __name__ == '__main__':
    unittest.main()