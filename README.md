# ShortLinkApp

Запуск приложения (тесты в докере, без выполнения не проходит деплой):

```
git clone https://github.com/Fryman420/ShortLinkApp
cd ShortLinkApp/
docker build -t shortlink .
docker run -d -p 80:80 shortlink 
```
Запустить тесты отдельно:
```
docker run --rm shortlink python -m pytest test_app.py
```
ссылка http://158.160.94.156/
