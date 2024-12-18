from django.urls import path
from .views import *

app_name = 'documents'

urlpatterns = [
    path('create_report/', ReportCreateView.as_view(), name='create_report'),
    path('report_detail/<report_id>/', ReportDetailView.as_view(), name='report_detail'),
    path('my_reports/', MyReportsListView.as_view(), name='my_reports'),
    path('edit_report/<int:report_id>/', EditReportView.as_view(), name='edit_report'),
]