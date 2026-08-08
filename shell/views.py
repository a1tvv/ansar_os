"""
Визуальные заготовки страниц, которые ещё не подключены к базе.

Разметка и демо-данные — те же, что показывали Раджану в макете.
Когда очередь дойдёт до конкретной страницы: смотри models.py в этом
приложении за списком нужных моделей, переноси страницу в свой
Django-app (как это уже сделано для reports/ и receiving/), и убирай
её из SHELL_PAGES ниже.
"""
from django.shortcuts import render, get_object_or_404
from django.http import Http404

TITLES = {
    'dashboard': 'Дашборд',
    'catalog': 'Каталог товаров',
    'stock': 'Склад и остатки',
    'transfers': 'Движение товара',
    'purchasing': 'Закупки и поставщики',
    'sales': 'Продажи',
    'branches': 'Филиалы',
    'staff': 'Сотрудники и роли',
    'settings': 'Настройки',
}


def page(request, slug):
    if slug not in TITLES:
        raise Http404
    return render(request, f'shell/{slug}.html', {'active': slug, 'title': TITLES[slug]})
