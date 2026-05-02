def is_valid_mobile(mobile):
    return mobile.isdigit() and len(mobile) == 10

def is_valid_acc(acc):
    return acc.isdigit() and len(acc) == 12

def is_valid_aadhar(aadhar):
    return aadhar.isdigit() and len(aadhar) == 12

def is_valid_pin(pin):
    return pin.isdigit() and len(pin) == 6
