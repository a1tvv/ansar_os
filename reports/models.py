"""
Модели первого модуля Ansar OS.

Ключевая идея всей системы против umag: данные хранятся ВЕЧНО.
Нигде в проекте нет автоочистки — ни cron, ни TTL, ни каскадного
удаления «старого». Удаление возможно только вручную (см. views.delete_*),
с подтверждением и записью в AuditLog.
"""
from django.db import models


class Branch(models.Model):
    code = models.CharField('Код', max_length=16, unique=True)
    name = models.CharField('Название', max_length=128)
    city = models.CharField('Город', max_length=64, blank=True)
    address = models.CharField('Адрес', max_length=200, blank=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField('Наименование', max_length=200)
    barcode = models.CharField('Штрихкод', max_length=32, blank=True)
    category = models.CharField('Категория', max_length=64, blank=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']

    def __str__(self):
        return self.name


class Sale(models.Model):
    """Чек продажи (шапка). Приходит с фискальной кассы по API."""
    STATUS = [('done', 'Проведено'), ('return', 'Возврат'), ('pending', 'Ожидает')]
    PAY = [('card', 'Карта'), ('cash', 'Наличные'), ('kaspi', 'Kaspi QR')]

    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='sales')
    receipt_no = models.CharField('Номер чека', max_length=32)
    sold_at = models.DateTimeField('Дата и время продажи')
    payment = models.CharField('Оплата', max_length=16, choices=PAY, default='card')
    status = models.CharField('Статус', max_length=16, choices=STATUS, default='done')
    total = models.DecimalField('Сумма', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Продажа'
        verbose_name_plural = 'Продажи'
        ordering = ['-sold_at']
        # Индексы под запросы отчётов по датам/филиалам.
        # NOTE (следующий шаг): при росте истории до миллионов строк
        # перевести на декларативное партиционирование по диапазону
        # sold_at (RANGE) — это делается на уровне Postgres, модель уже готова.
        indexes = [
            models.Index(fields=['sold_at']),
            models.Index(fields=['branch', 'sold_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.receipt_no


class SaleLine(models.Model):
    """Позиция чека — нужна для отчёта по топ-товарам."""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='lines')
    qty = models.PositiveIntegerField('Количество', default=1)
    amount = models.DecimalField('Сумма позиции', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Позиция чека'
        verbose_name_plural = 'Позиции чеков'


class SavedReport(models.Model):
    """
    Запись архива отчётов. retention всегда 'permanent'.
    Система НИКОГДА не удаляет это автоматически.
    """
    RETENTION = [('permanent', 'Хранится постоянно')]

    title = models.CharField('Отчёт', max_length=200)
    report_type = models.CharField('Тип', max_length=64, default='Продажи')
    period_from = models.DateField('Период с')
    period_to = models.DateField('Период по')
    created_at = models.DateTimeField('Сформирован', auto_now_add=True)
    author = models.CharField('Автор', max_length=128, default='Система')
    size_label = models.CharField('Размер', max_length=32, default='—')
    retention = models.CharField('Хранение', max_length=16, choices=RETENTION, default='permanent')

    class Meta:
        verbose_name = 'Отчёт в архиве'
        verbose_name_plural = 'Архив отчётов'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AuditLog(models.Model):
    """Журнал аудита. Сюда пишется каждое ручное удаление."""
    created_at = models.DateTimeField('Когда', auto_now_add=True)
    actor = models.CharField('Кто', max_length=128, default='—')
    action = models.CharField('Действие', max_length=64)
    object_repr = models.CharField('Объект', max_length=255)
    detail = models.TextField('Детали', blank=True)

    class Meta:
        verbose_name = 'Запись аудита'
        verbose_name_plural = 'Журнал аудита'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at:%d.%m.%Y %H:%M} · {self.action}'
