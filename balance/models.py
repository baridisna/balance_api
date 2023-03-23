from django.contrib.auth.models import User
from django.db import models

from balance import settings as app_settings


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserBalance(BaseModel):
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name="balance")
    balance = models.CharField(max_length=255, null=True, blank=True)
    balance_achieve = models.PositiveBigIntegerField()

    class Meta:
        db_table = "balance_user_balance"


class UserBalanceHistory(BaseModel):
    user_balance = models.ForeignKey(UserBalance, on_delete=models.PROTECT, related_name="history")
    balance_before = models.PositiveBigIntegerField()
    balance_after = models.PositiveBigIntegerField()
    activity = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=app_settings.TRANSACTION_TYPE)
    ip = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    author = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "balance_user_balance_history"


class BankBalance(BaseModel):
    user_balance = models.ForeignKey(UserBalance, on_delete=models.PROTECT, related_name="bank_balance")
    balance = models.PositiveBigIntegerField()
    balance_achieve = models.PositiveBigIntegerField()
    code = models.CharField(max_length=50, unique=True)
    enable = models.BooleanField(default=True)

    class Meta:
        db_table = "balance_bank_balance"


class BankBalanceHistory(BaseModel):
    bank_balance = models.ForeignKey(BankBalance, on_delete=models.PROTECT, related_name="history")
    balance_before = models.PositiveBigIntegerField()
    balance_after = models.PositiveBigIntegerField()
    activity = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=app_settings.TRANSACTION_TYPE)
    ip = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    author = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "balance_bank_balance_history"
