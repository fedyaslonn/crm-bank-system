import json
from locale import currency

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import F
from django.db import connection, transaction, IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.views.generic import RedirectView
from django.db.models import Q

from .forms import TradeCreationForm, ConductTradeForm
from .models import *
from customers.models import ClientCard

from transactions.models import Transaction

from customers.dto import TransactionDTO

from django.utils import timezone

from django.urls import reverse, reverse_lazy

import logging

from friendship.models import Friendship

from users.models import Promos

import plotly.graph_objs as go
from plotly.offline import plot
from django.shortcuts import render
from collections import Counter

from .signals import trade_create_notification

logger = logging.getLogger(__name__)

# Create your views here.

class TradesList(View):
    def get(self, request):
        trades = Trades.objects.all()

        search_query = self.request.GET.get('search', '')
        if search_query:
            trades = trades.filter(currency_to__icontains=search_query)

        paginator = Paginator(trades, 5)
        page = request.GET.get('page')

        try:
            trades = paginator.page(page)
        except PageNotAnInteger:
            trades = paginator.page(1)

        except EmptyPage:
            trades = paginator.page(paginator.num_pages)

        return render(request, "customer/trades_list.html", {"trades": trades})


class TradeCreationView(View):
    def get(self, request):
        trade_type = request.GET.get('trade_type', None)
        form = TradeCreationForm(user=request.user, trade_type=trade_type)
        return render(request, "customer/trades_create.html", {"form": form})

    def post(self, request):
        trade_type = request.POST.get('trades_type', None)
        form = TradeCreationForm(request.POST, user=request.user, trade_type=trade_type)

        if form.is_valid():
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT has_permanent_discount, trades_count, has_used_promo FROM \"Users\" WHERE id = %s",
                            [request.user.id]
                        )
                        user_data = cursor.fetchone()
                        if not user_data:
                            raise ValueError("User not found.")

                        has_permanent_discount, trades_count, has_used_promo = user_data

                        if not has_permanent_discount and trades_count >= 5:
                            raise ValueError("Вы не можете создавать больше трейдов без премиум статуса")
                        if has_permanent_discount and trades_count >= 10:
                            raise ValueError("Вы достигли максимального количества трейдов, даже с премиум статусом.")

                    card = form.cleaned_data["card"]

                    if has_permanent_discount and trades_count < 10:
                        transaction_fee_percentage = Decimal('0.005')
                    elif trades_count < 5 and has_used_promo:
                        transaction_fee_percentage = Decimal('0.007')
                    else:
                        transaction_fee_percentage = Decimal('0.01')

                    db_trade_type = 'UTC' if trade_type == 'USD_to_Crypto' else 'CTU'

                    currency_from = form.cleaned_data["currency_from"]
                    currency_to = form.cleaned_data["currency_to"]
                    amount_from = form.cleaned_data["amount_from"]
                    amount_to = form.cleaned_data["amount_to"]

                    with connection.cursor() as cursor:
                        if currency_to == 'USD':
                            cursor.execute(
                                'SELECT balance_in_usd FROM "Crypto_client_Cards" WHERE id = %s FOR UPDATE',
                                [card.id]
                            )
                            balance_in_usd = Decimal(cursor.fetchone()[0])
                            required_amount = amount_to + (amount_to * transaction_fee_percentage)
                            if balance_in_usd < required_amount:
                                raise ValueError("Недостаточно USD на карте.")

                            new_balance_in_usd = balance_in_usd - required_amount
                            cursor.execute(
                                'UPDATE "Crypto_client_Cards" SET balance_in_usd = %s WHERE id = %s',
                                [new_balance_in_usd, card.id]
                            )
                        else:
                            cursor.execute(
                                'SELECT balance FROM "Crypto_client_Cards" WHERE id = %s FOR UPDATE',
                                [card.id]
                            )
                            balance_json_str = cursor.fetchone()[0]
                            if balance_json_str:
                                try:
                                    balance_json = json.loads(balance_json_str)
                                except json.JSONDecodeError:
                                    balance_json = {}
                            else:
                                balance_json = {}

                            balance = Decimal(balance_json.get(currency_to, '0'))
                            required_amount = amount_to + (amount_to * transaction_fee_percentage)
                            if balance < required_amount:
                                raise ValueError(f"Недостаточно {currency_to} на карте.")

                            new_balance = balance - required_amount
                            cursor.execute(
                                'UPDATE "Crypto_client_Cards" SET balance = coalesce(balance::jsonb, \'{}\'::jsonb) || jsonb_build_object(%s, %s) WHERE id = %s',
                                [currency_to, str(new_balance), card.id]
                            )

                        cursor.execute(
                            'INSERT INTO "Trades" (status, card_id, trades_type, author_id, other_user_id, amount_from, currency_from, amount_to, currency_to, created_at) '
                            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                            [
                                'ACTIVE',
                                card.id,
                                db_trade_type,
                                request.user.id,
                                None,
                                amount_from,
                                currency_from,
                                amount_to,
                                currency_to,
                                timezone.now()
                            ]
                        )

                        new_trades_count = trades_count + 1
                        cursor.execute(
                            "UPDATE \"Users\" SET trades_count = %s WHERE id = %s",
                            [new_trades_count, request.user.id]
                        )

                        cursor.execute(
                            'UPDATE "Crypto_client_Cards" SET transaction_fee_percentage = %s WHERE id = %s',
                            [transaction_fee_percentage, card.id]
                        )

                    return redirect("trades_list")

            except ValueError as e:
                logger.error(f"Ошибка: {e}")
                form.add_error(None, str(e))
            except IntegrityError as e:
                logger.error(f"Ошибка базы данных: {e}")
                form.add_error(None, "Произошла ошибка транзакции. Попробуйте снова.")

        return render(request, "customer/trades_create.html", {"form": form})


