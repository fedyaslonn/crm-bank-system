import datetime
from pyexpat.errors import messages

from django.contrib.auth.forms import SetPasswordForm
from django.contrib.messages import error
from django.http.response import HttpResponse
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.views.generic import TemplateView
from keyring import set_password

from rest_framework import status
from urllib3 import request

from .models import RegistrationRequest, RegistrationRequestManager, CustomUser, UserClientCard
from .services import register_user, RegistrationRequestService, delete_user

from .serializers import *

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

import jwt

import logging

from .forms import UserEditForm

import random

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.shortcuts import render, HttpResponse

from .tasks import send_verification_code

# Create your views here.

logging.basicConfig()
logger = logging.getLogger(__name__)

class UserRegisterView(View):
    def get(self, request):
        form = UserRegistrationForm()
        return render(request, 'authentication/register.html', {'form': form})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = register_user(form.cleaned_data)

            backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user, backend=backend)
            return redirect('buy_crypto')
        else:
            form = UserRegistrationForm()
            return render(request, 'authentication/register.html', {'form': form, 'error': 'Ошибка при регистрации'})


class UserLoginView(View):
    def get(self, request):
        form = UserLoginForm()
        return render(request, 'authentication/login.html', {'form': form})

    def post(self, request):
        try:
            form = UserLoginForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                user = authenticate(request, username=username, password=password)

                if user is not None:
                    login(request, user)
                    return redirect('buy_crypto')
                else:
                    return HttpResponse(f"Неверные учетные данные для пользователя: {username}")

            error = 'Ошибка при входе'
            return render(request, 'authentication/login.html', {'form': form, 'error': error})
        except Exception as e:
            logger.error("Ошибка при попытке залогиниться", exc_info=str(e))
            error = 'Внутренняя ошибка сервера. Попробуйте позже.'
            return render(request, 'authentication/login.html', {'form': form, 'error': error})

class UserLogOutView(View):
    def post(self, request):
        logout(request)
        return redirect('login')

    def get(self, request):
        logout(request)
        return redirect('login')

class AdminIndexView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        return render(request, 'admin/admin_index.html')

class RegistrationRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        pending_requests = RegistrationRequest.objects.get_all_pending()
        return render(request, 'admin/admin_registration_requests.html', {'pending_requests': pending_requests})

class RegistrationRequestActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk=None, action=None):
        if action == 'approve':
            RegistrationRequestService.approve(pk)
        elif action == 'reject':
            RegistrationRequestService.reject(pk)

        return redirect('admin_registration_requests')


class AdminUserList(UserPassesTestMixin, TemplateView):
    template_name = "admin/users_list.html"

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get("search", "")
        users = CustomUser.objects.all().order_by("username")

        if search_query:
            users = users.filter(username__icontains=search_query)

        context["users"] = users
        context["search_query"] = search_query
        return context



class AddUsersCard(LoginRequiredMixin, View):
    def get(self, request):
        form = UserCardForm()
        return render(request, "customer/add_user_card.html", {"form": form})

    def post(self, request):
        form = UserCardForm(request.POST)
        if form.is_valid():
            card_number = form.cleaned_data["card_number"]
            expiration_date = form.cleaned_data['expiration_date']

            user_card = UserClientCard(
                user=request.user,
                card_number=card_number,
                expiration_date=expiration_date
            )

            user_card.save()

            return redirect('buy_crypto')
        return render(request, "customer/add_user_card.html", {"form": form})

class UserDefaultCards(LoginRequiredMixin, View):
    def get(self, request):
        sort = request.GET.get("sort", "")

        cards = UserClientCard.objects.filter(user=request.user)
        first_card = cards.order_by('created_at').first()

        if sort == "asc":
            cards = cards.order_by("created_at")
        else:
            cards = cards.order_by("-created_at")

        return render(request, "customer/user_default_cards.html", {"cards": cards, "first_card": first_card, "sort": sort})

class UserPasswordChangeView(View):
    def get(self, request):
        form = UserPasswordChangeForm(user=request.user)
        return render(request, 'authentication/password_change.html', {'form': form})

    def post(self, request):
        form = UserPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password1"]
            user = request.user
            user.set_password(new_password)
            user.save()

            update_session_auth_hash(request, user)

            return redirect('profile')
        return render(request, 'authentication/password_change.html', {'form': form})


class UserEditView(View, LoginRequiredMixin):
    def get(self, request, user_id):
        user = CustomUser.objects.get(id=user_id)
        form = UserEditForm(instance=user)
        return render(request, "customer/user_profile_edit.html", {"user": user, "form": form})

    def post(self, request, user_id):
        user = CustomUser.objects.get(id=user_id)
        form = UserEditForm(request.POST, instance=user)

        if form.is_valid():
            user.username = form.cleaned_data["username"]
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]

            user.save()

            return redirect('profile')

        else:
            return render(request, "customer/user_profile_edit.html", {"form": form, "user": user})

class UserResetPasswordRequestView(View):
    def get(self, request):
        form = PasswordResetRequestForm()
        return render(request, 'authentication/password_reset_request.html', {'form': form})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            code = random.randint(10000, 99999)
            request.session["reset_code"] = code
            request.session["reset_email"] = email
            send_verification_code.delay(email, code)
            return redirect('password_reset_confirm')

        return render(request, 'authentication/password_reset_request.html', {'form': form})


class UserResetPasswordConfirmView(View):
    def get(self, request):
        email = request.session.get("reset_email")
        if not email:
            return redirect('password_reset_request')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return redirect('password_reset_request')  # Redirect if user not found

        form = PasswordResetConfirmForm(user=user)
        return render(request, 'authentication/password_reset_confirm.html', {'form': form})

    def post(self, request):
        email = request.session.get("reset_email")
        reset_code = request.session.get("reset_code")
        if not email or not reset_code:
            return redirect('password_reset_request')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return redirect('password_reset_request')

        form = PasswordResetConfirmForm(user=user, data=request.POST)

        if form.is_valid():
            code = form.cleaned_data["code"]
            if str(code) == str(reset_code):
                form.save()

                del request.session["reset_code"]
                del request.session["reset_email"]

                return redirect("login")
            else:
                form.add_error("code", "Неверный код подтверждения.")

        return render(request, 'authentication/password_reset_confirm.html', {'form': form})
