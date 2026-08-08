from django.urls import reverse

_GROUPS = [
    ('Обзор', [('dashboard', 'Дашборд', 'ДБ'), ('reports', 'Отчёты и аналитика', 'ОТ')]),
    ('Товародвижение', [('catalog', 'Каталог товаров', 'КТ'), ('receiving', 'Приёмка товара', 'ПР'),
                        ('stock', 'Склад и остатки', 'СК'), ('transfers', 'Движение между филиалами', 'ДВ')]),
    ('Коммерция', [('purchasing', 'Закупки и поставщики', 'ЗК'), ('sales', 'Продажи', 'ПД')]),
    ('Администрирование', [('branches', 'Филиалы', 'ФЛ'), ('staff', 'Сотрудники и роли', 'СР'),
                          ('settings', 'Настройки', 'НС')]),
]

def nav(request):
    """Пункты бокового меню. Готовые модули ведут на реальные страницы,
    остальные пока '#' — впереди."""
    urls = {
        'reports': reverse('reports:reports'),
        'receiving': reverse('receiving:list'),
    }
    for slug in ('dashboard', 'catalog', 'stock', 'transfers', 'purchasing', 'sales', 'branches', 'staff', 'settings'):
        urls[slug] = reverse(f'shell:{slug}')
    groups = []
    for title, items in _GROUPS:
        groups.append({'title': title, 'items': [
            {'id': i, 'label': lbl, 'abbr': ab, 'url': urls.get(i, '#')}
            for i, lbl, ab in items
        ]})
    return {'nav': groups}