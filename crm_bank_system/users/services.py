from django.contrib.auth import authenticate, user_logged_in
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .dto import UserDTO, RequestDTO
from .models import CustomUserManager, CustomUser, RegistrationRequest, RegistrationRequestManager
from .tasks import send_admin_notification, send_registration_notification

from django.test import Client

from loans.models import LoanRequest

from loans.models import Loan


def register_user(data):
    user_dto = UserDTO(
        username=data['username'],
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        password=data['password1'],
        role=data['role'],
        profile_photo=data.get('profile_photo', '')
    )
    user = CustomUser.objects.create_user(user_dto)


    if user_dto.role != 'US':
        send_admin_notification.delay(user_dto.to_dict())

    else:
        send_registration_notification.delay(user_dto.email)

    return user


# def login_user(request, username, password):
#     user = authenticate(request, username=username, password=password)
#
#     if user is not None:
#         CustomUser.objects.update_last_login(user.id)
#         return user
#
#     return None


class RegistrationRequestService:
    @staticmethod
    def approve(request_id):
        RegistrationRequest.objects.approve(request_id)

    @staticmethod
    def reject(request_id):
        RegistrationRequest.objects.reject(request_id)

    @staticmethod
    def get_all_pending():
        return RegistrationRequest.objects.get_all_pending()

def delete_user(id):
    user = get_object_or_404(CustomUser, pk=id)
    user.delete()

class LoanRequestService:
    @staticmethod
    def submit_loan_request(user, loan_dto):
        if LoanRequest.objects.verify_if_request_unique == True:

            loan = Loan.objects.create(
                amount=loan_dto.amount,
                interest_rate=loan_dto.interest_rate,
                term=loan_dto.term,
                user=user,
                status='NOT_SELECTED'
            )

            loan_request = LoanRequest.objects.create(
                user=user,
                loan=loan,
                status='PENDING',
            )

            return loan_request

    @staticmethod
    def review_loan_request(request_id, specialist, is_approved, comments=None):
        loan_request = LoanRequest.objects.select_related("user", "loan").get(pk=request_id)

        if loan_request.status != 'PENDING':
            raise ValueError('Заявка уже обработана')

        if is_approved:
            loan_request.status = 'APPROVED'
            loan_request.loan.status = 'APPROVED'

        else:
            loan_request.status = 'REJECTED'
            loan_request.loan.status = 'REJECTED'

        loan_request.comments = comments
        loan_request.loan.save()
        loan_request.save()