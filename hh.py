from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import httpx
from urllib.parse import urlencode
import json

app = FastAPI()

# Добавляем middleware для работы с сессиями.
# В продакшене секретный ключ должен быть более сложным и храниться в переменных окружения.
app.add_middleware(SessionMiddleware, secret_key="super_secret_key_for_sessions")

# Конфигурация OAuth2 для HeadHunter
CLIENT_ID = "PLRA71P98D6AKD214F3ILJMTV00P2525A1D17R2OH6DQIOV0O5BMHF279VPKV21O"
CLIENT_SECRET = "OE1MR221VJU5MTFNPNDT0K89OCFCGAR4AJJMKL1F4K4MBG8FD2OC1G7B3EC647FE"
REDIRECT_URI = "https://platform.atlantys.kz/callback"  # Должен совпадать с настройками приложения
AUTHORIZATION_URL = "https://hh.ru/oauth/authorize"
TOKEN_URL = "https://hh.ru/oauth/token"


@app.get("/", response_class=HTMLResponse)
async def index():
    html_content = """
    <html>
        <head>
            <title>Atlantys AI</title>
        </head>
        <body>
            <h1>Добро пожаловать в Atlantys AI!</h1>
            <p><a href="/login">Войти через HeadHunter</a></p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/login")
async def login():
    """
    Шаг 1. Перенаправляем пользователя на страницу авторизации HH.
    Формируем URL с параметрами:
      - response_type=code (запрос авторизационного кода)
      - client_id – идентификатор вашего приложения
      - redirect_uri – куда HH вернёт пользователя после авторизации
      - (опционально) scope – запрашиваемые права (например, доступ к вакансиям и откликам)
    """
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        # Если требуется, добавьте scope, например:
        # "scope": "vacancies responses"
    }
    url = f"{AUTHORIZATION_URL}?{urlencode(params)}"
    return RedirectResponse(url)


@app.get("/callback")
async def callback(request: Request):
    """
    Шаг 2. Обработка перенаправления после авторизации.
    Если авторизация прошла успешно, в URL будет передан параметр code.
    Затем выполняется обмен кода на токены.
    """
    # Если возникла ошибка (например, пользователь отказался от доступа)
    error = request.query_params.get("error")
    if error:
        return HTMLResponse(content=f"Ошибка авторизации: {error}")

    code = request.query_params.get("code")
    if not code:
        return HTMLResponse(content="Не получен код авторизации.")

    # Шаг 3. Обмен кода на access_token
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI
    }
    async with httpx.AsyncClient() as client:
        token_response = await client.post(TOKEN_URL, data=token_data)

    if token_response.status_code != 200:
        return HTMLResponse(content=f"Ошибка получения токена: {token_response.text}")

    token_info = token_response.json()
    # Сохраняем полученные токены в сессии
    request.session['access_token'] = token_info.get("access_token")
    request.session['refresh_token'] = token_info.get("refresh_token")
    request.session['expires_in'] = token_info.get("expires_in")

    return RedirectResponse(url="/profile")


@app.get("/profile")
async def profile(request: Request):
    """
    Шаг 4. Используем access_token для вызова защищённых API HH.
    Примеры запросов:
      - Получение данных пользователя
      - Получение вакансий
      - Получение откликов
    """
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/login")

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with httpx.AsyncClient() as client:
        # Пример: Запрос данных пользователя
        user_response = await client.get("https://api.hh.ru/me", headers=headers)
        if user_response.status_code != 200:
            user_info = {"error": user_response.text}
        else:
            user_info = user_response.json()

        # Пример: Запрос вакансий (проверьте актуальный эндпоинт и параметры)
        vacancies_response = await client.get("https://api.hh.ru/vacancies", headers=headers)
        if vacancies_response.status_code != 200:
            vacancies = {"error": vacancies_response.text}
        else:
            vacancies = vacancies_response.json()

        # Пример: Запрос откликов (замените URL на корректный, если требуется)
        responses_response = await client.get("https://api.hh.ru/responses", headers=headers)
        if responses_response.status_code != 200:
            responses_data = {"error": responses_response.text}
        else:
            responses_data = responses_response.json()

    return JSONResponse(content={
        "user_info": user_info,
        "vacancies": vacancies,
        "responses": responses_data
    })


@app.get("/refresh")
async def refresh(request: Request):
    """
    Дополнительный эндпоинт для обновления access_token с использованием refresh_token.
    Позволяет обновить токен без участия пользователя.
    """
    refresh_token_value = request.session.get("refresh_token")
    if not refresh_token_value:
        return HTMLResponse(content="Нет refresh_token. Авторизуйтесь заново.")

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token_value,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, data=data)

    if response.status_code != 200:
        return HTMLResponse(content=f"Ошибка обновления токена: {response.text}")

    token_info = response.json()
    # Обновляем данные в сессии
    request.session["access_token"] = token_info.get("access_token")
    request.session["refresh_token"] = token_info.get("refresh_token")
    request.session["expires_in"] = token_info.get("expires_in")

    return JSONResponse(content=token_info)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("hh:app", host="0.0.0.0", port=8005, reload=True)