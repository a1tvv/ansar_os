"""
Модуль отчётов Ansar OS.

Отчёты считаются РЕАЛЬНО из базы (агрегация по выбранному периоду),
на любую глубину истории. Ничего не удаляется автоматически — удаление
из архива только вручную, через подтверждение и с записью в журнал аудита.
"""
from datetime import datetime, timedelta

from django.contrib import messages
from django.db.models import Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Branch, Sale, SaleLine, SavedReport, AuditLog

PRESETS = ['День', 'Неделя', 'Месяц', 'Квартал', 'Год', '3 года', 'Произвольно']
_PRESET_DAYS = {'День': 1, 'Неделя': 7, 'Месяц': 30, 'Квартал': 91, 'Год': 365, '3 года': 365 * 3}

# Текущий пользователь захардкожен до появления модуля аутентификации.
CURRENT_USER = 'А. Сериков'


def money(value):
    """1234567 -> '1 234 567 ₸' (пробел как разделитель разрядов)."""
    return f'{int(value or 0):,}'.replace(',', ' ') + ' ₸'


def _parse_date(s):
    for fmt in ('%Y-%m-%d', '%d.%m.%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _resolve_period(request):
    today = timezone.localdate()
    preset = request.GET.get('preset', 'Год')
    date_to = today
    date_from = None

    if preset in _PRESET_DAYS:
        date_from = today - timedelta(days=_PRESET_DAYS[preset])

    g_from = _parse_date(request.GET.get('from', ''))
    g_to = _parse_date(request.GET.get('to', ''))
    if g_from:
        date_from, preset = g_from, 'Произвольно'
    if g_to:
        date_to, preset = g_to, 'Произвольно'
    if date_from is None:
        date_from = today - timedelta(days=365)

    return date_from, date_to, preset


def reports(request):
    date_from, date_to, preset = _resolve_period(request)

    period = Sale.objects.filter(sold_at__date__gte=date_from, sold_at__date__lte=date_to)
    non_return = period.exclude(status='return')

    revenue = non_return.aggregate(s=Sum('total'))['s'] or 0
    checks = non_return.count()
    returns = period.filter(status='return').count()
    avg_check = int(revenue / checks) if checks else 0

    kpis = [
        {'label': 'Выручка за период', 'value': money(revenue), 't': 'ok', 'note': f'{date_from:%d.%m.%Y} — {date_to:%d.%m.%Y}'},
        {'label': 'Чеков', 'value': f'{checks:,}'.replace(',', ' '), 't': 'ok', 'note': 'проведённых'},
        {'label': 'Средний чек', 'value': money(avg_check), 't': 'ok', 'note': 'без возвратов'},
        {'label': 'Возвраты', 'value': f'{returns:,}'.replace(',', ' '), 't': 'warn', 'note': 'чеков за период'},
    ]

    branch_rows = []
    for b in Branch.objects.all():
        bq = non_return.filter(branch=b)
        c = bq.count()
        rev = bq.aggregate(s=Sum('total'))['s'] or 0
        if c == 0 and rev == 0:
            continue
        branch_rows.append({
            'name': b.name, 'checks': f'{c:,}'.replace(',', ' '),
            'avg': money(int(rev / c) if c else 0), 'rev': money(rev), 'rev_raw': rev,
        })
    branch_rows.sort(key=lambda r: r['rev_raw'], reverse=True)

    top_qs = (SaleLine.objects.filter(sale__in=non_return)
              .values('product__name')
              .annotate(total=Sum('amount'), qty=Sum('qty'))
              .order_by('-total')[:7])
    max_total = top_qs[0]['total'] if top_qs else 1
    top_goods = [{
        'n': i + 1, 'name': r['product__name'], 'sum': money(r['total']),
        'qty': f"{r['qty']:,}".replace(',', ' '),
        'w': f"{max(6, round(float(r['total']) / float(max_total) * 100))}%",
    } for i, r in enumerate(top_qs)]

    archive = SavedReport.objects.all()
    earliest = Sale.objects.order_by('sold_at').values_list('sold_at', flat=True).first()

    ctx = {
        'active': 'reports',
        'presets': PRESETS, 'preset': preset,
        'date_from': date_from, 'date_to': date_to,
        'kpis': kpis, 'branch_rows': branch_rows, 'top_goods': top_goods,
        'total_checks': f'{checks:,}'.replace(',', ' '),
        'total_revenue': money(revenue),
        'archive': archive, 'archive_count': archive.count(),
        'earliest': earliest,
    }
    return render(request, 'reports/reports.html', ctx)


@require_POST
def save_report(request):
    """Сохранить текущий отчёт в архив. retention = permanent (навсегда)."""
    date_from = _parse_date(request.POST.get('from', '')) or timezone.localdate()
    date_to = _parse_date(request.POST.get('to', '')) or timezone.localdate()
    report_type = request.POST.get('report_type', 'Продажи')
    title = f'{report_type} — {date_from:%d.%m.%Y}–{date_to:%d.%m.%Y}'

    SavedReport.objects.create(
        title=title, report_type=report_type,
        period_from=date_from, period_to=date_to,
        author=CURRENT_USER, size_label='—', retention='permanent',
    )
    messages.success(request, 'Отчёт сохранён в архив · хранится постоянно')
    return redirect(reverse('reports:reports') + f'?from={date_from:%Y-%m-%d}&to={date_to:%Y-%m-%d}')


def delete_report(request, pk):
    """
    Ручное удаление из архива. GET показывает подтверждение,
    POST удаляет и пишет в журнал аудита. Автоудаления в системе нет.
    """
    report = get_object_or_404(SavedReport, pk=pk)
    if request.method == 'POST':
        repr_ = f'{report.title} (id={report.pk})'
        AuditLog.objects.create(
            actor=CURRENT_USER, action='report.delete',
            object_repr=repr_,
            detail=f'Ручное удаление из архива. Период {report.period_from}–{report.period_to}.',
        )
        report.delete()
        messages.success(request, 'Отчёт удалён вручную · запись в журнале аудита')
        return redirect('reports:reports')
    return render(request, 'reports/confirm_delete.html', {'report': report, 'active': 'reports'})
