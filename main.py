from fastapi import FastAPI
from handlers import auth, links, front

app = FastAPI(title="API-сервис сокращения ссылок")

app.include_router(auth.router)
app.include_router(links.router)
app.include_router(front.router)

