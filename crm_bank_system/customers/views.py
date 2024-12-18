from decimal import Decimal, InvalidOperation
from django.contrib import messages

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, connection
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy

from django.views import View

from django.db.models import F
from django.views.generic import DetailView

from .dto import TransactionDTO
from .models import ClientCard
from .services import get_popular_currencies, add_card, get_cards_by_user, get_balance_by_card, make_transaction

from .forms import *

import requests

from users.models import UserClientCard, CustomUser

import logging

import string
import random

from users.models import Promos

from transactions.models import Transaction

logger = logging.getLogger(__name__)

# Create your views here.

class CustomerIndexView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'customer/user_index.html')

class RatesListView(View):
    def get(self, request):
        currencies = get_popular_currencies()
        context = {'rates': currencies}
        return render(request, 'customer/currencies_list.html', context=context)

class CardAddView(View):
    def get(self, request):
        form = ClientCardForm()
        return render(request, 'customer/add_client_card.html', {'form': form})

    def post(self, request):
        form = ClientCardForm(request.POST)
        if form.is_valid():
            card_data = form.cleaned_data
            card_data['user'] = request.user
            card = add_card(card_data)
            if card is not None:
                return redirect(reverse_lazy("card_list"))
        return render(request, 'customer/add_client_card.html', {'form': form})

class CardListView(View):
    def get(self, request):
        sort = request.GET.get("sort", "")

        cards = ClientCard.objects.filter(user=request.user)

        if sort == "asc":
            cards = cards.order_by("created_at")
        elif sort == "desc":
            cards = cards.order_by("-created_at")
        else:
            cards = cards.order_by("created_at")

        first_card = cards.order_by("created_at").first()

        return render(
            request,
            "customer/card_list.html",
            {"cards": cards, "sort": sort, "first_card": first_card},
        )

class BalanceView(LoginRequiredMixin, View):
    def get(self, request, card_id):
        user_id = request.user.id
        card, balance = get_balance_by_card(card_id, user_id)
        return render(request, 'customer/user_balance.html', {'balance': balance, 'card': card})

class TransferView(LoginRequiredMixin, View):
    def get(self, request):
        form = ClientTransferForm()
        return render(request, 'customer/user_transfers.html', {'form': form})

    def post(self, request):
        form = ClientTransferForm(request.POST)
        if form.is_valid():
            card_number = form.cleaned_data['card_number']
            amount = form.cleaned_data['amount']
            transaction = make_transaction(sender=request.user.id, recipient=card_number, amount=amount)
            return HttpResponse('Деньги успешно переведены')
        return render(request, 'customer/user_transfers.html', {'form': form})

def buy_crypto(request):
    api_url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 5,
        "page": 1,
        "sparkline": False
    }
    response = requests.get(api_url, params=params)
    crypto_data = response.json() if response.status_code == 200 else []

    if request.user.is_authenticated:
        user_cards = request.user.cards.filter(is_active=True)

    else:
        user_cards = []

    context = {
        "crypto_data": crypto_data,
        "user_cards": user_cards
    }
    return render(request, 'customer/buy_crypto.html', context)


