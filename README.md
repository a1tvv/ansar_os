# Ansar OS

Internal operations system for the Ansar retail network — starting with sales reports that are never deleted automatically.

![demo](docs/demo.gif)
<!-- TODO: add a screenshot or screen recording as docs/demo.gif -->

## Features

- **Reports:** sales for any period back to 2019 — KPIs, breakdown across branches and top products, all computed from the database
- **Permanent archive:** reports are never removed automatically; manual deletion needs confirmation and is written to an audit log
- **Goods receiving:** receiving documents with line items, bulk entry, payment status, posting and printable barcode sheets
- UI shell for the next modules: stock, transfers, purchasing, staff and more
- Django admin for all data, plus demo data generators

## Tech stack

Python · Django · PostgreSQL (SQLite fallback for development) · WhiteNoise

## Quick start

```bash
git clone https://github.com/a1tvv/ansar_os.git && cd ansar_os
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python manage.py migrate && python manage.py seed_demo
python manage.py runserver
```

Without `PG_DB` set, the project starts on SQLite. Open http://127.0.0.1:8000 — it redirects to the reports module. For the admin, run `python manage.py createsuperuser` and open `/admin/`.

## Configuration

Set these as environment variables (see [`.env.example`](.env.example)):

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret key — falls back to an insecure dev key, so always set it in production |
| `DJANGO_DEBUG` | Defaults to `1` (on); set `0` in production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated host names; defaults to `*`, so set it in production |
| `PG_DB`, `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_PORT` | PostgreSQL connection |
| `DATABASE_URL` | Alternative single connection string, e.g. on serverless hosting |

## License

[MIT](LICENSE)
