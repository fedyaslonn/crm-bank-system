from django.urls import path
from .views import *

urlpatterns = [
    path('transactions/', AdminTransactionListView.as_view(), name='transactions_list'),
    path('users/', AdminUserListView.as_view(), name='users_list'),
    path('users/<int:pk>/edit/', UserEditView.as_view(), name='user_edit'),
    path('trades/', AdminTradesListView.as_view(), name='admin_trades_list'),
    path('trades/<int:trade_id>/freeze/', AdminFreezeTradeView.as_view(), name='admin_freeze_trade'),
    path('trades/<int:trade_id>/activate/', AdminActivateTradeView.as_view(), name='admin_activate_trade'),
    path('users/export/', ExportUsersToExcelView.as_view(), name='export_users_excel'),
    path('transactions/export/', ExportTransactionsToExcelView.as_view(), name='export_transactions_list_excel'),
    path('trades/export/', ExportTradesToExcelView.as_view(), name='export_trades_list_excel'),
    path('respond_to_report/<int:report_id>/', RespondToReportView.as_view(), name='respond_to_report'),
    path('reject_report/<int:report_id>/', RejectReportView.as_view(), name='reject_report'),
    path('pending_reports/', AdminPendingReportsView.as_view(), name='admin_pending_reports'),
    path('admin/export-report-json/<int:report_id>/', ExportReportJsonView.as_view(), name='export_report_json'),
    path('admin/export-all-pending-reports-json/', ExportAllPendingReportsJsonView.as_view(),
         name='export_all_pending_reports_json'),
    path('client_cards/', AdminClientCardsListView.as_view(), name='admin_client_cards_list'),
    path('default_cards/', AdminDefaultCardsListView.as_view(), name='admin_default_cards_list'),
    path('crypto_growth/', crypto_growth_view, name='crypto_analytics'),
    path('admin_index/', AdminIndexView.as_view(), name='admin_index'),
]
