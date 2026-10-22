**English** | [Русский](README.ru.md)

# Ansar OS

An internal system for the daily work of Ansar shops. The first part is sales reports that are never deleted automatically.

<!-- TODO: add a screenshot or screen recording as docs/demo.gif -->

## Features

- **Reports:** sales for any period since 2019 — KPIs, results for each branch and top products. Everything is calculated from the database
- **Archive that stays forever:** reports are never deleted automatically. To delete a report by hand, you must confirm it, and the action is saved in an audit log
- **Goods receiving:** documents for new goods with item lines, adding many items at once, payment status, posting the document and barcode sheets you can print
- Empty screens are ready for the next modules: stock, transfers, purchasing, staff and more
- Django admin for all data, plus scripts that create demo data

## Tech stack

Python · Django · PostgreSQL (or SQLite for development) · WhiteNoise

## Quick start

```bash
git clone https://github.com/a1tvv/ansar_os.git && cd ansar_os
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python manage.py migrate && python manage.py seed_demo
python manage.py runserver
```

If `PG_DB` is not set, the project uses SQLite. Open http://127.0.0.1:8000 — it takes you to the reports module. For the admin panel, run `python manage.py createsuperuser` and open `/admin/`.

## Configuration

Set these as environment variables (see [`.env.example`](.env.example)):

| Variable | What it does |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret key. Without it, an unsafe dev key is used, so always set it in production |
| `DJANGO_DEBUG` | `1` (on) by default; set `0` in production |
| `DJANGO_ALLOWED_HOSTS` | Host names separated by commas; `*` by default, so set it in production |
| `PG_DB`, `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_PORT` | PostgreSQL connection |
| `DATABASE_URL` | Another way to connect: one connection string, for example on serverless hosting |

## License

[MIT](LICENSE)
