import hashlib
from .models import Account

def encrypt(pin):
    return hashlib.sha512(str(pin).encode()).hexdigest()

def generate_acc_no():
    last = Account.objects.order_by('-acc_no').first()
    if last:
        return last.acc_no + 1
    return 1000000001
