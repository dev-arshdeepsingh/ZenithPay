from django.db import models

class Account(models.Model):
    acc_no = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=32)
    mobile = models.BigIntegerField(unique=True)
    aadhar = models.BigIntegerField(unique=True)
    address = models.CharField(max_length=256)
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    occupation = models.CharField(max_length=50)
    pin = models.CharField(max_length=200, default="0")
    balance = models.FloatField(default=1000)

    def __str__(self):
        return self.name


class DepositRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="deposit_requests",
    )
    amount = models.FloatField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    note = models.CharField(max_length=255, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.account.name} - {self.amount} ({self.status})"


class UserNotification(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account.name} - {self.message}"


class AdminNotification(models.Model):
    deposit_request = models.ForeignKey(
        DepositRequest,
        on_delete=models.CASCADE,
        related_name="admin_notifications",
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class Transaction(models.Model):
    TYPE_DEPOSIT = "deposit"
    TYPE_WITHDRAW = "withdraw"
    TYPE_TRANSFER_SENT = "transfer_sent"
    TYPE_TRANSFER_RECEIVED = "transfer_received"

    TYPE_CHOICES = (
        (TYPE_DEPOSIT, "Deposit"),
        (TYPE_WITHDRAW, "Withdraw"),
        (TYPE_TRANSFER_SENT, "Transfer Sent"),
        (TYPE_TRANSFER_RECEIVED, "Transfer Received"),
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.FloatField()
    counterparty = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_transactions",
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account.acc_no} - {self.transaction_type} - {self.amount}"
