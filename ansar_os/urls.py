from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='reports:reports', permanent=False)),
    path('reports/', include('reports.urls')),
    path('receiving/', include('receiving.urls')),
    path('m/', include('shell.urls')),
]