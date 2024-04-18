from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import leads
from teams.models import User

# Create your views here.

@login_required(login_url='app:login')
def leads_list(request):

    if not request.user.is_authenticated:
        return redirect('app:login')
    
    all_leads = leads.objects.all()
    user_id = request.user.id

    if request.user.role == 'admin':
        user_leads = all_leads
    else:
        user_leads = leads.objects.filter(user=user_id)

    user_details = {}
    if user_leads.exists():
        for lead in user_leads:
            user_details[lead.user] = User.objects.get(pk=lead.user)

    context = {
        'user_leads': user_leads,
        'user_details': user_details
    }
    
    return render(request, 'lead/leads.html', context)