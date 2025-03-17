from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlstuff import get_db, Link, User
from sqlalchemy.orm import Session
from typing import Optional
from handlers.auth import get_current_user_optional

router = APIRouter()

# Функция для формирования базового HTML с Bootstrap
def base_html(title: str, content: str, current_user: Optional[User] = None) -> str:
    nav = navbar(current_user)
    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        {nav}
        <div class="container mt-4">
            {content}
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

# Функция формирования навигационного меню
def navbar(current_user: Optional[User]) -> str:
    if current_user:
        return f"""
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <a class="navbar-brand" href="/">ShortLink</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav mr-auto">
                    <li class="nav-item"><a class="nav-link" href="/">Главная</a></li>
                    <li class="nav-item"><a class="nav-link" href="/dashboard">Личный кабинет</a></li>
                    <li class="nav-item"><a class="nav-link" href="/create">Создать ссылку</a></li>
                    <li class="nav-item"><a class="nav-link" href="/stats_page">Статистика</a></li>
                </ul>
                <span class="navbar-text mr-3">Привет, {current_user.username}</span>
                <a class="btn btn-outline-light" href="/logout">Выход</a>
            </div>
        </nav>
        """
    else:
        return """
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <a class="navbar-brand" href="/">ShortLink</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav mr-auto">
                    <li class="nav-item"><a class="nav-link" href="/">Главная</a></li>
                </ul>
                <a class="btn btn-outline-light mr-2" href="/register_page">Регистрация</a>
                <a class="btn btn-outline-light" href="/login_page">Вход</a>
            </div>
        </nav>
        """

# ================================
# Landing Page (Главная страница)
# ================================
@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    message = request.query_params.get("message", "")
    msg_html = f"<div class='alert alert-success'>{message}</div>" if message else ""
    
    if current_user:
        links = db.query(Link).filter(Link.user_id == current_user.id).all()
        links_html = "<h3>Ваши ссылки:</h3><table class='table table-striped'><thead><tr><th>Оригинальный URL</th><th>Короткая ссылка</th><th>Клики</th></tr></thead><tbody>"
        for l in links:
            links_html += f"<tr><td>{l.original_url}</td><td><a href='/links/{l.short_code}' target='_blank'>/links/{l.short_code}</a></td><td>{l.clicks}</td></tr>"
        links_html += "</tbody></table>"
    else:
        links_html = "<h2>Добро пожаловать!</h2><p>Пожалуйста, зарегистрируйтесь или войдите, чтобы начать пользоваться сервисом.</p>"
    
    create_form = """
    <h2>Создать короткую ссылку</h2>
    <form action="/links/shorten/form" method="post">
        <div class="form-group">
            <label>Оригинальный URL:</label>
            <input type="url" class="form-control" name="original_url" placeholder="https://example.com" required>
        </div>
        <div class="form-group">
            <label>Custom alias (необязательно):</label>
            <input type="text" class="form-control" name="custom_alias">
        </div>
        <div class="form-group">
            <label>Expires at (YYYY-MM-DD HH:MM:SS, необязательно):</label>
            <input type="text" class="form-control" name="expires_at" placeholder="2025-12-31 23:59:59">
        </div>
        <button type="submit" class="btn btn-primary">Создать ссылку</button>
    </form>
    """
    content = msg_html + create_form + links_html
    return HTMLResponse(content=base_html("Главная страница", content, current_user))

# ================================
# Страница регистрации
# ================================
@router.get("/register_page", response_class=HTMLResponse)
async def register_page(request: Request):
    content = """
    <h1>Регистрация</h1>
    <form action="/register" method="post">
        <div class="form-group">
            <label>Username:</label>
            <input type="text" class="form-control" name="username" required>
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" class="form-control" name="password" required>
        </div>
        <div class="form-group">
            <label>Подтверждение пароля:</label>
            <input type="password" class="form-control" name="confirm" required>
        </div>
        <button type="submit" class="btn btn-success">Зарегистрироваться</button>
    </form>
    <p>Уже зарегистрированы? <a href="/login_page">Войти</a></p>
    """
    return HTMLResponse(content=base_html("Регистрация", content))

