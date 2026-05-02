from django.shortcuts import redirect

def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'acc_no' not in request.session:
            return redirect('login')   # redirect to login if not logged in
        return view_func(request, *args, **kwargs)
    return wrapper