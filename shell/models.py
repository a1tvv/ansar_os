"""
Заготовки под будущие модули. Ничего здесь пока не мигрируется —
это просто напоминание себе, какие модели понадобятся, когда
дойдёт очередь превращать конкретную страницу из макета в рабочий
модуль (по той же схеме, что reports/models.py и receiving/models.py).

Ничего не наследуется от models.Model, поэтому Django их не увидит
и makemigrations не создаст для них таблиц, пока не раскомментируешь.

# --- Каталог товаров ---
# class Product(models.Model):
#     name, barcode, category, unit, purchase_price, sale_price, markup_pct
#     (реальные поля видны в выгрузке umag — 35к товаров, штрихкод,
#      артикул, код НКТ, закуп./прод. цена, ед. изм., наценка %)

# --- Склад и остатки ---
# class StockBalance(models.Model):
#     branch (FK Branch), product (FK Product), qty
#     Обновляется из ReceivingDocument.post() и из Sale (списание).

# --- Движение между филиалами ---
# class Transfer(models.Model):
#     from_branch, to_branch, status (sent/in_transit/received), lines...

# --- Закупки и поставщики ---
# supplier уже есть в receiving.models.Supplier — переиспользовать.
# class PurchaseOrder(models.Model):
#     supplier, eta, status, lines...

# --- Продажи ---
# class Sale уже есть в reports.models — этот экран просто другой
# срез той же таблицы (журнал чеков), отдельная модель не нужна.

# --- Филиалы / Сотрудники ---
# Branch уже есть в reports.models. Понадобится модель Employee
# (auth.User + профиль: роль, филиал) — вместе с полноценной аутентификацией.

# --- Настройки ---
# Понадобится модель IntegrationSettings (API-ключ кассы) и Dictionary
# (справочники: категории, ед. измерения, причины списания).
"""