# ================================
# Страница входа
# ================================
@router.get("/login_page", response_class=HTMLResponse)
async def login_page(request: Request):
    content = """
    <h1>Вход</h1>
    <form action="/login" method="post">
        <div class="form-group">
            <label>Username:</label>
            <input type="text" class="form-control" name="username" required>
        </div>
        <div class="form-group">
            <label>Password:</label>
            <input type="password" class="form-control" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary">Войти</button>
    </form>
    <p>Нет аккаунта? <a href="/register_page">Зарегистрироваться</a></p>
    """
    return HTMLResponse(content=base_html("Вход", content))

# ================================
# Личный кабинет (Dashboard)
# ================================
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    if not current_user:
        return RedirectResponse(url="/login_page?message=Сначала авторизуйтесь", status_code=303)
    links = db.query(Link).filter(Link.user_id == current_user.id).all()
    rows = ""
    for l in links:
        rows += f"""
        <tr>
            <td>{l.original_url}</td>
            <td><a href="/links/{l.short_code}" target="_blank">/links/{l.short_code}</a></td>
            <td>{l.clicks}</td>
            <td>{l.created_at.strftime("%Y-%m-%d %H:%M:%S")}</td>
            <td>{l.expires_at.strftime("%Y-%m-%d %H:%M:%S") if l.expires_at else "Нет"}</td>
            <td>
                <a class="btn btn-sm btn-warning" href="/edit_link?short_code={l.short_code}">Редактировать</a>
                <a class="btn btn-sm btn-danger" href="/delete_link?short_code={l.short_code}">Удалить</a>
                <a class="btn btn-sm btn-info" href="/stats_page?short_code={l.short_code}">Статистика</a>
            </td>
        </tr>
        """
    content = f"""
    <h1>Личный кабинет</h1>
    <h2>Ваши ссылки</h2>
    <table class="table table-bordered">
        <thead>
            <tr>
                <th>Оригинальный URL</th>
                <th>Короткая ссылка</th>
                <th>Клики</th>
                <th>Создана</th>
                <th>Истекает</th>
                <th>Действия</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    """
    return HTMLResponse(content=base_html("Личный кабинет", content, current_user))

# ================================
# Страница создания ссылки
# ================================
@router.get("/create", response_class=HTMLResponse)
async def create_page(request: Request, current_user=Depends(get_current_user_optional)):
    if not current_user:
        return RedirectResponse(url="/login_page?message=Сначала авторизуйтесь", status_code=303)
    content = """
    <h1>Создать ссылку</h1>
    <form action="/links/shorten/form" method="post">
        <div class="form-group">
            <label>Оригинальный URL:</label>
            <input type="url" class="form-control" name="original_url" placeholder="https://example.com" required>
            <small class="form-text text-muted">Пример: https://example.com</small>
        </div>
        <div class="form-group">
            <label>Custom alias (необязательно):</label>
            <input type="text" class="form-control" name="custom_alias">
            <small class="form-text text-muted">Например: mylink</small>
        </div>
        <div class="form-group">
            <label>Expires at (YYYY-MM-DD HH:MM:SS, необязательно):</label>
            <input type="text" class="form-control" name="expires_at" placeholder="2025-12-31 23:59:59">
            <small class="form-text text-muted">Формат: ГГГГ-ММ-ДД ЧЧ:ММ:СС</small>
        </div>
        <button type="submit" class="btn btn-primary">Создать ссылку</button>
    </form>
    """
    return HTMLResponse(content=base_html("Создать ссылку", content, current_user))

