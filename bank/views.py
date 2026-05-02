from datetime import datetime, time, timedelta

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import (
    Account,
    AdminNotification,
    DepositRequest,
    Transaction,
    UserNotification,
)
from .utils import encrypt, generate_acc_no
from .decorators import login_required   # 👈 NEW


def _parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def home(request):
    acc = None

    if 'acc_no' in request.session:
        acc = Account.objects.get(acc_no=request.session['acc_no'])

    return render(request, 'home.html', {'acc': acc})


def create_account(request):
    if request.method == "POST":
        acc = Account.objects.create(
            acc_no = generate_acc_no(),
            name = request.POST['name'],
            mobile = request.POST['mobile'],
            aadhar = request.POST['aadhar'],
            address = request.POST['address'],
            dob = request.POST['dob'],
            gender = request.POST['gender'],
            occupation = request.POST['occupation']
        )
        return redirect('setpin', acc_no=acc.acc_no)

    return render(request,'create_account.html')


def set_pin(request, acc_no):
    acc = Account.objects.get(acc_no=acc_no)

    if request.method == "POST":
        pin = request.POST['pin']
        acc.pin = encrypt(pin)
        acc.save()
        return redirect('login')

    return render(request,'set_pin.html', {'acc':acc})


def login_view(request):
    if request.method == "POST":
        acc_no = request.POST['acc_no']
        pin = encrypt(request.POST['pin'])

        try:
            acc = Account.objects.get(acc_no=acc_no, pin=pin)
            request.session['acc_no'] = acc.acc_no
            return redirect('dashboard')
        except:
            return render(request,'login.html', {'error':'Invalid details'})

    return render(request,'login.html')


# 🔐 PROTECTED VIEWS BELOW


@login_required
def dashboard(request):
    acc = Account.objects.get(acc_no=request.session['acc_no'])
    deposit_requests = acc.deposit_requests.order_by('-requested_at')[:10]
    unread_notifications = acc.notifications.filter(is_read=False).order_by('-created_at')[:5]
    transactions = acc.transactions.select_related("counterparty").order_by("-created_at")[:12]
    return render(
        request,
        'dashboard.html',
        {
            'acc': acc,
            'deposit_requests': deposit_requests,
            'unread_notifications': unread_notifications,
            'transactions': transactions,
        },
    )


@login_required
def deposit(request):
    acc = Account.objects.get(acc_no=request.session['acc_no'])
    error = None
    success = None

    if request.method == "POST":
        try:
            amt = float(request.POST['amount'])
            if amt <= 0:
                error = "Please enter a valid amount greater than 0."
            elif acc.deposit_requests.filter(status=DepositRequest.STATUS_PENDING).count() >= 3:
                error = "You already have 3 pending requests. Please wait for admin review."
            else:
                latest_request = acc.deposit_requests.order_by('-requested_at').first()
                if (
                    latest_request
                    and (timezone.now() - latest_request.requested_at).total_seconds() < 120
                ):
                    error = "Please wait 2 minutes before creating another request."
                else:
                    deposit_request = DepositRequest.objects.create(account=acc, amount=amt)
                    AdminNotification.objects.create(
                        deposit_request=deposit_request,
                        message=(
                            f"New deposit request from {acc.name} "
                            f"(A/C {acc.acc_no}) for Rs {amt}."
                        ),
                    )
                    success = "Deposit request submitted. Amount will be added after admin approval."
        except (TypeError, ValueError):
            error = "Please enter a valid deposit amount."

    return render(request, 'deposit.html', {'error': error, 'success': success})


