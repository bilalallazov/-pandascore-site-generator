# Esports matches site generator (PandaScore)

Генератор сайта из 3 страниц без параметров URL:

- `/yesterday` — матчи за вчера
- `/today` — матчи за сегодня
- `/tomorrow` — матчи на завтра

Данные берутся из PandaScore (`/matches/past` и `/matches/upcoming`) и по клику **сервер** генерирует “голый HTML” с SEO-полями и микроразметкой schema.org.

## Требования

- Python 3.11+ (рекомендуется)
- токен PandaScore в переменной окружения `PANDASCORE_TOKEN`

Токен находится в PandaScore Dashboard. Не кладите токен в клиентский JS.

## Установка

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск

Задайте переменные окружения и запустите сервер:

```powershell
$env:PANDASCORE_TOKEN="PASTE_YOUR_TOKEN"
$env:SITE_URL="http://localhost:8000"
$env:SITE_NAME="Esports Matches"
$env:TIMEZONE="Europe/Moscow"
uvicorn server.main:app --reload --port 8000
```

Откройте `http://localhost:8000/`, нажмите кнопку **“Сгенерировать сайт”**. После генерации доступны:

- `http://localhost:8000/yesterday`
- `http://localhost:8000/today`
- `http://localhost:8000/tomorrow`

## Запуск через Docker (если Python не установлен)

```powershell
$env:PANDASCORE_TOKEN="PASTE_YOUR_TOKEN"
docker compose up --build
```

Дальше так же откройте `http://localhost:8000/` и нажмите кнопку генерации.

## Что именно генерируется

- Кэш данных в `data/yesterday.json`, `data/today.json`, `data/tomorrow.json`
- Статические страницы в:
  - `generated/yesterday/index.html`
  - `generated/today/index.html`
  - `generated/tomorrow/index.html`

## SEO / микроразметка

В исходном HTML страниц присутствуют:

- `title`, `meta description`
- `canonical`, OpenGraph (`og:*`), Twitter card
- schema.org:
  - `Organization` (JSON-LD переменная `org_schema`)
  - `SportsEvent` (microdata на каждой карточке матча)

## Деплой

Для тестового проще всего:

- GitHub репозиторий
- деплой на Render/Railway/Fly.io/VPS

Если нужен именно статический хостинг (GitHub Pages), можно изменить подход: запускать генерацию локально и публиковать папку `generated/`.
