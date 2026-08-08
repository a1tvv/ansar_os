"""
Вьюхи приёмки. Сценарий под реальный ручной процесс кладовщика:
1. Создать документ (поставщик, филиал, номер накладной).
2. Сканировать штрихкод -> строка добавляется/увеличивается сама.
   Если товара с таким штрихкодом нет в каталоге — создаётся заготовка
   (кладовщик потом дозаполнит название и цену), чтобы сканирование
   никогда не блокировалось незнакомым товаром.
3. Видно расхождение накладная/факт по каждой строке.
4. Оприходовать -> статус posted, дата фиксируется, история остаётся навсегда.
"""
from django.contrib import admin as _unused  # noqa (keeps flake quiet if imported elsewhere)
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from reports.models import Branch, Product
from .models import Supplier, ReceivingDocument, ReceivingLine

CURRENT_USER = 'А. Сериков'


def money(value):
    return f'{int(value or 0):,}'.replace(',', ' ') + ' ₸'


def doc_list(request):
    docs = ReceivingDocument.objects.select_related('supplier', 'branch').all()
    rows = []
    for d in docs:
        rows.append({
            'obj': d, 'total': money(d.total),
            'lines_count': d.lines.count(),
            'mismatch': d.has_mismatch,
        })
    return render(request, 'receiving/list.html', {'active': 'receiving', 'rows': rows})


def doc_new(request):
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        branch_id = request.POST.get('branch')
        invoice_no = request.POST.get('invoice_no', '').strip()
        supplier = get_object_or_404(Supplier, pk=supplier_id)
        branch = get_object_or_404(Branch, pk=branch_id)
        last = ReceivingDocument.objects.order_by('-id').first()
        next_no = f'ПР-{timezone.localdate():%Y}-{(last.id if last else 0) + 1:04d}'
        doc = ReceivingDocument.objects.create(
            doc_no=next_no, supplier=supplier, branch=branch,
            invoice_no=invoice_no, invoice_date=timezone.localdate(),
            status='draft', author=CURRENT_USER,
        )
        return redirect('receiving:detail', pk=doc.pk)

    return render(request, 'receiving/new.html', {
        'active': 'receiving',
        'suppliers': Supplier.objects.all(),
        'branches': Branch.objects.all(),
    })


def doc_detail(request, pk):
    doc = get_object_or_404(ReceivingDocument, pk=pk)
    lines = []
    for l in doc.lines.select_related('product').all():
        lines.append({
            'obj': l, 'total': money(l.line_total),
            'price': money(l.unit_price), 'mismatch': l.mismatch,
        })
    return render(request, 'receiving/detail.html', {
        'active': 'receiving', 'doc': doc, 'lines': lines, 'total': money(doc.total),
    })


@require_POST
def add_line(request, pk):
    """
    Симулирует сканирование: ищем товар по штрихкоду. Если он уже есть
    строкой в этом документе — увеличиваем qty_fact на 1 (как повторное
    сканирование той же позиции). Если товара нет в каталоге — создаём
    заготовку по штрихкоду, чтобы сканирование не блокировалось.
    """
    doc = get_object_or_404(ReceivingDocument, pk=pk)
    barcode = request.POST.get('barcode', '').strip()
    qty_invoice = request.POST.get('qty_invoice')

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
        if created and qty_invoice:
            try:
                line.qty_invoice = int(qty_invoice)
            except ValueError:
                pass
        line.save()

    return redirect('receiving:detail', pk=pk)


@require_POST
def delete_line(request, pk, line_id):
    doc = get_object_or_404(ReceivingDocument, pk=pk)
    ReceivingLine.objects.filter(pk=line_id, document=doc).delete()
    return redirect('receiving:detail', pk=pk)


@require_POST
def post_document(request, pk):
    """Оприходовать. Статус становится posted/mismatch, дата фиксируется навсегда."""
    doc = get_object_or_404(ReceivingDocument, pk=pk)
    if doc.lines.count() == 0:
        messages.error(request, 'Нельзя оприходовать пустой документ — добавьте позиции')
        return redirect('receiving:detail', pk=pk)

    doc.status = 'mismatch' if doc.has_mismatch else 'posted'
    doc.posted_at = timezone.now()
    doc.save()
    messages.success(request, f'Документ {doc.doc_no} оприходован')
    return redirect('receiving:list')