@login_required
def withdraw(request):
    acc = Account.objects.get(acc_no=request.session['acc_no'])
    error = None

    if request.method == "POST":
        try:
            amt = float(request.POST.get("amount", ""))
        except (TypeError, ValueError):
            msg = "Please enter a valid amount."
            if _is_ajax(request):
                return JsonResponse({"ok": False, "error": msg}, status=400)
            error = msg
            return render(request, "withdraw.html", {"error": error})

        if amt <= 0:
            msg = "Please enter an amount greater than 0."
            if _is_ajax(request):
                return JsonResponse({"ok": False, "error": msg}, status=400)
            error = msg
            return render(request, "withdraw.html", {"error": error})

        if acc.balance >= amt:
            acc.balance -= amt
            acc.save()
            Transaction.objects.create(
                account=acc,
                transaction_type=Transaction.TYPE_WITHDRAW,
                amount=amt,
            )
            if _is_ajax(request):
                return JsonResponse(
                    {
                        "ok": True,
                        "message": "Withdraw Successful",
                        "new_balance": acc.balance,
                    }
                )
            return render(request, "withdraw.html", {"success": True})
        else:
            msg = "Insufficient Funds ❌"
            if _is_ajax(request):
                return JsonResponse({"ok": False, "error": msg})
            error = msg

    return render(request, "withdraw.html", {"error": error})


def logout_view(request):
    request.session.flush()   # clears session
    return redirect('login')

@login_required
def reset_pin(request):
    acc = Account.objects.get(acc_no=request.session['acc_no'])
    error = None
    success = None

    if request.method == "POST":
        old_pin = encrypt(request.POST['old_pin'])
        new_pin = request.POST['new_pin']
        confirm_pin = request.POST['confirm_pin']

        # check old pin
        if acc.pin != old_pin:
            error = "Old PIN is incorrect ❌"

        # check new pin match
        elif new_pin != confirm_pin:
            error = "New PIN and Confirm PIN do not match ❌"

        # check length
        elif len(new_pin) != 6:
            error = "PIN must be 6 digits"

        else:
            acc.pin = encrypt(new_pin)
            acc.save()
            success = "PIN Updated Successfully ✅"

    return render(request, 'reset_pin.html', {
        'error': error,
        'success': success
    })

from .utils import encrypt

@login_required
def transfer(request):
    sender = Account.objects.get(acc_no=request.session['acc_no'])
    error = None
    success = None

    if request.method == "POST":
        receiver_acc_no = request.POST['receiver']
        amount = float(request.POST['amount'])
        pin = encrypt(request.POST['pin'])

        # check PIN first
        if sender.pin != pin:
            error = "Incorrect PIN ❌"
            return render(request, 'transfer.html', {'error': error})

        # check receiver exists
        try:
            receiver = Account.objects.get(acc_no=receiver_acc_no)
        except:
            error = "Receiver account not found ❌"
            return render(request, 'transfer.html', {'error': error})

        # cannot send to self
        if receiver.acc_no == sender.acc_no:
            error = "You cannot transfer to your own account ❌"

        # insufficient balance
        elif sender.balance < amount:
            error = "Insufficient Balance ❌"

        else:
            sender.balance -= amount
            receiver.balance += amount
            sender.save()
            receiver.save()
            Transaction.objects.create(
                account=sender,
                transaction_type=Transaction.TYPE_TRANSFER_SENT,
                amount=amount,
                counterparty=receiver,
            )
            Transaction.objects.create(
                account=receiver,
                transaction_type=Transaction.TYPE_TRANSFER_RECEIVED,
                amount=amount,
                counterparty=sender,
            )
            success = "Money transferred successfully ✅"

    return render(request, 'transfer.html', {
        'error': error,
        'success': success
    })


@login_required
def transaction_history(request):
    acc = Account.objects.get(acc_no=request.session['acc_no'])
    txns = acc.transactions.select_related("counterparty").order_by("-created_at")

    txn_type = request.GET.get("type", "").strip()
    from_date = _parse_date(request.GET.get("from_date", "").strip())
    to_date = _parse_date(request.GET.get("to_date", "").strip())

    if txn_type:
        txns = txns.filter(transaction_type=txn_type)
    if from_date:
        start = timezone.make_aware(datetime.combine(from_date, time.min))
        txns = txns.filter(created_at__gte=start)
    if to_date:
        end_exclusive = timezone.make_aware(
            datetime.combine(to_date + timedelta(days=1), time.min)
        )
        txns = txns.filter(created_at__lt=end_exclusive)

    return render(
        request,
        "transaction_history.html",
        {
            "acc": acc,
            "transactions": txns[:100],
            "selected_type": txn_type,
            "from_date": request.GET.get("from_date", ""),
            "to_date": request.GET.get("to_date", ""),
            "txn_types": Transaction.TYPE_CHOICES,
        },
    )
