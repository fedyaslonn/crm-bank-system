from django.shortcuts import get_object_or_404

from .dto import LoanDTO
from .models import Loan, LoanRequest


def create_loan(amount, interest_rate, term):
    loan_dto = LoanDTO(amount=amount,
                       interest_rate=interest_rate,
                       term=term)
    created_loan = Loan.objects.create_loan(loan_dto)
    return created_loan

def get_all_loans():
    loans = Loan.objects.get_loans()
    return loans

def get_loan_requests():
    loans = LoanRequest.objects.get_loans()
    return loans

def create_request_loan(loan_offer_id, user):
    loan_offer = get_object_or_404(Loan, id=loan_offer_id)
    if LoanRequest.objects.filter(user=user, status='PENDING').exists():
        raise ValueError(f'У пользователя уже существует запрос на кредит!')

    loan_request = LoanRequest.objects.create(
        user=user,
        loan=loan_offer,
        status='PENDING',
        comments=''
    )

    loan_offer.status = 'PENDING'
    loan_offer.save()
    return loan_request