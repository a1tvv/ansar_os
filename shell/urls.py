from django.urls import path
from . import views

app_name = 'shell'

PAGES = ['dashboard', 'catalog', 'stock', 'transfers', 'purchasing', 'sales', 'branches', 'staff', 'settings']

urlpatterns = [path(f'{p}/', views.page, {'slug': p}, name=p) for p in PAGES]
