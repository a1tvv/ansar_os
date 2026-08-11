"""
Вьюхи приёмки. Сценарий под реальный ручной процесс кладовщика:
1. Создать документ (поставщик, филиал, счёт оплаты, номер накладной).
2. Сканировать штрихкод -> строка добавляется/увеличивается сама.
   Если товара с таким штрихкодом нет в каталоге — создаётся заготовка
   (кладовщик потом дозаполнит название и цену), чтобы сканирование
   никогда не блокировалось незнакомым товаром.
3. Видно расхождение накладная/факт и наценку по каждой строке.
4. Оприходовать -> статус posted, дата фиксируется, история остаётся навсегда.
5. Печать этикеток и ценников — со списка и из документа.
"""
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from reports.models import Branch, Product
from .models import Supplier, ReceivingDocument, ReceivingLine

CURRENT_USER = 'А. Сериков'

# Счета оплаты. Пока справочник захардкожен — когда появится модуль
# «Настройки», вынести в отдельную модель Account.
ACCOUNTS = ['Сейф - 1', 'Kaspi Bank (расчётный)', 'Наличные касса', 'Halyk Bank']


def money(value):
    """12345 -> '12 345,00 ₸' — как в umag, с копейками."""
    return f'{Decimal(value or 0):,.2f}'.replace(',', ' ').replace('.', ',') + ' ₸'


def _dec(raw, default='0'):
    try:
        return Decimal(str(raw).replace(',', '.').strip() or default)
    except (InvalidOperation, AttributeError):
        return Decimal(default)


