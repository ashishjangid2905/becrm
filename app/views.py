from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages, auth
from django.template import loader
from teams.models import Profile, Branch, User, UserVariable
from teams.views import get_user_variable
from sample.models import sample
from invoice.models import proforma, orderList
from invoice.templatetags.custom_filters import total_order_value, sale_category
from invoice.utils import STATUS_CHOICES
from django.db.models import Count
from django.db.models.functions import ExtractMonth, TruncDate
from django.http import JsonResponse
import calendar, json
from datetime import timedelta
from django.utils.timezone import now
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Create your views here.


@login_required(login_url='app:login')
def home(request):
    if not request.user.is_authenticated:
        return redirect('app:login')
    
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # user_target_variable = UserVariable.objects.filter(variable_name = 'sales_target', user_profile=user_profile).last()

    user_target_variable = get_user_variable(user_profile, 'sales_target')

    user_target = int(user_target_variable)/1000 if user_target_variable else 0

    user_details = {
        'user_id': request.user.id,
        'team_member': request.user.full_name(),
        'role': request.user.role,
        'department': request.user.department
    }

    context = {
        'user_id': request.user.id,
        'user_details': user_details,
        'user_target': user_target
    }

    return render(request, 'dashboard/dashboard.html', context)

@login_required(login_url='app:login')
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('app:login')
    
    user_branch = Profile.objects.get(user=request.user).branch


    all_pi = proforma.objects.all()

    if all_pi:
        for pi in all_pi:
            pi.user_id = get_object_or_404(Profile, user = pi.user_id)

    all_pi_data = all_pi

    pi_list = []

    for pi in all_pi_data:

        pi_data = {
            'pi_date': pi.pi_date,
            'pi_no': pi.pi_no,
            'pi_status': pi.status,
            'pi_user': pi.user_id.id,
            'team_member': pi.user_id.user.full_name(),
            'biller': pi.bank.biller_id.biller_name,
            'bank': pi.bank.bank_name,
            'closed_at': pi.closed_at,
            'totalValue': total_order_value(pi),
            'sales_category': sale_category(pi),
            'order_list': []
        }

        order_items = orderList.objects.filter(proforma_id=pi.id)

        for order in order_items:
            pi_data['order_list'].append({
                'category': order.category,
                'report_type': order.report_type,
                'product': order.product,
                'is_lumpsum': order.is_lumpsum,
                'total_price': order.total_price,
                'lumpsum': order.lumpsum_amt
            })

        pi_list.append(pi_data)

    return JsonResponse(pi_list, safe=False, json_dumps_params={'indent':2})



@login_required(login_url='app:login')
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

@login_required
def settings(request):
    if request.user.role != 'admin':
        return redirect('teams:user_password')
    
    return render(request,'admin/settings.html')


def custom_page_not_found(request, exception):
    return render(request, 'error/page404.html', status=404)