def process_purchase(request):
    if request.method == 'POST':
        logger.info(f"Received POST data: {request.POST}")

        # Приводим валюту к верхнему регистру
        crypto_symbol = request.POST.get('crypto', '').strip().upper()
        card_number = request.POST.get('card_number')
        amount_str = request.POST.get('amount', '0')
        crypto_hidden = request.POST.get('crypto_hidden', '0')

        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                raise ValueError("Сумма должна быть больше нуля")
        except (InvalidOperation, ValueError):
            messages.error(request, "Некорректная сумма")
            return redirect('buy_crypto')

        if not crypto_symbol or not card_number:
            messages.error(request, "Некорректные данные")
            return redirect('buy_crypto')

        try:
            client_calculated_crypto_amount = Decimal(crypto_hidden).quantize(Decimal('0.00000001'))
        except (InvalidOperation, ValueError):
            messages.error(request, "Некорректные данные о криптовалюте")
            return redirect('buy_crypto')

        try:
            crypto_rate = Decimal(request.POST.get('crypto_rate', '0'))
            if crypto_rate <= 0:
                raise ValueError("Курс криптовалюты должен быть больше нуля")
        except (InvalidOperation, ValueError) as e:
            logger.warning(f"Invalid crypto_rate: {crypto_rate}. Error: {e}")
            messages.error(request, "Некорректный курс криптовалюты")
            return redirect('buy_crypto')

        server_calculated_crypto_amount = (amount / crypto_rate).quantize(Decimal('0.00000001'))

        tolerance = Decimal('0.00000001')
        if abs(client_calculated_crypto_amount - server_calculated_crypto_amount) > tolerance:
            messages.error(request, "Ошибка в расчетах криптовалюты. Попробуйте снова.")
            return redirect('buy_crypto')

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT id, balance_in_usd, COALESCE(balance, \'{}\'::jsonb) FROM "Crypto_client_Cards" WHERE card_number = %s AND user_id = %s AND is_active = TRUE FOR UPDATE',
                    [card_number, request.user.id]
                )
                card = cursor.fetchone()
                if not card:
                    messages.error(request, "Карта не найдена или неактивна")
                    return redirect('buy_crypto')

                card_id, balance_in_usd, balance = card

                if balance_in_usd < amount:
                    messages.error(request, "Недостаточно средств на карте")
                    return redirect('buy_crypto')

                cursor.execute(
                    """
                    UPDATE "Crypto_client_Cards"
                    SET balance_in_usd = balance_in_usd - %s
                    WHERE id = %s
                    """,
                    [amount, card_id]
                )

                # Обновляем баланс в криптовалюте
                cursor.execute(
                    """
                    UPDATE "Crypto_client_Cards"
                    SET balance = jsonb_set(
                        COALESCE(balance, '{}'::jsonb),  -- Гарантируем, что balance это JSON
                        %s,
                        COALESCE(
                            (balance->>%s)::numeric + %s,
                            %s
                        )::text::jsonb
                    )
                    WHERE id = %s
                    """,
                    [f'{{{crypto_symbol}}}', crypto_symbol, server_calculated_crypto_amount, server_calculated_crypto_amount, card_id]
                )

        messages.success(request, f"Успешно приобретено {server_calculated_crypto_amount:.8f} {crypto_symbol}")
        return redirect('buy_crypto')

    return redirect('buy_crypto')



class BalanceRechargeView(View, LoginRequiredMixin):
    def get(self, request, card_id):
        card = ClientCard.objects.get(id=card_id)
        if card.user != request.user:
           return render(request, 'customer/add_balance.html', {'error_message': "Вы не можете пополнить баланс чужой карты!"})
        form = BalanceRechargeForm()
        return render(request, 'customer/add_balance.html', {'form': form, 'card': card})

    def post(self, request, card_id):
        card = ClientCard.objects.get(id=card_id)
        if request.user != card.user:
            render(request, 'customer/add_balance.html', {'error_message': "Вы не можете пополнить баланс чужой карты!"})
        form = BalanceRechargeForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            card.update_balance('USD', amount)
            return redirect('card_list')
        return render(request, 'customer/balance_recharge.html', {'form': form, 'card': card})


class TopUpCryptoCardView(View, LoginRequiredMixin):
    def post(self, request):
        form = TopUpCryptoCardForm(request.POST, user=request.user)
        if form.is_valid():
            regular_card_id = form.cleaned_data["user_regular_cards"].id
            crypto_card_id = form.cleaned_data["crypto_cards"].id
            amount = form.cleaned_data["amount"]

            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT balance FROM "Client_Cards" WHERE id = %s FOR UPDATE',
                        [regular_card_id]
                    )
                    regular_card_balance = cursor.fetchone()[0]
                    if regular_card_balance < amount:
                        messages.error(request, "Недостаточно средств на обычной карте")
                        return redirect('top_up_crypto_card')

                    cursor.execute(
                        'SELECT balance_in_usd FROM "Crypto_client_Cards" WHERE id = %s FOR UPDATE',
                        [crypto_card_id]
                    )
                    crypto_card_balance = cursor.fetchone()[0]

                    cursor.execute(
                        """
                        UPDATE "Client_Cards"
                        SET balance = balance - %s
                        WHERE id = %s
                        """,
                        [amount, regular_card_id]
                    )

                    cursor.execute(
                        """
                        UPDATE "Crypto_client_Cards"
                        SET balance_in_usd = balance_in_usd + %s
                        WHERE id = %s
                        """,
                        [amount, crypto_card_id]
                    )

                    cursor.execute(
                        """
                        INSERT INTO "Transactions" (status, type, sender_id, recipient_id, currency_from, currency_to, amount, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """,
                        [
                            "COMPLETED", "REPLENISHMENT", request.user.id, request.user.id,
                            "USD", "USD", amount
                        ]
                    )

                    transaction_to_create = Transaction(
                        status="COMPLETED",
                        type="REPLENISHMENT",
                        sender=request.user,
                        recipient=request.user,
                        currency_from="USD",
                        currency_to="USD",
                        amount=amount
                    )


                messages.success(request, "Пополнение успешно произведено")
                return redirect('buy_crypto')

        messages.error(request, "Неправильно заполнена форма")
        return redirect('top_up_crypto_card')


    def get(self, request):
        form = TopUpCryptoCardForm(user=request.user)
        return render(request, 'customer/top_up_crypto_card.html', {'form': form})


