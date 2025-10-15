from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from student_management_system import settings
from django.conf.urls.i18n import i18n_patterns

urlpatterns =[
    path('admin/', admin.site.urls),
    path('', include('apps.student_management.urls', namespace="student_management")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


