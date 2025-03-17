from fastapi import APIRouter, HTTPException, Depends, status, Form, Header, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from sqlstuff import get_db, Link
from pydantic_stuff import LinkCreate, LinkUpdate, LinkStats
from uuid_stuff import generate_short_code
from handlers.auth import get_current_user, get_current_user_optional
from cache import get_cache, set_cache, delete_cache  # Импорт функций кэша

router = APIRouter()

def get_link(short_code: str, db: Session) -> Link:
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Ссылка не найдена.")
    return link

# ================================
# Создание ссылки
# ================================
@router.post("/links/shorten", status_code=status.HTTP_201_CREATED)
def create_link_api(
    link: LinkCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    short_code = link.custom_alias if link.custom_alias else generate_short_code()
    existing_link = db.query(Link).filter(Link.short_code == short_code).first()
    if existing_link:
        raise HTTPException(status_code=400, detail="Код занят.")
    new_link = Link(
        short_code=short_code,
        original_url=str(link.original_url),  # Приведение к строке
        expires_at=link.expires_at,
        user_id=current_user.id if current_user else None
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return {"short_code": short_code, "original_url": new_link.original_url}

@router.post("/links/shorten/form")
def create_link_form(
    original_url: str = Form(...),
    custom_alias: Optional[str] = Form(None),
    expires_at: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    short_code = custom_alias if custom_alias else generate_short_code()
    existing_link = db.query(Link).filter(Link.short_code == short_code).first()
    if existing_link:
        return HTMLResponse(
            content=f"<h3>Код {short_code} уже занят.</h3><a href='/create'>Назад</a>",
            status_code=400
        )
    expires_dt = None
    if expires_at:
        try:
            expires_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return HTMLResponse(
                content="<h3>Неверный формат даты.</h3><a href='/create'>Назад</a>",
                status_code=400
            )
    new_link = Link(
        short_code=short_code,
        original_url=original_url,
        expires_at=expires_dt,
        user_id=current_user.id if current_user else None
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return RedirectResponse(url=f"/?message=Ссылка создана: /links/{short_code}", status_code=303)

# ================================
# Перенаправление по короткой ссылке
# ================================
@router.get("/links/{short_code}")
def redirect_link(short_code: str, db: Session = Depends(get_db)):
    link = get_link(short_code, db)
    if link.expires_at and datetime.utcnow() > link.expires_at:
        raise HTTPException(status_code=410, detail="Ссылка уже слишком старая.")
    link.clicks += 1
    link.last_accessed_at = datetime.utcnow()
    db.commit()
    return RedirectResponse(url=link.original_url, status_code=302)

# ================================
# Получение статистики по ссылке (API) с кэшированием
# ================================
@router.get("/links/{short_code}/stats", response_model=LinkStats)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    cache_key = f"link_stats_{short_code}"
    cached_stats = get_cache(cache_key)
    if cached_stats:
        return cached_stats
    link = get_link(short_code, db)
    stats = LinkStats(
        original_url=str(link.original_url),
        created_at=link.created_at,
        expires_at=link.expires_at,
        clicks=link.clicks,
        last_accessed_at=link.last_accessed_at
    )
    set_cache(cache_key, stats, ttl=60)
    return stats

# ================================
# Обновление ссылки
# ================================
@router.put("/links/{short_code}")
def update_link_api(
    short_code: str,
    link_data: LinkUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    link = get_link(short_code, db)
    if not link.user_id or link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой ссылке")
    # Преобразуем HttpUrl в строку для сохранения в БД
    link.original_url = str(link_data.original_url)
    db.commit()
    delete_cache(f"link_stats_{short_code}")
    return {"message": "Ссылка обновлена", "short_code": short_code}

@router.post("/links/update")
def update_link_form(
    short_code: str = Form(...),
    original_url: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    link = get_link(short_code, db)
    if not link.user_id or link.user_id != current_user.id:
        return HTMLResponse(
            content="<h3>Нет доступа к этой ссылке</h3><a href='/dashboard'>Назад</a>",
            status_code=403
        )
    link.original_url = original_url
    db.commit()
    delete_cache(f"link_stats_{short_code}")
    return RedirectResponse(url="/?message=Ссылка успешно обновлена", status_code=303)

# ================================
# Удаление ссылки
# ================================
@router.delete("/links/{short_code}")
def delete_link_api(
    short_code: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    link = get_link(short_code, db)
    if not link.user_id or link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой ссылке")
    db.delete(link)
    db.commit()
    delete_cache(f"link_stats_{short_code}")
    return {"message": "Ссылка удалена"}

@router.post("/links/delete")
def delete_link_form(
    short_code: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    link = get_link(short_code, db)
    if not link.user_id or link.user_id != current_user.id:
        return HTMLResponse(
            content="<h3>Нет доступа к этой ссылке</h3><a href='/dashboard'>Назад</a>",
            status_code=403
        )
    db.delete(link)
    db.commit()
    delete_cache(f"link_stats_{short_code}")
    return RedirectResponse(url="/?message=Ссылка успешно удалена", status_code=303)
