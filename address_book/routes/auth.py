from fastapi import APIRouter, HTTPException, Depends, status, Security, Response, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from address_book.services.email import send_email
from address_book.database.db import get_db
from address_book.repository import users as repository_users
from address_book.services.auth import auth_service
from address_book.schemas import UserModel, UserResponse, TokenModel, RequestEmail


router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
        Frontend route for user's registration
        :param body: user's object body
        :type body: UserModel
        :param background_tasks: BackgroundTasks object
        :type background_tasks: BackgroundTasks
        :param request: A HTTP request object
        :type request: Request
        :param db: The database session
        :type db: Session

        :return: The dictionary of the new user object and a string 'User successfully created. Check your email for confirmation'
        :rtype: dict
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    return new_user.to_dict()


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
        Frontend route for user's login
        :param body: user's object body
        :type body: OAuth2PasswordRequestForm
        :param db: The database session
        :type db: Session

        :return: The dictionary of the access token, refresh token and a token type
        :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenModel)
async def updatee_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
        Frontend route for refreshing user's token
        :param credentials: credentials object
        :type credentials: HTTPAuthorizationCredentials
        :param db: The database session
        :type db: Session

        :return: The dictionary of the access token, refresh token and a token type
        :rtype: dict
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmedd_email(token: str, db: Session = Depends(get_db)):
    """
        Frontend route for confirming user's email
        :param token: token string
        :type token: str
        :param db: The database session
        :type db: Session

        :return: The dictionary {"message": "Email confirmed"}
        :rtype: dict
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
        Frontend route for sending an email for user so he can comfirm his email address
        :param body: request email object
        :type body: RequestEmail
        :param background_tasks: BackgroundTasks object
        :type background_tasks: BackgroundTasks
        :param request: A HTTP request object
        :type request: Request
        :param db: The database session
        :type db: Session

        :return: The dictionary {"message": "Check your email for confirmation."}
        :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}