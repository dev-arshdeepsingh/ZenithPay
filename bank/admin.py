from django.contrib import admin
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .forms import AccountAdminForm
from .models import (
    Account,
    AdminNotification,
    DepositRequest,
    Transaction,
    UserNotification,
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    form = AccountAdminForm
    list_display = ("acc_no", "name", "mobile", "balance")
    search_fields = ("acc_no", "name", "mobile")
    readonly_fields = ("pin",)
    fieldsets = (
        (
            "Account",
            {
                "fields": (
                    "acc_no",
                    "name",
                    "mobile",
                    "aadhar",
                    "address",
                    "dob",
                    "gender",
                    "occupation",
                    "balance",
                )
            },
        ),
        (
            "PIN",
            {
                "fields": ("pin", "new_pin", "confirm_new_pin"),
                "description": (
                    "The PIN is stored as a hash and cannot be viewed. "
                    "Enter a new 6-digit PIN below to reset it for this customer."
                ),
            },
        ),
    )


@admin.register(DepositRequest)
class DepositRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "amount", "status", "requested_at", "reviewed_at")
    list_filter = ("status", "requested_at")
    search_fields = ("account__name", "account__acc_no", "id")
    readonly_fields = ("requested_at", "reviewed_at")
    actions = ("approve_selected_requests", "reject_selected_requests")

    @admin.action(description="Approve selected deposit requests")
    def approve_selected_requests(self, request, queryset):
        with transaction.atomic():
            pending_requests = queryset.select_for_update().filter(
                status=DepositRequest.STATUS_PENDING
            )

            for deposit_request in pending_requests:
                Account.objects.filter(pk=deposit_request.account_id).update(
                    balance=F("balance") + deposit_request.amount
                )
                Transaction.objects.create(
                    account_id=deposit_request.account_id,
                    transaction_type=Transaction.TYPE_DEPOSIT,
                    amount=deposit_request.amount,
                    note="Deposit approved by admin",
                )
                UserNotification.objects.create(
                    account_id=deposit_request.account_id,
                    message=f"Your deposit request of Rs {deposit_request.amount} has been approved.",
                )
                AdminNotification.objects.filter(
                    deposit_request=deposit_request
                ).update(is_read=True)

            updated_count = pending_requests.update(
                status=DepositRequest.STATUS_APPROVED,
                reviewed_at=timezone.now(),
            )

        self.message_user(
            request,
            f"{updated_count} deposit request(s) approved and credited.",
        )

    @admin.action(description="Reject selected deposit requests")
    def reject_selected_requests(self, request, queryset):
        pending_requests = queryset.filter(status=DepositRequest.STATUS_PENDING)
        for deposit_request in pending_requests:
            UserNotification.objects.create(
                account_id=deposit_request.account_id,
                message=f"Your deposit request of Rs {deposit_request.amount} has been rejected.",
            )
            AdminNotification.objects.filter(deposit_request=deposit_request).update(
                is_read=True
            )

        updated_count = pending_requests.update(
            status=DepositRequest.STATUS_REJECTED, reviewed_at=timezone.now()
        )
        self.message_user(
            request,
            f"{updated_count} deposit request(s) rejected.",
        )


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "message", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("account__name", "account__acc_no", "message")
    actions = ("mark_as_read",)

    @admin.action(description="Mark selected notifications as read")
    def mark_as_read(self, request, queryset):
        updated_count = queryset.update(is_read=True)
        self.message_user(request, f"{updated_count} notification(s) marked as read.")


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "deposit_request", "message", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("message", "deposit_request__account__name", "deposit_request__id")
    actions = ("mark_as_read",)

    @admin.action(description="Mark selected notifications as read")
    def mark_as_read(self, request, queryset):
        updated_count = queryset.update(is_read=True)
        self.message_user(request, f"{updated_count} notification(s) marked as read.")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "account",
        "transaction_type",
        "amount",
        "counterparty",
        "created_at",
    )
    list_filter = ("transaction_type", "created_at")
    search_fields = ("account__acc_no", "account__name", "counterparty__acc_no")
