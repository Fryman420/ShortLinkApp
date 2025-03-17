from fastapi import APIRouter, HTTPException, Depends, status, Form, Header, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm
from sqlstuff import get_db, User
from pydantic_stuff import UserCreate
from passlib.context import CryptContext

router = APIRouter()

# Инициализация контекста для хэширования паролей (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ================================
# Эндпоинты регистрации
# ================================

# API-эндпоинт для регистрации
@router.post("/users/register", status_code=status.HTTP_201_CREATED)
def register_user_api(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким username уже существует.")
    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"Пользователь {new_user.username} зарегистрирован", "username": new_user.username}

# HTML-эндпоинт для регистрации через форму (с подтверждением пароля)
@router.post("/register")
async def register_user_form(
    username: str = Form(...),
    password: str = Form(...),
    confirm: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm:
        return HTMLResponse(
            content="<h3>Пароли не совпадают.</h3><a href='/register_page'>Назад</a>",
            status_code=400
        )
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return HTMLResponse(
            content=f"<h3>Пользователь с username '{username}' уже существует.</h3><a href='/register_page'>Назад</a>",
            status_code=400
        )
    new_user = User(
        username=username,
        hashed_password=get_password_hash(password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return RedirectResponse(url="/?message=Регистрация прошла успешно", status_code=303)

# ================================
# Эндпоинты логина
# ================================

# API-эндпоинт для логина (OAuth2PasswordRequestForm)
@router.post("/users/login")
def login_user_api(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    # Простейший вариант: токен – это username
    return {"token": user.username}

# HTML-эндпоинт для логина через форму
@router.post("/login")
async def login_user_form(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return HTMLResponse(
            content="<h3>Неверное имя пользователя или пароль.</h3><a href='/login_page'>Назад</a>",
            status_code=401
        )
    response = RedirectResponse(url="/?message=Вход выполнен успешно", status_code=303)
    # Устанавливаем cookie "token" для аутентификации
    response.set_cookie(key="token", value=user.username)
    return response

# Эндпоинт для выхода (logout)
@router.get("/logout")
def logout_user():
    response = RedirectResponse(url="/?message=Вы успешно вышли", status_code=303)
    response.delete_cookie("token")
    return response

# ================================
# Вспомогательные функции аутентификации
# ================================

def get_current_user(authorization: Optional[str] = Header(None), token: Optional[str] = Cookie(None), db: Session = Depends(get_db)) -> User:
    token_value = None
    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Неверный формат заголовка авторизации.")
        token_value = authorization[len("Bearer "):]
    elif token:
        token_value = token
    if not token_value:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    user = db.query(User).filter(User.username == token_value).first()
    if not user:
        raise HTTPException(status_code=401, detail="Неверный токен или пользователь не найден.")
    return user

def get_current_user_optional(authorization: Optional[str] = Header(None), token: Optional[str] = Cookie(None), db: Session = Depends(get_db)) -> Optional[User]:
    token_value = None
    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Неверный формат заголовка авторизации.")
        token_value = authorization[len("Bearer "):]
    elif token:
        token_value = token
    if token_value:
        user = db.query(User).filter(User.username == token_value).first()
        return user
    return None
