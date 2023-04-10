from django.shortcuts import render

# Create your views here.

def new_account(request):
    return render(request, 'account_list.html')

def new_account_form(request):
    if request.GET.get('new_account_submit'):
        return redirect('/account/new')
    return render(request, 'new_account_form.html')

