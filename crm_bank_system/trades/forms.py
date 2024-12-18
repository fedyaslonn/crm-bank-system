from decimal import Decimal

from django import forms
from .models import Trades
from customers.models import ClientCard


class TradeCreationForm(forms.Form):
    TRADE_TYPES = [
        ('USD_to_Crypto', 'USD в Крипто'),
        ('Crypto_to_USD', 'Крипто в USD'),
    ]

    CRYPTO_CURRENCIES = [
        ("BTC", "Bitcoin"),
        ("ETH", "Ethereum"),
        ("USDT", "USDT"),
        ("SOL", "Solana"),
        ("XRP", "XPR"),
    ]

    USD = [("USD", "USD")]

    card = forms.ModelChoiceField(
        queryset=None,  # Will be set dynamically
        label="Выберите карту",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_card'}),
        required=True
    )

    trades_type = forms.ChoiceField(
        choices=TRADE_TYPES,
        label="Тип трейда",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_trades_type'}),
        required=True
    )

    currency_from = forms.ChoiceField(
        choices=[],  # Заполняется динамически
        label="Требуемая валюта",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_currency_from'}),
        required=True
    )

    currency_to = forms.ChoiceField(
        choices=[],  # Заполняется динамически
        label="Предлагаемая валюта",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_currency_to'}),
        required=True
    )

    amount_from = forms.DecimalField(
        max_digits=20,
        decimal_places=8,
        label="Количество требуемой валюты",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_amount_from'}),
        required=True
    )

    amount_to = forms.DecimalField(
        max_digits=20,
        decimal_places=8,
        label="Количество предлагаемой валюты",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_amount_to'}),
        required=True
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        trade_type = kwargs.pop('trade_type', None)
        super().__init__(*args, **kwargs)

        # Установка queryset для поля card
        if user:
            cards = ClientCard.objects.filter(user=user, is_active=True)
            self.fields['card'].queryset = cards
            if cards.exists():
                self.fields['card'].initial = cards.first()
            else:
                self.fields['card'].queryset = ClientCard.objects.none()  # Если карт нет
                self.fields['card'].widget.attrs['disabled'] = 'disabled'
                self.fields['card'].help_text = "У вас нет активных карт. Добавьте карту, чтобы создать трейд."

        # Логика для выбора валют
        if trade_type == 'USD_to_Crypto':
            self.fields['currency_from'].choices = self.USD
            self.fields['currency_to'].choices = self.CRYPTO_CURRENCIES
        elif trade_type == 'Crypto_to_USD':
            self.fields['currency_from'].choices = self.CRYPTO_CURRENCIES
            self.fields['currency_to'].choices = self.USD
        else:
            self.fields['currency_from'].choices = self.USD + self.CRYPTO_CURRENCIES
            self.fields['currency_to'].choices = self.USD + self.CRYPTO_CURRENCIES


    def clean(self):
        cleaned_data = super().clean()
        trades_type = cleaned_data.get("trades_type")
        currency_from = cleaned_data.get("currency_from")
        currency_to = cleaned_data.get("currency_to")

        if trades_type == 'USD_to_Crypto' and currency_from != 'USD':
            raise forms.ValidationError("Для типа трейда USD в Крипто валюта 'Предлагаемая' должна быть USD.")
        if trades_type == 'Crypto_to_USD' and currency_to != 'USD':
            raise forms.ValidationError("Для типа трейда Крипто в USD валюта 'Требуемая' должна быть USD.")
        if currency_from == currency_to:
            raise forms.ValidationError("Предлагаемая и требуемая валюты не могут совпадать.")

        return cleaned_data

    def calculate_fee_percentage(self, user):
        if user.has_permanent_discount and user.trades_count < 10:
            return Decimal('0.005')
        elif user.trades_count < 5 and user.has_used_promo:
            return Decimal('0.007')
        return Decimal('0.01')


class ConductTradeForm(forms.Form):
    card = forms.ModelChoiceField(
        queryset=ClientCard.objects.none(),
        label="Выберите карту для проведения трейда",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['card'].queryset = ClientCard.objects.filter(user=user, is_active=True)