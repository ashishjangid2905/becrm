from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages, auth
from django.template import loader
from teams.models import Profile, Branch, User
from sample.models import sample
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.http import JsonResponse
import datetime, calendar, json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Create your views here.


def home(request):
    if request.user.is_authenticated:
        samples = sample.objects.all().count()
        received_sample = sample.objects.filter(status='received').count()
        pending_sample = sample.objects.filter(status='pending').count()

        context = {
            'total_samples': samples,
            'received_sample': received_sample,
            'pending_sample': pending_sample,
        }

        return render(request, 'dashboard/dashboard.html', context)
    else:
        return redirect('app:login')

@login_required(login_url='app:home')
def sample_chart(request):

    # filter_count = {
    #     'status__icontains': 'received',
    #     'status__icontains': 'pending',
    #     'status__icontains': 'reject'
    #                 }

    received_sample = sample.objects.filter(status='received').count()
    pending_sample = sample.objects.filter(status='pending').count()
    rejected_sample = sample.objects.filter(status='reject').count()

    samples_data = sample.objects.annotate(
            month_name = ExtractMonth('requested_at')
            ).values('month_name').annotate(
                counts = Count('sample_id')
                ).order_by('month_name')
        
    months = []
    sample_counts = []

    for sample_data in samples_data:
        months.append(calendar.month_name[sample_data['month_name']])
        sample_counts.append(sample_data['counts'])
    
    data = {
        'month_labels': months,
        'sample_counts': sample_counts,
        'rejected_sample':rejected_sample,
        'received_sample':received_sample,
        'pending_sample':pending_sample


    }

    return JsonResponse(data)

def login_user(request):
    if request.method == 'POST':
        email =  request.POST['email']
        password =  request.POST['password']

        user = authenticate(request, email=email, password=password)
        if user is not None:

            login(request, user)
            return redirect('app:home')
        else:
            messages.success(request, "There was an Error, Please Try again")
            return redirect('app:login')
    elif request.user.is_authenticated:
        return redirect('app:home')
    else:
        return render(request, 'login.html')

@login_required
def logout_user(request):
    logout(request)
    messages.success(request,"You have Logged Out")
    return redirect('app:login')