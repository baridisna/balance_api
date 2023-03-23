import uuid

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError

from .models import UserBalance, BankBalance, BankBalanceHistory, UserBalanceHistory
from .helpers import get_ip_location


def calculate_balance(model_balance, request, amount, history_model, added_data, transaction_type, activity):
        prev_balance = model_balance.balance_achieve
        current_balance = (prev_balance + amount) if transaction_type == "debit" else (prev_balance - amount)
        model_balance.balance_achieve = current_balance
        model_balance.balance = current_balance
        model_balance.save()

        # Make history balance
        user_data = get_ip_location(request)
        bank_balance_history_data = {
            "balance_before": prev_balance,
            "balance_after":current_balance,
            "activity": activity,
            "type": transaction_type,
            "ip": user_data["ip"],
            "location": user_data["location"],
            "user_agent": user_data["user_agent"]
        }

        history_model.objects.create(**added_data, **bank_balance_history_data)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "email", "username", "password"]

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create(email=validated_data["email"],
                                    username=validated_data["username"])
        user.set_password(validated_data["password"])
        user.save()

        # create user_account
        user_balance = UserBalance.objects.create(user=user, balance_achieve=0)
        # create bank_account
        bank_balance_data = {
            "user_balance": user_balance,
            "balance": 0,
            "balance_achieve": 0,
            "code": user.username + '_' + uuid.uuid4().hex[:4].upper()
        }
        BankBalance.objects.create(**bank_balance_data)
            
        return user


class BankBalanceSerializer(serializers.ModelSerializer):
    balance = serializers.IntegerField(read_only=True)
    balance_achieve = serializers.IntegerField(read_only=True)
    code = serializers.CharField(read_only=True)
    enable = serializers.BooleanField(read_only=True)

    class Meta:
        model = BankBalance
        fields = ["id", "balance", "balance_achieve", "code", "enable"]
    
    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        user_balance = hasattr(user, "balance")
        if not user_balance:
            raise NotFound("User has no user balance")
        bank_balance_data = {
            "user_balance": user_balance,
            "balance": 0,
            "balance_achieve": 0,
            "code": user.username + '_' + uuid.uuid4().hex[:4].upper()
        }
        bank_balance = BankBalance.objects.create(**bank_balance_data)

        return bank_balance


class DepositSerializer(serializers.Serializer):
    code_bank = serializers.CharField(write_only=True)
    amount = serializers.IntegerField(min_value=100, max_value=2000000000, write_only=True)
    balance = serializers.IntegerField(read_only=True)
    balance_achieve = serializers.IntegerField(read_only=True)
    code = serializers.CharField(read_only=True)
    enable = serializers.BooleanField(read_only=True)

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not request.user or not request.user.balance:
            raise NotFound("Not found")
        user = request.user
        user_balance = user.balance
        bank_balance = BankBalance.objects.filter(code=validated_data["code_bank"], user_balance=user_balance)

        # Validate user has bank
        if not bank_balance:
            raise ValidationError({"code_bank": "Bank code not found"})
        
        bank_balance = bank_balance[0]
        amount = validated_data["amount"]
        # calculate bank balance
        calculate_balance(bank_balance, request, amount, BankBalanceHistory, {"bank_balance": bank_balance}, "debit", "deposit")

        # calculate user balance
        calculate_balance(user_balance, request, amount, UserBalanceHistory, {"user_balance": user_balance}, "debit", "deposit")

        return {"success": True}


class TransferSerializer(serializers.Serializer):
    destination_bank_code = serializers.CharField()
    source_bank_code = serializers.CharField()
    amount = serializers.IntegerField(min_value=100, max_value=2000000000)

    def validate(self, attrs):
        if attrs["destination_bank_code"] == attrs["source_bank_code"]:
            raise ValidationError({"destination_bank_code": "cannot be the same with source_bank_code"})
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not request.user or not request.user.balance:
            raise NotFound("Not found")
        user = request.user
        amount = validated_data["amount"]

        # Validate destination_bank exist
        try:
            destination_bank = BankBalance.objects.get(code=validated_data["destination_bank_code"])
        except BankBalance.DoesNotExist:
            raise ValidationError({"destination_bank_code": "The destination bank code did not exist"})

        # Validate source_bank_code exist
        source_bank = BankBalance.objects.filter(code=validated_data["source_bank_code"], user_balance=user.balance)
        if not source_bank:
            raise ValidationError({"source_bank_code": "The source bank cannot be found"})
        source_bank = source_bank[0]

        # Validate amount cannot less than balance
        if source_bank.balance_achieve < amount:
            raise ValidationError({"amount": "Your balance not enough"})

        # Calculate balance destination bank
        calculate_balance(
            destination_bank, request, amount, BankBalanceHistory, {"bank_balance": destination_bank}, "debit", "transfer")
        # Calculate balance source bank balance
        calculate_balance(
            source_bank, request, amount, BankBalanceHistory, {"bank_balance": source_bank}, "kredit", "transfer")
        
        if source_bank.user_balance == destination_bank.user_balance:
            return {"success": True}

        # Calculate balance destination user balance
        calculate_balance(
            destination_bank.user_balance,
            request,
            amount,
            UserBalanceHistory,
            {"user_balance": destination_bank.user_balance},
            "debit",
            "transfer")
        # Calculate balance source user balance
        calculate_balance(
            user.balance, request, amount, UserBalanceHistory, {"user_balance": user.balance}, "kredit", "transfer")

        return {"success": True}


class UserBalanceSerializer(serializers.ModelSerializer):
    bank_balances = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    class Meta:
        model = UserBalance
        fields = ["id", "username", "balance", "balance_achieve", "bank_balances"]
    
    def get_bank_balances(self, obj):
        bank_balances_obj = obj.bank_balance.all()
        bank_balances = []
        if bank_balances_obj:
            for bank_balance in bank_balances_obj:
                bank_balances.append({
                    "balance": bank_balance.balance,
                    "balance_achieve": bank_balance.balance_achieve,
                    "code": bank_balance.code,
                    "enable": bank_balance.enable
                })
        return bank_balances
    
    def get_username(self, obj):
        username = obj.user.username
        return username


class DateFilterSerializer(serializers.Serializer):
    from_date = serializers.DateField(format="%Y-%m-%d", required=False)
    end_date = serializers.DateField(format="%Y-%m-%d", required=False)

    def validate(self, attrs):
        if attrs.get("from_date") and attrs.get("end_date"):
            if attrs["from_date"] > attrs["end_date"]:
                raise ValidationError("from_date cannot bigger than end_date")
        if attrs.get("end_date") and not attrs.get("from_date"):
            raise ValidationError({"from_date": "from_date required if there is end_date"})
        return attrs


class UserBalanceHistorySerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")    

    class Meta:
        model = UserBalanceHistory
        fields = [
            "id",
            "created_at",
            "balance_before",
            "balance_after",
            "activity",
            "type",
            "ip",
            "location",
            "user_agent",
            "author"
        ]


class BankBalanceHistorySerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")    

    class Meta:
        model = UserBalanceHistory
        fields = [
            "id",
            "created_at",
            "balance_before",
            "balance_after",
            "activity",
            "type",
            "ip",
            "location",
            "user_agent",
            "author"
        ]
