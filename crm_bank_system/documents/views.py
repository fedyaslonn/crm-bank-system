from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .forms import ReportForm
from .services import create_report, create_report_document, reports_list, get_detail_report

from .models import Report

# Create your views here.

class ReportCreateView(View):
    def get(self, request):
        form = ReportForm()
        return render(request, 'documents/report_create.html', {'form': form})

    def post(self, request):
        form = ReportForm(request.POST)
        if form.is_valid():
            description = form.cleaned_data['description']
            screenshot = form.cleaned_data['screenshot']
            report = create_report(user=request.user.id,
                                   description=description,
                                   screenshot=screenshot)
            document = create_report_document(report)
            return redirect('documents:my_reports')
        return render(request, 'documents/report_create.html', {'form': form})


class ReportDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'AD'

    def get(self, request, report_id):
        report = get_detail_report(report_id=report_id)
        return render(request, 'documents/report_detail.html', {'report': report})

class MyReportsListView(LoginRequiredMixin, View):
    def get(self, request):
        # Get query parameters for sorting and filtering
        sort = request.GET.get('sort', 'desc')  # Default to newest first
        status = request.GET.get('status', None)  # Default to all statuses

        # Filter reports by status if a status is selected
        reports = Report.objects.filter(user=request.user)
        if status:
            reports = reports.filter(status=status)

        if sort == 'asc':
            reports = reports.order_by('created_at')
        else:
            reports = reports.order_by('-created_at')

        return render(request, 'customer/my_reports_list.html', {'reports': reports, 'sort': sort, 'status': status})

class EditReportView(LoginRequiredMixin, View):
    def get(self, request, report_id):
        report = get_object_or_404(Report, id=report_id, user=request.user)
        form = ReportForm(instance=report)
        return render(request, 'documents/edit_report.html', {'form': form, 'report': report})

    def post(self, request, report_id):
        report = get_object_or_404(Report, id=report_id, user=request.user)
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            return redirect('documents:my_reports')
        return render(request, 'documents/edit_report.html', {'form': form, 'report': report})