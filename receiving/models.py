"""
Модуль приёмки товара.

Реальный процесс в Ansar: кладовщик вносит позиции с бумажной накладной
вручную и сканирует штрихкоды/количества сам — без электронной выгрузки
от поставщика. Поэтому первая версия делает этот ручной ввод быстрым
(сканер -> строка), а не пытается распознавать PDF.

История приёмок хранится без ограничения срока — тот же принцип
вечного хранения, что и в модуле отчётов (см. reports/models.py).
"""
from django.db import models
from reports.models import Branch, Product


class Supplier(models.Model):
    name = models.CharField('Название', max_length=200)
    city = models.CharField('Город', max_length=64, blank=True)
    terms = models.CharField('Условия оплаты', max_length=64, blank=True)

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['name']

    def __str__(self):
        return self.name


class ReceivingDocument(models.Model):
    """Документ приёмки (шапка) — один на одну накладную от поставщика."""
    STATUS = [
        ('draft', 'Черновик'),
        ('posted', 'Оприходовано'),
        ('mismatch', 'С расхождением'),
    ]

    doc_no = models.CharField('Номер документа', max_length=32, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='documents')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='receiving_documents')
    invoice_no = models.CharField('Номер накладной', max_length=64, blank=True)
    invoice_date = models.DateField('Дата накладной', null=True, blank=True)
    status = models.CharField('Статус', max_length=16, choices=STATUS, default='draft')
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    posted_at = models.DateTimeField('Оприходован', null=True, blank=True)
    author = models.CharField('Кладовщик', max_length=128, default='—')

    class Meta:
        verbose_name = 'Документ приёмки'
        verbose_name_plural = 'Документы приёмки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['branch', 'status']),
        ]

    def __str__(self):
        return self.doc_no

    @property
    def total(self):
        return sum((l.line_total for l in self.lines.all()), start=0)

    @property
    def has_mismatch(self):
        return any(l.qty_invoice != l.qty_fact for l in self.lines.all())


class ReceivingLine(models.Model):
    """
    Позиция документа приёмки.
    qty_invoice — сколько заявлено в накладной.
    qty_fact — сколько кладовщик реально насканировал/пересчитал.
    Расхождение видно сразу по разнице этих двух полей.
    """
    document = models.ForeignKey(ReceivingDocument, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='receiving_lines')
    qty_invoice = models.PositiveIntegerField('Кол-во по накладной', default=0)
    qty_fact = models.PositiveIntegerField('Кол-во фактически', default=0)
    unit_price = models.DecimalField('Цена за ед.', max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Позиция приёмки'
        verbose_name_plural = 'Позиции приёмки'

    def __str__(self):
        return f'{self.product} × {self.qty_fact}'

    @property
    def line_total(self):
        return self.unit_price * self.qty_fact

    @property
    def mismatch(self):
        return self.qty_invoice != self.qty_fact