# ================================
# Страница статистики и аналитики
# ================================
@router.get("/stats_page", response_class=HTMLResponse)
async def stats_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    if not current_user:
        return RedirectResponse(url="/login_page?message=Сначала авторизуйтесь", status_code=303)
    short_code = request.query_params.get("short_code")
    stats_html = ""
    if short_code:
        link = db.query(Link).filter(Link.short_code == short_code, Link.user_id == current_user.id).first()
        if not link:
            stats_html = "<p>Ссылка не найдена или доступ запрещён.</p>"
        else:
            stats_html = f"""
            <h3>Статистика для ссылки {short_code}</h3>
            <ul class="list-group">
                <li class="list-group-item">Оригинальный URL: {link.original_url}</li>
                <li class="list-group-item">Создана: {link.created_at.strftime("%Y-%m-%d %H:%M:%S")}</li>
                <li class="list-group-item">Истекает: {link.expires_at.strftime("%Y-%m-%d %H:%M:%S") if link.expires_at else "Нет"}</li>
                <li class="list-group-item">Клики: {link.clicks}</li>
                <li class="list-group-item">Последний клик: {link.last_accessed_at.strftime("%Y-%m-%d %H:%M:%S") if link.last_accessed_at else "Нет"}</li>
            </ul>
            """
    else:
        stats_html = "<p>Введите короткий код для просмотра статистики.</p>"
    content = f"""
    <h1>Статистика и аналитика</h1>
    <form method="get" action="/stats_page" class="form-inline mb-3">
        <div class="form-group">
            <label class="mr-2">Введите короткий код:</label>
            <input type="text" name="short_code" class="form-control mr-2" required>
        </div>
        <button type="submit" class="btn btn-info">Показать статистику</button>
    </form>
    {stats_html}
    """
    return HTMLResponse(content=base_html("Статистика", content, current_user))

# ================================
# Страница редактирования ссылки
# (Изменён путь – теперь доступна по /edit_link)
# ================================
@router.get("/edit_link", response_class=HTMLResponse)
async def edit_link_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    if not current_user:
        return RedirectResponse(url="/login_page?message=Сначала авторизуйтесь", status_code=303)
    short_code = request.query_params.get("short_code")
    if not short_code:
        return HTMLResponse(content=base_html("Ошибка", "<p>Нет короткого кода.</p>", current_user))
    link = db.query(Link).filter(Link.short_code == short_code, Link.user_id == current_user.id).first()
    if not link:
        return HTMLResponse(content=base_html("Ошибка", "<p>Ссылка не найдена или доступ запрещён.</p>", current_user))
    content = f"""
    <h1>Редактировать ссылку</h1>
    <form action="/links/update" method="post">
        <input type="hidden" name="short_code" value="{link.short_code}">
        <div class="form-group">
            <label>Оригинальный URL:</label>
            <input type="url" class="form-control" name="original_url" value="{link.original_url}" required>
        </div>
        <button type="submit" class="btn btn-warning">Сохранить изменения</button>
    </form>
    """
    return HTMLResponse(content=base_html("Редактировать ссылку", content, current_user))

# ================================
# Страница удаления ссылки (подтверждение)
# (Изменён путь – теперь доступна по /delete_link)
# ================================
@router.get("/delete_link", response_class=HTMLResponse)
async def delete_link_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    if not current_user:
        return RedirectResponse(url="/login_page?message=Сначала авторизуйтесь", status_code=303)
    short_code = request.query_params.get("short_code")
    if not short_code:
        return HTMLResponse(content=base_html("Ошибка", "<p>Нет короткого кода.</p>", current_user))
    link = db.query(Link).filter(Link.short_code == short_code, Link.user_id == current_user.id).first()
    if not link:
        return HTMLResponse(content=base_html("Ошибка", "<p>Ссылка не найдена или доступ запрещён.</p>", current_user))
    content = f"""
    <h1>Удалить ссылку</h1>
    <p>Вы уверены, что хотите удалить ссылку <strong>{link.short_code}</strong>?</p>
    <form action="/links/delete" method="post">
        <input type="hidden" name="short_code" value="{link.short_code}">
        <button type="submit" class="btn btn-danger">Удалить</button>
        <a href="/dashboard" class="btn btn-secondary">Отмена</a>
    </form>
    """
    return HTMLResponse(content=base_html("Удалить ссылку", content, current_user))
