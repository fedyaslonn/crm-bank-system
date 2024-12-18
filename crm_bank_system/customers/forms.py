from django import forms
from .models import ClientCard
from users.models import UserClientCard
from django.utils import timezone
from django.core.exceptions import ValidationError

class ClientCardForm(forms.ModelForm):
    class Meta:
        model = ClientCard
        fields = ['card_number', 'expiration_date', 'wallet_address']
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'})
        }

    def clean_wallet_address(self):
        wallet_address = self.cleaned_data['wallet_address']

        if not wallet_address:
            raise ValidationError("Адрес кошелька не может быть пустым.")

        if len(wallet_address) < 10 or len(wallet_address) > 42:
            raise ValidationError("Адрес кошелька должен содержать от 10 до 42 символов.")

        if not all(c.isalnum() or c in ['_', '-', ':'] for c in wallet_address):
            raise ValidationError("Адрес кошелька может содержать только буквы, цифры, дефисы, подчеркивания и двоеточие.")

        return wallet_address

    def clean_card_number(self):
        card_number = self.cleaned_data['card_number']

        if not card_number.isdigit():
            raise ValidationError("Номер карты должен содержать только цифры.")

        if len(card_number) != 16:
            raise ValidationError("Номер карты должен содержать ровно 16 цифр.")

        return card_number

    def clean_expiration_date(self):
        expiration_date = self.cleaned_data['expiration_date']
        if expiration_date < timezone.now().date():
            raise ValidationError("Срок действия должен быть в будущем.")
        return expiration_date

class ClientTransferForm(forms.Form):
    card_number = forms.CharField(
        label='Номер карты',
        max_length=16,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите номер карты'})
    )
    amount = forms.DecimalField(
        label='Сумма',
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Введите сумму'})
    )


class BalanceRechargeForm(forms.Form):
    amount = forms.DecimalField(
        label="Сумма пополнения",
        min_value=10,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'placeholder': "Введите сумму"})
    )

class TopUpCryptoCardForm(forms.Form):
    user_regular_cards = forms.ModelChoiceField(
        queryset=None,
        label="Выберите обычную карту",
        empty_label="Выберите карту",
        limit_choices_to=None
    )
    crypto_cards = forms.ModelChoiceField(
        queryset=None,
        label="Выберите криптовалютную карту",
        empty_label="Выберите карту",
        limit_choices_to=None
    )
    amount = forms.DecimalField(
        label="Сумма в USD",
        min_value=1,
        decimal_places=2,
        max_digits=10
    )


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)
        self.fields['user_regular_cards'].queryset = UserClientCard.objects.filter(user=user, is_active=True)
        self.fields['crypto_cards'].queryset = ClientCard.objects.filter(user=user, is_active=True)


class TopUpDefaultCardForm(forms.Form):
    user_regular_cards_to = forms.ModelChoiceField(
        queryset=None,
        label="Выберите обычную карту для пополнения",
        empty_label="Выберите карту",
        limit_choices_to=None
    )

    user_regular_cards_from = forms.ModelChoiceField(
        queryset=None,
        label="Выберите другую обычную карту для списания",
        empty_label="Выберите карту",
        limit_choices_to=None
    )

    amount = forms.DecimalField(
        label="Сумма для перевода",
        min_value=0.01,
        decimal_places=2,
        max_digits=10,
        help_text="Введите сумму для перевода между картами"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        initial = kwargs.get('initial', {})
        super().__init__(*args, **kwargs)
        self.fields['user_regular_cards_to'].queryset = UserClientCard.objects.filter(user=user, is_active=True)
        self.fields['user_regular_cards_from'].queryset = UserClientCard.objects.filter(user=user, is_active=True)

        if initial.get('user_regular_cards_from'):
            self.fields['user_regular_cards_from'].initial = initial['user_regular_cards_from']

    def clean(self):
        cleaned_data = super().clean()
        card_to = cleaned_data.get('user_regular_cards_to')
        card_from = cleaned_data.get('user_regular_cards_from')
        amount = cleaned_data.get('amount')

        if card_to == card_from:
            raise ValidationError("Карты для пополнения и списания должны быть разными!")

        if card_from.balance < amount:
            raise ValidationError("Недостаточно средств на карте для списания!")

        return cleaned_data


class PromocodeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        if hasattr(self.user, "promo"):
            raise forms.ValidationError("У вас уже есть промокод.")
        return super().clean()


from django import forms

class TopUpDefaultCardByCryptoCardForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['user_regular_cards'].queryset = UserClientCard.objects.filter(user=user, is_active=True)
        self.fields['crypto_cards'].queryset = ClientCard.objects.filter(user=user, is_active=True)

    user_regular_cards = forms.ModelChoiceField(
        queryset=UserClientCard.objects.none(),
        label="Обычная карта для пополнения",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    crypto_cards = forms.ModelChoiceField(
        queryset=ClientCard.objects.none(),
        label="Криптовалютная карта для списания",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Сумма пополнения (USD)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Введите сумму'}),
        required=True,
        min_value=0.01
    )
