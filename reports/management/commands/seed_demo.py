"""
Заполняет БД демо-данными для модуля отчётов:
8 филиалов, товары, продажи с позициями с 2019 года по сегодня,
и несколько записей в архиве отчётов.

Запуск:  python manage.py seed_demo
Сброс:   python manage.py seed_demo --reset
"""
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from reports.models import Branch, Product, Sale, SaleLine, SavedReport

BRANCHES = [
    ('ALA-1', 'Алматы — Абая', 'Алматы', 'пр. Абая 68, Алматы'),
    ('ALA-2', 'Алматы — Сайран', 'Алматы', 'мкр. Сайран 12, Алматы'),
    ('AST-1', 'Астана — Сарыарка', 'Астана', 'пр. Сарыарка 41, Астана'),
    ('AST-2', 'Астана — Есиль', 'Астана', 'ул. Достык 5, Астана'),
    ('SHY-1', 'Шымкент — Аль-Фараби', 'Шымкент', 'пр. Аль-Фараби 118, Шымкент'),
    ('KGF-1', 'Караганда — Бухар-Жырау', 'Караганда', 'пр. Бухар-Жырау 76, Караганда'),
    ('AKT-1', 'Актобе — Абилкайыр хана', 'Актобе', 'пр. Абилкайыр хана 22, Актобе'),
    ('ATY-1', 'Атырау — Азаттык', 'Атырау', 'пр. Азаттык 94, Атырау'),
]
# (наименование, штрихкод, категория, средняя цена)
PRODUCTS = [
    ('Набор кастрюль Zeus, 6 предметов', '4870021184402', 'Посуда и кухня', 38900),
    ('Сушилка для белья Home Star 20 м', '4870021184419', 'Уборка и хранение', 9450),
    ('Ковёр Anatolia 160×230, беж', '8697551220145', 'Ковры', 54200),
    ('Термос Vacuum 1,2 л, сталь', '4870021184433', 'Посуда и кухня', 7900),
    ('Комплект белья Sateen, 2-спальный', '4870021184440', 'Текстиль', 21300),
    ('Настольная лампа Nordic LED', '6941059612348', 'Освещение', 12700),
    ('Сковорода Titan 26 см, антипригар', '4870021184464', 'Посуда и кухня', 11600),
    ('Контейнеры пищевые, набор 10 шт', '4870021184471', 'Уборка и хранение', 6200),
    ('Плед флисовый Cozy 180×200', '4870021184488', 'Текстиль', 8760),
    ('Швабра с отжимом Spin Mop', '4870021184495', 'Уборка и хранение', 5400),
]
PAY = ['card', 'card', 'card', 'cash', 'kaspi']  # карта чаще
ARCHIVE = [
    ('Продажи по сети — 2019 год', 'Продажи', date(2019, 1, 1), date(2019, 12, 31), 'Система', '4,2 МБ'),
    ('Выручка по филиалам — 2021', 'Выручка', date(2021, 1, 1), date(2021, 12, 31), 'Система', '5,8 МБ'),
    ('Движение товара — 2022 Q4', 'Движение', date(2022, 10, 1), date(2022, 12, 31), 'А. Сериков', '2,7 МБ'),
    ('Топ-товары — 2024 год', 'Топ-товары', date(2024, 1, 1), date(2024, 12, 31), 'Система', '3,4 МБ'),
    ('Остатки на конец года — 2025', 'Остатки', date(2025, 12, 31), date(2025, 12, 31), 'Система', '6,1 МБ'),
    ('Продажи — июль 2026', 'Продажи', date(2026, 7, 1), date(2026, 7, 31), 'А. Сериков', '2,2 МБ'),
]


class Command(BaseCommand):
    help = 'Заполнить БД демо-данными для модуля отчётов'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Очистить данные перед заполнением')

    def handle(self, *args, **opts):
        rnd = random.Random(42)

        if opts['reset']:
            for m in (SaleLine, Sale, SavedReport, Product, Branch):
                m.objects.all().delete()
            self.stdout.write('Старые данные очищены.')

        if Sale.objects.exists():
            self.stdout.write(self.style.WARNING(
                'В базе уже есть продажи. Запусти с --reset, чтобы пересоздать.'))
            return

        branches = [Branch.objects.create(code=c, name=n, city=ci, address=a)
                    for c, n, ci, a in BRANCHES]
        products = [Product.objects.create(name=n, barcode=b, category=c)
                    for n, b, c, _ in PRODUCTS]
        prices = {p.pk: PRODUCTS[i][3] for i, p in enumerate(products)}

        # Множитель «размера» филиала — чтобы выручка отличалась.
        weight = [1.0, 0.9, 1.15, 0.8, 1.25, 0.65, 1.0, 1.15]

        start = date(2019, 1, 1)
        today = timezone.localdate()
        receipt = 1000
        sales_bulk = []
        # Готовим шапки чеков: historic (разрежённо) + плотные последние 45 дней.
        cur = start
        while cur <= today:
            recent = (today - cur).days <= 45
            base = 6 if recent else 1  # чеков «на филиало-день»
            for bi, br in enumerate(branches):
                n = max(0, int(rnd.gauss(base * weight[bi], 1.4)))
                for _ in range(n):
                    receipt += 1
                    hh = rnd.randint(9, 20); mm = rnd.randint(0, 59)
                    dt = timezone.make_aware(datetime.combine(cur, time(hh, mm)))
                    status = 'return' if rnd.random() < 0.012 else 'done'
                    sales_bulk.append(Sale(
                        branch=br, receipt_no=f'№{receipt}', sold_at=dt,
                        payment=rnd.choice(PAY), status=status, total=Decimal('0'),
                    ))
            # шаг: летом каждый день (последние 45), в истории — раз в ~5 дней
            cur += timedelta(days=1 if recent else 5)

        Sale.objects.bulk_create(sales_bulk, batch_size=1000)
        self.stdout.write(f'Создано чеков: {len(sales_bulk):,}'.replace(',', ' '))

        # Позиции чеков + пересчёт суммы чека.
        lines_bulk = []
        updates = []
        for sale in Sale.objects.all().iterator(chunk_size=1000):
            total = Decimal('0')
            for _ in range(rnd.randint(1, 4)):
                prod = rnd.choice(products)
                qty = rnd.randint(1, 3)
                unit = int(prices[prod.pk] * rnd.uniform(0.9, 1.1))
                amount = Decimal(unit * qty)
                total += amount
                lines_bulk.append(SaleLine(sale=sale, product=prod, qty=qty, amount=amount))
                if len(lines_bulk) >= 2000:
                    SaleLine.objects.bulk_create(lines_bulk); lines_bulk = []
            sale.total = total
            updates.append(sale)
            if len(updates) >= 1000:
                Sale.objects.bulk_update(updates, ['total']); updates = []
        if lines_bulk:
            SaleLine.objects.bulk_create(lines_bulk)
        if updates:
            Sale.objects.bulk_update(updates, ['total'])

        for title, rtype, pf, pt, author, size in ARCHIVE:
            SavedReport.objects.create(
                title=title, report_type=rtype, period_from=pf, period_to=pt,
                author=author, size_label=size, retention='permanent')

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Филиалов: {len(branches)}, товаров: {len(products)}, '
            f'позиций: {SaleLine.objects.count():,}, в архиве: {SavedReport.objects.count()}.'
            .replace(',', ' ')))
        self.stdout.write('Открой http://127.0.0.1:8000/reports/ — период по умолчанию год, '
                          'можно выбрать любой вплоть до 2019.')