class TopUpDefaultCardByCryptoCardView(View, LoginRequiredMixin):
    def get(self, request):
        form = TopUpCryptoCardForm(user=request.user)
        return render(request, 'customer/top_up_crypto_card_by_default_card.html', {'form': form})
    def post(self, request):
        form = TopUpDefaultCardByCryptoCardForm(request.POST, user=request.user)
        if form.is_valid():
            regular_card = form.cleaned_data["user_regular_cards"]
            crypto_card = form.cleaned_data["crypto_cards"]
            amount = form.cleaned_data["amount"]
            with transaction.atomic():
                if crypto_card.balance_in_usd < amount:
                    messages.error(request, "Недостаточно средств на криптовалютной карте")
                    return redirect('top_up_default_card_by_crypto')
                ClientCard.objects.filter(pk=crypto_card.id).update(balance_in_usd=F('balance_in_usd') - amount)
                regular_card = UserClientCard.objects.get(pk=regular_card.id)

                regular_card.balance = F('balance') + amount
                regular_card.save()


                transaction_to_create = Transaction(
                    status="COMPLETED",
                    type="REPLENISHMENT",
                    sender=request.user,
                    recipient=request.user,
                    currency_from="USD",
                    currency_to="USD",
                    amount=amount
                )

                transaction_to_create.save()

                messages.success(request, "Пополнение успешно произведено")
                return redirect('top_up_crypto_card')

            messages.error(request, "Неправильно заполнена форма")
            return redirect('top_up_default_card_by_crypto')



class UserProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = "customer/customer_profile.html"
    context_object_name = "user_profile"

    def get_object(self, queryset=None):
        return get_object_or_404(CustomUser, pk=self.request.user.pk)


    def post(self, request, *args, **kwargs):
        form = PromocodeForm(request.POST, user=request.user)

        if form.is_valid():
            with transaction.atomic():
                user_cards = UserClientCard.objects.filter(user=request.user, is_active=True).order_by("created_at")


                if hasattr(request.user, 'promo'):
                    messages.error(request, "Вы уже создали свой промокод!")
                    return redirect("profile")

                card_to_use = None
                for user_card in user_cards:
                    if user_card.balance >= 20:
                        card_to_use = user_card
                        break

                if not card_to_use:
                    messages.error(request, "Не удалось создать промокод. Для создания промокода необходимо минимум 20 USD на карте!")
                    return redirect("profile")

                card_to_use.balance -= 20
                card_to_use.save()


                promo_code = self.generate_unique_promo_code()

                promo = Promos.objects.create(user=request.user, promo_code=promo_code, promo_usage=0)

                promo.save()
            messages.success(request, f"Ваш промокод успешно создан: {promo_code}")

        else:
            messages.error(request, "Не удалось создать промокод. Попробуйте снова.")

        return redirect("profile")

    def generate_unique_promo_code(self, length=8):
        characters = string.ascii_uppercase + string.digits

        while True:
            promo_code = ''.join(random.choices(characters, k=length))
            if not Promos.objects.filter(promo_code=promo_code).exists():
                return promo_code


class ApplyPromocode(LoginRequiredMixin, View):
    def post(self, request):
        promo_code = request.POST.get("promo_code")
        if not promo_code:
            messages.error(request, "Промокод не указан.")
            return redirect("profile")
        try:
            promo = Promos.objects.get(promo_code=promo_code)

        except Promos.DoesNotExist:
            messages.error(request, "Указанный промокод не существует.")
            return redirect("profile")
        author = promo.user
        customer = request.user

        if customer == author:
            messages.error(request, "Вы не можете использовать свой собственный промокод.")
            return redirect("profile")

        if customer.has_used_promo:
            messages.error(request, "Вы уже использовали промокод.")
            return redirect("profile")

        with transaction.atomic():
            promo.promo_usage += 1
            promo.save()

            customer.has_used_promo = True
            customer.save()

            if promo.promo_usage >= 5:
                author.has_permanent_discount = True
                author.save()
            messages.success(request, f"Промокод {promo_code} успешно применен!")

        return redirect("profile")

