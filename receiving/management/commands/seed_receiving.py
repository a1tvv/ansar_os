"""
Сидит поставщиков и несколько демо-документов приёмки:
один оприходованный без расхождений, один с расхождением,
один черновик — чтобы сразу видеть все три состояния.

Запуск: python manage.py seed_receiving
"""
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from reports.models import Branch, Product
from receiving.models import Supplier, ReceivingDocument, ReceivingLine

SUPPLIERS = [
    ('ТОО «Уют-KZ»', 'Алматы', 'отсрочка 30 дней'),
    ('ИП «Даулет Трейд»', 'Шымкент', 'предоплата 50%'),
    ('ТОО «Хоум Импорт»', 'Астана', 'отсрочка 45 дней'),
    ('ТОО «Астана Текстиль»', 'Астана', 'по факту'),
]


class Command(BaseCommand):
    help = 'Заполнить демо-данными модуль приёмки: поставщики + примеры документов'

    def handle(self, *args, **opts):
        if ReceivingDocument.objects.exists():
            self.stdout.write(self.style.WARNING('Документы приёмки уже есть — пропускаю сид.'))
            return

        branch = Branch.objects.first()
        products = list(Product.objects.all()[:6])
        if not branch or not products:
            self.stdout.write(self.style.ERROR(
                'Нет филиалов/товаров. Сначала выполни: python manage.py seed_demo'))
            return

        suppliers = list(Supplier.objects.all())
        if not suppliers:
            suppliers = [Supplier.objects.create(name=n, city=c, terms=t) for n, c, t in SUPPLIERS]

        today = timezone.localdate()

        # 1. Оприходован без расхождений
        d1 = ReceivingDocument.objects.create(
            doc_no='ПР-2026-0001', supplier=suppliers[0], branch=branch,
            invoice_no='НК-88214', invoice_date=today - timedelta(days=3),
            status='posted', posted_at=timezone.now() - timedelta(days=3), author='Д. Ахметов',
            account='Сейф - 1', paid=Decimal('570000'), comment='',
        )
        for p in products[:3]:
            ReceivingLine.objects.create(document=d1, product=p, qty_invoice=20, qty_fact=20,
                                         unit_price=Decimal('9500'), sale_price=Decimal('12800'))

        # 2. Оприходован с расхождением
        d2 = ReceivingDocument.objects.create(
            doc_no='ПР-2026-0002', supplier=suppliers[1], branch=branch,
            invoice_no='НК-88301', invoice_date=today - timedelta(days=1),
            status='mismatch', posted_at=timezone.now() - timedelta(days=1), author='Д. Ахметов',
            account='Kaspi Bank (расчётный)', paid=Decimal('200000'), comment='Недовоз 2 шт, согласовано',
        )
        ReceivingLine.objects.create(document=d2, product=products[3], qty_invoice=30, qty_fact=28,
                                     unit_price=Decimal('8900'), sale_price=Decimal('11900'))
        ReceivingLine.objects.create(document=d2, product=products[4], qty_invoice=15, qty_fact=15,
                                     unit_price=Decimal('12700'), sale_price=Decimal('16500'))

        # 3. Черновик — ждёт сканирования
        d3 = ReceivingDocument.objects.create(
            doc_no='ПР-2026-0003', supplier=suppliers[2], branch=branch,
            invoice_no='НК-88412', invoice_date=today, status='draft', author='Д. Ахметов',
            account='Наличные касса', paid=Decimal('0'), comment='',
        )
        ReceivingLine.objects.create(document=d3, product=products[5], qty_invoice=10, qty_fact=4,
                                     unit_price=Decimal('6200'), sale_price=Decimal('8400'))

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Поставщиков: {len(suppliers)}, документов приёмки: 3 '
            f'(оприходован, с расхождением, черновик).'))
