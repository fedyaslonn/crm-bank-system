from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render
from urllib3 import request

from .forms import LoanForm
from .models import Loan, LoanRequest
from .services import create_loan, get_all_loans, get_loan_requests, create_request_loan
from users.services import LoanRequestService


# Create your views here.

class CreateLoanView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'LS'

    def get(self, request):
        form = LoanForm()
        return render(request, 'loans/loan_request.html', {'form': form})

    def post(self, request):
        form = LoanForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            interest_rate = form.cleaned_data['interest_rate']
            term = form.cleaned_data['term']

            create_loan(amount=amount,
                        interest_rate=interest_rate,
                        term=term)

            return HttpResponse("Кредит успешно создан")
        return render(request, 'loans/loan_request.html', {'form': form})

class LoanListView(LoginRequiredMixin, View):
    def get(self, request):
        loan_offers = get_all_loans()
        return render(request, 'loans/loan_offer_list.html', {'loan_offers': loan_offers})


class LoanRequestList(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == "LS"

    def get(self, request):
        loan_requests = get_loan_requests()
        return render(request, 'loans/loan_requests_list.html', {'loan_requests': loan_requests})

class LoanRequestReviewView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == "LS"

    def post(self, request, pk):
        loan_request = get_object_or_404(LoanRequest, pk=pk)
        is_approved = request.POST.get('is_approved') == 'true'
        comments = request.POST.get('comments', '')

        try:
            LoanRequestService.review_loan_request(request_id=pk, specialist=request.user, is_approved=is_approved, comments=comments)
            return HttpResponse('Заявка успешно обработана')
        except ValueError as e:
            return HttpResponse('Не получилось обработать заявку')

class LoanRequestCreateView(LoginRequiredMixin, View):
    def post(self, request, loan_offer_id):
        user = request.user

        loan_request = create_request_loan(loan_offer_id, user)
        if loan_request:
            return redirect('list')

        return redirect('list')

class LoanRequestApproveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == "LS"

    def post(self, request, loan_request_id):
        loan_request = get_object_or_404(LoanRequest, id=loan_request_id)
        loan_request.status = 'APPROVED'
        loan_request.save()
        return redirect(reverse_lazy('loan_requests_list'))

class LoanRequestRejectView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == "LS"

    def post(self, request, loan_request_id):
        loan_request = get_object_or_404(LoanRequest, id=loan_request_id)
        loan_request.status = 'REJECTED'
        loan_request.save()
        return redirect(reverse_lazy('loan_requests_list'))