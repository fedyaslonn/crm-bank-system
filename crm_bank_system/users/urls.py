from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogOutView.as_view(), name='logout'),
    path('registration_requests/', RegistrationRequestView.as_view(), name='admin_registration_requests'),
    path('registration_requests/<int:pk>/<str:action>/', RegistrationRequestActionView.as_view(), name='registration_request_action'),
    path('users_list/', AdminUserList.as_view(), name='users_list'),
    path('password_change/', UserPasswordChangeView.as_view(), name='password_change'),
    path('profile/edit/<int:user_id>/', UserEditView.as_view(), name='edit_profile'),
    path('password_reset/', UserResetPasswordRequestView.as_view(), name='password_reset_request'),
    path('password_reset/confirm/', UserResetPasswordConfirmView.as_view(), name='password_reset_confirm'),
]