from django.urls import path
from . import views

app_name = 'receiving'

urlpatterns = [
    path('', views.doc_list, name='list'),
    path('new/', views.doc_new, name='new'),
    # Печать — общая для всего проекта: принимает документ, выбранные
    # позиции или товары каталога, поэтому лежит отдельно от карточки.
    path('print/', views.print_setup, name='print_setup'),
    path('print/sheet/', views.print_sheet, name='print_sheet'),
    path('<int:pk>/', views.doc_detail, name='detail'),
    path('<int:pk>/add-line/', views.add_line, name='add_line'),
    path('<int:pk>/line/<int:line_id>/update/', views.update_line, name='update_line'),
    path('<int:pk>/line/<int:line_id>/delete/', views.delete_line, name='delete_line'),
    path('<int:pk>/payment/', views.update_payment, name='update_payment'),
    path('<int:pk>/post/', views.post_document, name='post'),
    path('<int:pk>/bulk/', views.bulk_lines, name='bulk_lines'),
]
