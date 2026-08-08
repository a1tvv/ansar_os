from django.urls import path
from . import views

app_name = 'receiving'

urlpatterns = [
    path('', views.doc_list, name='list'),
    path('new/', views.doc_new, name='new'),
    path('<int:pk>/', views.doc_detail, name='detail'),
    path('<int:pk>/add-line/', views.add_line, name='add_line'),
    path('<int:pk>/line/<int:line_id>/delete/', views.delete_line, name='delete_line'),
    path('<int:pk>/post/', views.post_document, name='post'),
]
