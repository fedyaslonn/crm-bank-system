from django.urls import path
from .views import *
from users.views import UserDefaultCards, AddUsersCard

urlpatterns = [
    path('customer_index/', CustomerIndexView.as_view(), name='customer_index'),
    path('currencies_list/', RatesListView.as_view(), name='currencies_list'),
    path('add_custom_card/', CardAddView.as_view(), name='add_card'),
    path('card_list/', CardListView.as_view(), name='card_list'),
    path('check_balance/<int:card_id>/', BalanceView.as_view(), name='check_balance'),
    path('customer_transfers/', TransferView.as_view(), name='customer_transfers'),
    path('buy/', buy_crypto, name='buy_crypto'),
    path('process_purchase/', process_purchase, name='process_purchase'),
    path('add_balance/<int:card_id>/', BalanceRechargeView.as_view(), name='add_balance'),
    path('top_up_crypto_card/', TopUpCryptoCardView.as_view(), name='top_up_crypto_card'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('apply_promo_code/', ApplyPromocode.as_view(), name='apply_promo_code'),
    path('user_cards_list/', UserDefaultCards.as_view(), name='default_cards'),
    path('add_users_card/', AddUsersCard.as_view(), name='add_users_card'),
    path('cards/delete/<int:card_id>/', DeleteCardView.as_view(), name='delete_card'),
    path('cards/freeze/<int:card_id>/', FreezeCardView.as_view(), name='freeze_card'),
    path('cards/unfreeze/<int:card_id>/', UnfreezeCardView.as_view(), name='unfreeze_card'),
    path('top_up_default_card/<int:card_id>/', TopUpDefaultCardView.as_view(), name='top_up_default_card'),
    path('crypto_cards/delete/<int:card_id>/', DeleteCryptoCardView.as_view(), name='delete_crypto_card'),
    path('crypto_cards/freeze/<int:card_id>/', FreezeCryptoCardView.as_view(), name='freeze_crypto_card'),
    path('crypto_cards/unfreeze/<int:card_id>/', UnfreezeCryptoCardView.as_view(), name='unfreeze_crypto_card'),
    path('transactions_history/', TransactionHistoryView.as_view(), name='transaction_history'),
    path('top_up_default_card_by_crypto/', TopUpDefaultCardByCryptoCardView.as_view(), name='top_up_default_card_by_crypto')
]