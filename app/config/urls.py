from django.urls import path, include
from django.contrib import admin
from .yasg import urlpatterns as doc_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('main.urls')),
]

urlpatterns.extend(doc_urls)

