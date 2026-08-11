from django.urls import reverse

# Полное меню системы. Каждый пункт помечен ролями, которым он виден.
# 'receiver'  — приёмщик/кладовщик: только то, что нужно на складе.
# 'director'  — директор сети: видит всё, включая отчёты и администрирование.
#
# Модули не удаляются из проекта — они просто не показываются той роли,
# которой не нужны. Отчёты, например, остаются рабочими и доступны
# директору: это главное отличие системы от umag (вечное хранение истории),
# и терять его нельзя, даже если приёмщику этот раздел ни к чему.
_GROUPS = [
    ('Обзор', [
        ('dashboard', 'Дашборд', 'ДБ', {'receiver', 'director'}),
        ('reports', 'Отчёты и аналитика', 'ОТ', {'director'}),
    ]),
    ('Товародвижение', [
        ('catalog', 'Каталог товаров', 'КТ', {'receiver', 'director'}),
        ('receiving', 'Приёмка товара', 'ПР', {'receiver', 'director'}),
        ('stock', 'Склад и остатки', 'СК', {'receiver', 'director'}),
        ('transfers', 'Движение между филиалами', 'ДВ', {'director'}),
    ]),
    ('Коммерция', [
        ('purchasing', 'Закупки и поставщики', 'ЗК', {'receiver', 'director'}),
        ('sales', 'Продажи', 'ПД', {'receiver', 'director'}),
    ]),
    ('Администрирование', [
        ('branches', 'Филиалы', 'ФЛ', {'director'}),
        ('staff', 'Сотрудники и роли', 'СР', {'director'}),
        ('settings', 'Настройки', 'НС', {'director'}),
    ]),
]

# Текущая роль. Захардкожена до появления модуля аутентификации —
# тогда будет браться из профиля вошедшего пользователя.
CURRENT_ROLE = 'receiver'


def nav(request):
    """Боковое меню, собранное под текущую роль."""
    urls = {
        'reports': reverse('reports:reports'),
        'receiving': reverse('receiving:list'),
    }
    for slug in ('dashboard', 'catalog', 'stock', 'transfers',
                 'purchasing', 'sales', 'branches', 'staff', 'settings'):
        urls[slug] = reverse(f'shell:{slug}')

    groups = []
    for title, items in _GROUPS:
        visible = [
            {'id': i, 'label': lbl, 'abbr': ab, 'url': urls.get(i, '#')}
            for i, lbl, ab, roles in items if CURRENT_ROLE in roles
        ]
        # группа без единого доступного пункта не показывается вовсе
        if visible:
            groups.append({'title': title, 'items': visible})
    return {'nav': groups, 'role': CURRENT_ROLE}
