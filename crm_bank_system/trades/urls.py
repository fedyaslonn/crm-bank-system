from django.urls import path, include
from .views import *

urlpatterns = [
    path('trades_list/', TradesList.as_view(), name='trades_list'),
    path('trades_creation/', TradeCreationView.as_view(), name='trade_creation'),
    path('trades/<int:pk>/conduct/', ConductTradeView.as_view(), name='conduct_trade'),
    path('trade_histogram/', trade_histogram, name='trade_histogram')
]