from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages, auth
from django.template import loader
from teams.models import Profile, Branch, User
from sample.models import sample
from django.db.models import Count
from django.db.models.functions import ExtractMonth, TruncDate
from django.http import JsonResponse
import calendar, json
from datetime import timedelta
from django.utils.timezone import now
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Create your views here.


def home(request):
    if request.user.is_authenticated:
        user_branch = Profile.objects.get(user=request.user).branch
        total_samples = sample.objects.filter(user__profile__branch = user_branch.id)

        if request.user.role == 'admin':
            user_sample = total_samples
        else:
            user_sample = total_samples.filter(user = request.user)

        total_samples = user_sample.count()
        received_sample = user_sample.filter(status='received').count()
        pending_sample = user_sample.filter(status='pending').count()

        context = {
            'total_samples': total_samples,
            'received_sample': received_sample,
            'pending_sample': pending_sample,
        }

        return render(request, 'dashboard/dashboard.html', context)
    else:
        return redirect('app:login')

@login_required(login_url='app:home')
def sample_chart(request):

    if not request.user.is_authenticated:
        return redirect('app:login')
    # filter_count = {
    #     'status__icontains': 'received',
    #     'status__icontains': 'pending',
    #     'status__icontains': 'reject'
    #                 }

    user_branch = Profile.objects.get(user=request.user).branch

    total_samples = sample.objects.filter(user__profile__branch = user_branch.id)
    if request.user.role == 'admin':
        user_sample = total_samples
    else:
        user_sample = total_samples.filter(user = request.user)
    

    # received_sample = user_sample.filter(status='received').count()
    # pending_sample = user_sample.filter(status='pending').count()
    # rejected_sample = user_sample.filter(status='reject').count()

    last_month = now() - timedelta(days=30)

    samples_per_day = user_sample.filter(requested_at__gte = last_month).annotate(date=TruncDate('requested_at')).values('date').annotate(count=Count('sample_id')).order_by('date')
        
    status_counts = user_sample.values('status').annotate(count=Count('sample_id')).order_by('status')
    doughnut_data = {status['status']: status['count'] for status in status_counts}

    samples_data = user_sample.annotate(
            month_name = ExtractMonth('requested_at')
            ).values('month_name').annotate(
                counts = Count('sample_id')
                ).order_by('month_name')
        
    months = []
    sample_counts = []
    per_day_count = {str(sample['date']):sample['count'] for sample in samples_per_day}

    for sample_data in samples_data:
        months.append(calendar.month_name[sample_data['month_name']])
        sample_counts.append(sample_data['counts'])
    
    data = {
        'month_labels': months,
        'sample_counts': sample_counts,
        'doughnut_data':doughnut_data,
        'per_day_count': per_day_count
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


def custom_page_not_found(request, exception):
    return render(request, 'error/page404.html', status=404)