class ConductTradeView(View):
    def get(self, request, *args, **kwargs):
        trade_id = kwargs['pk']
        trade = get_object_or_404(Trades, pk=trade_id)
        user = self.request.user

        if user == trade.author:
            messages.error(self.request, "Вы не можете провести собственный трейд.")
            return redirect('trades_list')

        if trade.other_user is not None:
            messages.error(self.request, "Этот трейд уже принят другим пользователем.")
            return redirect('trades_list')

        form = ConductTradeForm(user=user)
        return render(request, "customer/conduct_trade.html", {"form": form, "trade": trade})


    def post(self, request, *args, **kwargs):
        trade_id = kwargs['pk']
        trade = get_object_or_404(Trades, pk=trade_id)
        user = self.request.user

        if user == trade.author:
            messages.error(self.request, "Вы не можете провести собственный трейд.")
            return HttpResponseRedirect(reverse_lazy('trades_list'))

        if trade.other_user is not None:
            messages.error(self.request, "Этот трейд уже принят другим пользователем.")
            return HttpResponseRedirect(reverse_lazy('trades_list'))

        form = ConductTradeForm(user=user, data=request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    consumer_card = form.cleaned_data['card']
                    author_card = ClientCard.objects.get(pk=trade.card.id, is_active=True)

                    is_friendship_active = Friendship.objects.filter(
                        Q(user_from=consumer_card.user, user_to=author_card.user) | Q(user_from=author_card.user, user_to=consumer_card.user),
                    ).exists()

                    if is_friendship_active:
                        transaction_fee_percentage = Decimal('0.005')
                    elif user.has_permanent_discount:
                        transaction_fee_percentage = Decimal('0.005')
                    elif user.has_used_promo:
                        transaction_fee_percentage = Decimal('0.007')
                    else:
                        transaction_fee_percentage = Decimal('0.01')

                    total_fee = trade.amount_from * transaction_fee_percentage

                    consumer_card.deduct_balance(trade.currency_from, trade.amount_from + total_fee)

                    author_card.add_balance(trade.currency_from, trade.amount_from)

                    consumer_card.add_balance(trade.currency_to, trade.amount_to)

                    consumer_card.transaction_fee_percentage = transaction_fee_percentage
                    consumer_card.save()


                    transaction_create_1 = Transaction.objects.create_transaction(
                        transaction_dto=TransactionDTO(
                            sender=user,
                            recipient=trade.author,
                            currency_from=trade.currency_from,
                            currency_to=trade.currency_to,
                            amount=trade.amount_from,
                            type="TRADE"
                        )
                    )

                    transaction_create_2 = Transaction.objects.create_transaction(
                        transaction_dto=TransactionDTO(
                            sender=trade.author,
                            currency_from=trade.currency_from,
                            currency_to=trade.currency_to,
                            recipient=user,
                            amount=trade.amount_to,
                            type="TRADE"
                        )
                    )

                    if transaction_create_1:
                        trade.author.trades_count = F("trades_count") - 1
                        trade.author.save()


                    trade.other_user = user
                    trade.status = 'COMPLETED'
                    trade.save()


                    messages.success(self.request, "Трейд успешно завершен.")

            except ValidationError as e:
                logger.error(f"Ошибка валидации: {str(e)}")
                messages.error(self.request, f"Ошибка: {str(e)}")
            except ClientCard.DoesNotExist:
                logger.error("Активная карта не найдена для одного из пользователей.")
                messages.error(self.request, "У одного из пользователей отсутствует активная карта.")
            except Exception as e:
                logger.error(f"Непредвиденная ошибка: {str(e)}")
                messages.error(self.request, f"Произошла ошибка: {str(e)}")

        return HttpResponseRedirect(reverse_lazy('trades_list'))


def trade_histogram(request):
    trades = Trades.objects.all()
    trade_pairs = [f"{trade.currency_from} → {trade.currency_to}" for trade in trades]

    trade_counts = Counter(trade_pairs)
    labels = list(trade_counts.keys())
    values = list(trade_counts.values())

    bar = go.Bar(
        x=labels,
        y=values,
        text=[f"Количество: {v}" for v in values],
        textposition='auto',
        marker=dict(color='rgba(75, 192, 192, 0.6)', line=dict(color='rgba(75, 192, 192, 1.0)', width=2)),
    )

    layout = go.Layout(
        title='Популярность трейдов',
        xaxis=dict(title='Торговые пары'),
        yaxis=dict(title='Количество сделок'),
    )

    fig = go.Figure(data=[bar], layout=layout)
    plot_div = plot(fig, output_type='div')

    return render(request, 'trades_histogram.html', {'plot_div': plot_div})