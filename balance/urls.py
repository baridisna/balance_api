from django.urls import path

from .views import (
    BankBalanceView,
    BankBalanceHistoryView,
    BalanceDepositView,
    TransferView,
    UserBalanceView,
    UserBalanceHistoryView)

urlpatterns = [
    path("user/", UserBalanceView.as_view()),
    path("user/<username>/history/", UserBalanceHistoryView.as_view()),
    path("deposit/", BalanceDepositView.as_view()),
    path("transfer/", TransferView.as_view()),
    path("bank/", BankBalanceView.as_view()),
    # path("bank/{code}/update-enable/", BankBalanceView.as_view())
    path("bank/<code>/history/", BankBalanceHistoryView.as_view())
]