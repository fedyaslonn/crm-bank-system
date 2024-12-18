import requests
from django.contrib.auth import get_user_model
from rest_framework.generics import get_object_or_404

from .dto import ClientCardDTO, TransactionDTO
from .models import ClientCard
from transactions.models import Transaction

from django.db import transaction as db_transaction

User = get_user_model()

def get_popular_currencies(retries=3, delay=2):
    api_url = "https://api.exchangerate-api.com/v4/latest/BYN"
    for attempt in range(retries):
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            rates = data['rates']
            popular_currencies = ['USD', 'EUR', 'RUB', 'GBP', 'CNY', 'JPY', 'CAD', 'AUD', 'CHF', 'SGD']
            popular_rates = {currency: rates[currency] for currency in popular_currencies if currency in rates}
            return popular_rates

        except Exception as e:
            raise e

def add_card(data):
    card_dto = ClientCardDTO(
        user=data['user'],
        card_number=data['card_number'],
        expiration_date=data['expiration_date'],
        wallet_address=data['wallet_address'],
        balance=data.get('balance', 0)
    )
    card = ClientCard.objects.create_card(card_dto)

    return card

def get_cards_by_user(user_id):
    return ClientCard.objects.get_cards_by_user(user_id=user_id)

def get_balance_by_card(card_id, user_id):
    card = get_object_or_404(ClientCard, id=card_id, user_id=user_id)
    balance = card.get_balance()
    return card, balance

def make_transaction(sender, recipient, amount):
    try:
        sender = User.objects.get(id=sender)
        recipient_card = ClientCard.objects.get_card_by_card_number(card_num=recipient)

    except User.DoesNotExist:
        raise ValueError("Отправитель не найден")
    except ClientCard.DoesNotExist:
        raise ValueError("Получатель не найден")

    sender_card = ClientCard.objects.get(user=sender.id)
    recipient_inst = get_object_or_404(User, id=recipient_card.user.id)

    if sender_card.balance < amount:
        raise ValueError("Недостаточно средств на карте")

    transaction_dto = TransactionDTO(
        sender=sender,
        recipient=recipient_inst,
        amount=amount
    )

    with db_transaction.atomic():
        transaction = Transaction.objects.create_transaction(transaction_dto)

        ClientCard.objects.withdraw(sender_card, amount)
        recipient_card.balance += amount

        recipient_card.save()
        transaction.save()

    return transaction
