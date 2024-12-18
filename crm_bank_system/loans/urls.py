from django.urls import path
from .views import *


urlpatterns = [
    path('create_loan/', CreateLoanView.as_view(), name='create_loan'),
    path('list/', LoanListView.as_view(), name='list'),
    path('loan_request/<int:loan_offer_id>/', LoanRequestCreateView.as_view(), name='loan_request_create'),
    path('loan_request_list/', LoanRequestList.as_view(), name='loan_requests_list'),
    path('loan_request/<int:loan_request_id>/approve/', LoanRequestApproveView.as_view(), name='loan_request_approve'),
    path('loan_request/<int:loan_request_id>/reject/', LoanRequestRejectView.as_view(), name='loan_request_reject'),
]