# urls.py
from django.urls import path
from django.conf import settings

from .views import upload_pdf, get_pdf, get_deficiency_report, generate_deficiency_report

urlpatterns = [
    path('upload-pdf/', upload_pdf, name='upload_pdf'),
    # path('upload-multiple-pdfs/', upload_multiple_pdfs, name='upload_pdf'),
    path('get-pdf/<str:start_date>/<str:end_date>/', get_pdf, name='get_pdf'),
    path('generate-deficiency-report/<str:id>/',generate_deficiency_report),
    path('get-deficiency-report/<str:id>/',get_deficiency_report),
]