class DeleteCardView(LoginRequiredMixin, View):
    def post(self, request, card_id):
        with transaction.atomic():
            card = get_object_or_404(UserClientCard, id=card_id)

            card_user = card.user

            if UserClientCard.objects.filter(user=card_user).count() == 1:
                return redirect('default_cards')

            first_card = UserClientCard.objects.filter(user=card_user).order_by('created_at').first()

            if first_card and first_card.id != card.id:
                first_card.balance += card.balance
                first_card.save()

            card.delete()

            return redirect('default_cards')

class FreezeCardView(LoginRequiredMixin, View):
    def post(self, request, card_id):
        card = get_object_or_404(UserClientCard, id=card_id)

        if not request.user.is_staff:
            return redirect('user_default_cards')

        card.is_active = False
        card.save()

        return redirect('default_cards')

class UnfreezeCardView(LoginRequiredMixin, View):
    def post(self, request, card_id):
        card = get_object_or_404(UserClientCard, id=card_id)

        if not request.user.is_staff:
            return redirect('default_cards')

        card.is_active = True
        card.save()
        messages.success(request, "Карта успешно разморожена.")

        return redirect('default_cards')


class TopUpDefaultCardView(LoginRequiredMixin, View):
    def get(self, request, card_id):
        if card_id:
            card_to = get_object_or_404(UserClientCard, id=card_id, user=request.user, is_active=True)

            form = TopUpDefaultCardForm(user=request.user, initial={'user_regular_cards_to': card_to})
            return render(request, 'customer/top_up_default_card.html', {'form': form})


    def post(self, request, card_id):
        form = TopUpDefaultCardForm(request.POST, user=request.user)
        if form.is_valid():
            card_to = form.cleaned_data['user_regular_cards_to']
            card_from = form.cleaned_data['user_regular_cards_from']
            amount = form.cleaned_data['amount']

            with transaction.atomic():
                card_from.balance = F('balance') - amount
                card_from.save()

                card_to.balance = F('balance') + amount
                card_to.save()

                Transaction.objects.create_transaction(
                    transaction_dto=TransactionDTO(
                        sender=card_from.user,
                        recipient=card_to.user,
                        amount=amount,
                        type="REPLENISHMENT"
                    )
                )

                messages.success(request, "Баланс успешно пополнен.")
                return redirect('default_cards')

        messages.error(request, "Ошибка при пополнении баланса.")
        return render(request, 'customer/top_up_default_card.html', {'form': form})


class DeleteCryptoCardView(LoginRequiredMixin, View):
    def post(self, request, card_id):
        with transaction.atomic():
            card = get_object_or_404(ClientCard, id=card_id)

            if ClientCard.objects.filter(user=request.user).count() == 1:
                messages.error(request, "Нельзя удалить последнюю карту.")
                return redirect('card_list')

            first_card = ClientCard.objects.filter(user=request.user).order_by('created_at').first()

            if first_card and first_card.id != card.id:
                # Проверяем, что card.balance — это словарь
                first_card.balance_in_usd += card.balance_in_usd

                if isinstance(card.balance, dict):
                    for currency, amount in card.balance.items():
                        amount = Decimal(amount)
                        first_card.update_balance(currency, amount)

                first_card.save()
                    # Обработка случая, если card.balance не является словарем

            card.delete()

            messages.success(request, "Карта успешно удалена.")
            return redirect('card_list')

class FreezeCryptoCardView(View):
    def post(self, request, card_id):
        card = get_object_or_404(ClientCard, id=card_id)

        if not request.user.is_superuser:
            return redirect('card_list')

        card.is_active = False
        card.save()

        next_url = request.GET.get('next', 'admin_client_cards_list')

        messages.success(request, "Карта успешно заморожена.")
        return redirect('card_list')


class UnfreezeCryptoCardView(View):
    def post(self, request, card_id):
        card = get_object_or_404(ClientCard, id=card_id)

        if not request.user.is_superuser:
            return redirect('card_list')

        card.is_active = True
        card.save()
        messages.success(request, "Карта успешно разморожена.")
        return redirect('card_list')


class TransactionHistoryView(LoginRequiredMixin, View):
    def get(self, request):
        transaction_list = Transaction.objects.filter(
            sender=request.user
        ) | Transaction.objects.filter(
            recipient=request.user
        )

        transaction_list = transaction_list.order_by('-created_at')

        return render(request, 'customer/transactions_history.html', {
            'transaction_list': transaction_list
        })