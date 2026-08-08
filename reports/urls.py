from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports, name='reports'),
    path('save/', views.save_report, name='save'),
    path('archive/<int:pk>/delete/', views.delete_report, name='delete'),
]
