from datetime import timedelta

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from .helpers import date_from_str
from .models import BankBalance, BankBalanceHistory, UserBalance, UserBalanceHistory
from .serializers import (
    BankBalanceHistorySerializer,
    BankBalanceSerializer,
    DateFilterSerializer,
    DepositSerializer,
    TransferSerializer,
    UserBalanceSerializer,
    UserBalanceHistorySerializer,
    UserSerializer,
)
from .schemas import date_filter_schema


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class BankBalanceView(generics.ListCreateAPIView):
    serializer_class = BankBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_balance = hasattr(user, "balance")
        if not user_balance:
            raise NotFound("User has no user balance")

        queryset = BankBalance.objects.filter(user_balance=user_balance)
        return queryset


class BalanceDepositView(generics.CreateAPIView):
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data=data, status=status.HTTP_201_CREATED)


class TransferView(generics.CreateAPIView):
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data=data, status=status.HTTP_201_CREATED)


class UserBalanceView(generics.ListAPIView):
    serializer_class = UserBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        username = self.request.query_params.get("username")
        filter_param = {}
        if not user.is_superuser:
            filter_param["user"] = user
        elif user.is_superuser and username:
            filter_param["user__username"] = username
        queryset = UserBalance.objects.filter(**filter_param).prefetch_related("bank_balance")
        return queryset


class UserBalanceHistoryView(generics.ListAPIView):
    serializer_class = UserBalanceHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        username = self.kwargs["username"]
        filter_param = {}
        query_params = self.request.query_params
        
        if not user.is_superuser:
            if username != user.username:
                return []
            else:
                filter_param["user_balance__user__username"] = user.username
        else:
            filter_param["user_balance__user__username"] = username

        # filter date range
        from_date = query_params.get("start_date")
        end_date = query_params.get("end_date")
        serializer = DateFilterSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        from_date = date_from_str(from_date) if from_date else timezone.localtime() - timedelta(days=7)
        filter_param["created_at__gte"] = from_date
        if end_date:
            filter_param["created_at__lte"] = date_from_str(date_str=end_date, max_time=True)
        
        queryset = UserBalanceHistory.objects.filter(**filter_param).order_by("-created_at")
        return queryset

    @swagger_auto_schema(manual_parameters=date_filter_schema('GET'))
    def get(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)


class BankBalanceHistoryView(generics.ListAPIView):
    serializer_class = BankBalanceHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        bank_code = self.kwargs["code"]
        query_params = self.request.query_params
        filter_param = {}

        if not user.is_superuser:
            filter_param["bank_balance__code"] = bank_code
            filter_param["bank_balance__user_balance__user"] = user
        else:
            filter_param["bank_balance__code"] = bank_code
        
        # filter date range
        from_date = query_params.get("start_date")
        end_date = query_params.get("end_date")
        serializer = DateFilterSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)
        from_date = date_from_str(from_date) if from_date else timezone.localtime() - timedelta(days=7)
        filter_param["created_at__gte"] = from_date
        if end_date:
            filter_param["created_at__lte"] = date_from_str(date_str=end_date, max_time=True)

        queryset = BankBalanceHistory.objects.filter(**filter_param).order_by("-created_at")
        return queryset

    @swagger_auto_schema(manual_parameters=date_filter_schema('GET'))
    def get(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)
