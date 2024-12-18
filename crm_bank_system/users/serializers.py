from django.core.exceptions import ValidationError
from django.utils import timezone

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth import get_user_model
from .models import CustomUser, UserClientCard


User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, label="Фамилия")
    last_name = forms.CharField(required=True, label="Имя")

    ROLE_CHOICES = [
        ('AD', 'Администратор'),
        ('US', 'Пользователь')
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role')


class UserLoginForm(AuthenticationForm):
    class Meta:
        fields = ['username', 'password']

class UserCardForm(forms.ModelForm):

    class Meta:
        model = UserClientCard
        fields = ['card_number', 'expiration_date']
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'})
        }

    def clean_card_number(self):
        card_number = self.cleaned_data['card_number']

        if not card_number.isdigit():
            raise ValidationError("Номер карты должен содержать только цифры.")

        if len(card_number) != 16:
            raise ValidationError("Номер карты должен содержать ровно 16 цифр.")

        return card_number

    def clean_expiration_date(self):
        expiration_date = self.cleaned_data['expiration_date']
        if expiration_date < timezone.now():
            raise ValidationError("Срок действия должен быть в будущем.")
        return expiration_date

class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Текущий пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Пароль должен быть не менее 8 символов, содержать буквы и цифры.",
    )
    new_password2 = forms.CharField(
        label="Повторите новый пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password = cleaned_data.get('new_password1')

        if old_password == new_password:
            raise forms.ValidationError("Новый пароль не может совпадать со старым!")

        return cleaned_data


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Почта",
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text="Введите вашу почту для восстановления пароля."
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с такой почтой не найден.")
        return email


class PasswordResetConfirmForm(SetPasswordForm):
    code = forms.CharField(
        label="Код подтверждения",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Введите код, который был отправлен на вашу почту."
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Введите новый пароль."
    )
    new_password2 = forms.CharField(
        label="Подтвердите новый пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Введите пароль ещё раз для подтверждения."
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("Пароли не совпадают.")
        return cleaned_data