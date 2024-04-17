from typing import Optional
from address_book.conf.config import settings
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from address_book.database.db import get_db
from address_book.repository import users as repository_users


class Auth:
    """
        Authentication service class.

        Attributes:
        - pwd_context: Password hashing context
        - SECRET_KEY: Secret key for JWT encoding and decoding
        - ALGORITHM: Algorithm for JWT encoding and decoding
        - oauth2_scheme: OAuth2 password bearer scheme for token authentication
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = settings.ALGORITHM
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    def verify_password(self, plain_password, hashed_password):
        """
            Verify the plain password against the hashed password.

            :param plain_password: The plain text password
            :type plain_password: str
            :param hashed_password: The hashed password
            :type hashed_password: str

            :return: True if the passwords match, False otherwise
            :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
            Get the hashed version of a password.

            :param password: The password to hash
            :type password: str

            :return: The hashed password
            :rtype: str
        """
        return self.pwd_context.hash(password)

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
            Generate a new access token.

            :param data: The data to encode in the token
            :type data: dict
            :param expires_delta: The expiration delta in seconds (default is 15 minutes)
            :type expires_delta: Optional[float]

            :return: The encoded access token
            :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
            Generate a new refresh token.

            :param data: The data to encode in the token
            :type data: dict
            :param expires_delta: The expiration delta in seconds (default is 7 days)
            :type expires_delta: Optional[float]

            :return: The encoded refresh token
            :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
            Decode and validate a refresh token.

            :param refresh_token: The refresh token to decode
            :type refresh_token: str

            :return: The email associated with the token
            :rtype: str
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
            Get the current authenticated user.

            :param token: The authentication token
            :type token: str
            :param db: The database session
            :type db: Session

            :return: The current authenticated user
            :rtype: User
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        return user

    async def create_email_token(self, data: dict):
        """
            Generate a new email verification token.

            :param data: The data to encode in the token
            :type data: dict

            :return: The encoded email verification token
            :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        """
            Decode and validate an email verification token.

            :param token: The email verification token
            :type token: str

            :return: The email associated with the token
            :rtype: str
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")


auth_service = Auth()