def _parse_date(s):
    for fmt in ('%Y-%m-%d', '%d.%m.%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def doc_list(request):
    """
    Список приёмок — аналог «Списка приемок» в umag, но с наценкой
    и без потери истории: период по умолчанию неделя, но доступна
    любая глубина, данные не удаляются автоматически.
    """
    today = timezone.localdate()
    date_from = _parse_date(request.GET.get('from', '')) or (today - timedelta(days=7))
    date_to = _parse_date(request.GET.get('to', '')) or today
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')

    docs = (ReceivingDocument.objects
            .select_related('supplier', 'branch')
            .prefetch_related('lines')
            .filter(created_at__date__gte=date_from, created_at__date__lte=date_to))

    if query:
        docs = docs.filter(
            Q(doc_no__icontains=query) | Q(invoice_no__icontains=query)
            | Q(supplier__name__icontains=query) | Q(author__icontains=query)
        )
    if status:
        docs = docs.filter(status=status)

    rows, t_total, t_paid, t_remaining, t_sell = [], Decimal(0), Decimal(0), Decimal(0), Decimal(0)
    for d in docs:
        total, paid = d.total, d.paid
        remaining, sell = d.remaining, d.sell_total
        t_total += total; t_paid += paid; t_remaining += remaining; t_sell += sell
        rows.append({
            'obj': d,
            'lines_count': d.lines.count(),
            'total': money(total), 'paid': money(paid),
            'remaining': money(remaining), 'remaining_zero': remaining <= 0,
            'sell': money(sell), 'mismatch': d.has_mismatch,
        })

    paginator = Paginator(rows, int(request.GET.get('size', 50) or 50))
    page = paginator.get_page(request.GET.get('page', 1))

    ctx = {
        'active': 'receiving', 'page_obj': page, 'rows': page.object_list,
        'date_from': date_from, 'date_to': date_to, 'query': query, 'status': status,
        'totals': {
            'total': money(t_total), 'paid': money(t_paid),
            'remaining': money(t_remaining), 'sell': money(t_sell),
            'margin': money(t_sell - t_total),
        },
        'count': len(rows),
        'statuses': ReceivingDocument.STATUS,
    }
    return render(request, 'receiving/list.html', ctx)


def doc_new(request):
    if request.method == 'POST':
        supplier = get_object_or_404(Supplier, pk=request.POST.get('supplier'))
        branch = get_object_or_404(Branch, pk=request.POST.get('branch'))
        last = ReceivingDocument.objects.order_by('-id').first()
        doc = ReceivingDocument.objects.create(
            doc_no=f'ПР-{timezone.localdate():%Y}-{(last.id if last else 0) + 1:04d}',
            supplier=supplier, branch=branch,
            invoice_no=request.POST.get('invoice_no', '').strip(),
            invoice_date=_parse_date(request.POST.get('invoice_date', '')) or timezone.localdate(),
            account=request.POST.get('account', ''),
            paid=_dec(request.POST.get('paid', 0)),
            comment=request.POST.get('comment', '').strip(),
            status='draft', author=CURRENT_USER,
        )
        return redirect('receiving:detail', pk=doc.pk)

    return render(request, 'receiving/new.html', {
        'active': 'receiving',
        'suppliers': Supplier.objects.all(),
        'branches': Branch.objects.all(),
        'accounts': ACCOUNTS,
        'today': timezone.localdate(),
    })


def doc_detail(request, pk):
    doc = get_object_or_404(ReceivingDocument, pk=pk)
    lines = [{
        'obj': l, 'total': money(l.line_total), 'sell_total': money(l.line_sell_total),
        'price': money(l.unit_price), 'sale_price': money(l.sale_price),
        'markup': l.markup_pct, 'mismatch': l.mismatch,
    } for l in doc.lines.select_related('product').all()]

    return render(request, 'receiving/detail.html', {
        'active': 'receiving', 'doc': doc, 'lines': lines,
        'total': money(doc.total), 'sell_total': money(doc.sell_total),
        'margin': money(doc.margin), 'paid': money(doc.paid),
        'remaining': money(doc.remaining), 'accounts': ACCOUNTS,
    })


@require_POST
def add_line(request, pk):
    """
    Сканирование: ищем товар по штрихкоду. Повторный скан той же позиции
    увеличивает qty_fact на 1. Неизвестный штрихкод создаёт заготовку
    товара, чтобы сканирование не вставало из-за незнакомого кода.
    """
    doc = get_object_or_404(ReceivingDocument, pk=pk)
    barcode = request.POST.get('barcode', '').strip()
    if not barcode:
        messages.error(request, 'Введите или отсканируйте штрихкод')
        return redirect('receiving:detail', pk=pk)

    product = Product.objects.filter(barcode=barcode).first()
    if not product:
        product = Product.objects.create(name=f'Новый товар (шк {barcode})', barcode=barcode)
        messages.info(request, f'Штрихкод {barcode} не найден в каталоге — создана заготовка товара')

    with transaction.atomic():
        line, created = ReceivingLine.objects.get_or_create(document=doc, product=product)
        line.qty_fact += 1
        if created:
            qty_invoice = request.POST.get('qty_invoice')
            if qty_invoice:
                try:
                    line.qty_invoice = int(qty_invoice)
                except ValueError:
                    pass
            line.unit_price = _dec(request.POST.get('unit_price', 0))
            line.sale_price = _dec(request.POST.get('sale_price', 0))
        line.save()

    return redirect('receiving:detail', pk=pk)


@require_POST
def update_line(request, pk, line_id):
    """Правка строки: количества и цены (закупочная/продажная)."""
    doc = get_object_or_404(ReceivingDocument, pk=pk)
    line = get_object_or_404(ReceivingLine, pk=line_id, document=doc)
    try:
        line.qty_invoice = int(request.POST.get('qty_invoice', line.qty_invoice) or 0)
        line.qty_fact = int(request.POST.get('qty_fact', line.qty_fact) or 0)
    except ValueError:
        pass
    line.unit_price = _dec(request.POST.get('unit_price', line.unit_price))
    line.sale_price = _dec(request.POST.get('sale_price', line.sale_price))
    line.save()
    return redirect('receiving:detail', pk=pk)


@require_POST
def delete_line(request, pk, line_id):
    doc = get_object_or_404(ReceivingDocument, pk=pk)
    ReceivingLine.objects.filter(pk=line_id, document=doc).delete()
    return redirect('receiving:detail', pk=pk)


@require_POST
def update_payment(request, pk):
    """Обновить счёт/оплату/комментарий по документу."""
    doc = get_object_or_404(ReceivingDocument, pk=pk)
    doc.account = request.POST.get('account', doc.account)
    doc.paid = _dec(request.POST.get('paid', doc.paid))
    doc.comment = request.POST.get('comment', doc.comment).strip()
    doc.save()
    messages.success(request, 'Оплата по документу обновлена')
    return redirect('receiving:detail', pk=pk)


@require_POST
def post_document(request, pk):
    """Оприходовать. Статус становится posted/mismatch, дата фиксируется."""
    doc = get_object_or_404(ReceivingDocument, pk=pk)
    if doc.lines.count() == 0:
        messages.error(request, 'Нельзя оприходовать пустой документ — добавьте позиции')
        return redirect('receiving:detail', pk=pk)

    doc.status = 'mismatch' if doc.has_mismatch else 'posted'
    doc.posted_at = timezone.now()
    doc.save()
    messages.success(request, f'Документ {doc.doc_no} оприходован')
    return redirect('receiving:list')


def print_labels(request, pk):
    """
    Печать этикеток (штрихкод) или ценников (цена крупно) по документу.
    ?kind=label | price ; количество этикеток = фактически принятому.
    Штрихкод рисуем CSS-полосками — без внешних библиотек, чтобы
    страница печаталась даже без интернета на складе.
    """
    doc = get_object_or_404(ReceivingDocument, pk=pk)
    kind = request.GET.get('kind', 'label')

    items = []
    for line in doc.lines.select_related('product').all():
        for _ in range(max(1, line.qty_fact)):
            items.append({
                'name': line.product.name,
                'barcode': line.product.barcode or '—',
                'price': money(line.sale_price),
                'bars': [(int(c) % 4) + 1 for c in (line.product.barcode or '0000000000000')],
            })

    return render(request, 'receiving/labels.html', {
        'doc': doc, 'items': items, 'kind': kind,
        'title': 'Ценники' if kind == 'price' else 'Этикетки',
    })
