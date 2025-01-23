from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template import loader
from teams.models import Profile, Branch, User, UserVariable
from sample.models import sample
from invoice.models import proforma, orderList
from invoice.templatetags.custom_filters import total_order_value, sale_category
from teams.templatetags.teams_custom_filters import get_current_position, get_current_target
from invoice.utils import STATUS_CHOICES
from django.db.models import Count, Q, Min, Max
from django.db.models.functions import ExtractMonth, TruncDate
from django.http import JsonResponse
import calendar
from datetime import timedelta, datetime
from django.utils.timezone import now

from .activity_log_utils import log_user_activity, get_action
from .models import ActivityLog

# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication



class Home(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        content = {'message': 'hello world'}
        return Response(content)



@login_required(login_url='app:login')
def home(request):
    if not request.user.is_authenticated:
        return redirect('app:login')
    
    user_profile = get_object_or_404(Profile, user=request.user)
    
    # user_target_variable = UserVariable.objects.filter(variable_name = 'sales_target', user_profile=user_profile).last()

    user_target_variable = get_current_target(user_profile)

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
    
    today = now().date()

    # Get the fiscal year range
    date_range = proforma.objects.aggregate(min_date=Min('pi_date'), max_date=Max('pi_date'))
    min_year = date_range['min_date'].year if date_range['min_date'] else today.year
    max_year = date_range['max_date'].year if date_range['max_date'] else today.year

    fiscal_years = [f"{year}-{year + 1}" for year in range(min_year, max_year + 1)]

    selected_fy = request.GET.get('fy', None)

    if selected_fy:
        fy_start_year = int(selected_fy.split('-')[0])
        fy_start = datetime(fy_start_year, 4, 1).date()
        fy_end = datetime(fy_start_year + 1, 3, 31).date()
    else:
        fy_start = datetime(today.year - 1, 4, 1).date() if today.month < 4 else datetime(today.year, 4, 1).date()
        fy_end = datetime(fy_start.year + 1, 3, 31).date()
    
    user_profile = Profile.objects.get(user=request.user)
    user_branch = user_profile.branch

    all_users = Profile.objects.filter(branch=user_branch)
    
    current_position = get_current_position(user_profile)
    user_role = request.user.role
    if current_position != 'Head' and user_role != 'admin':
        all_users = all_users.exclude(user__groups__name__in=['Head'])

    all_users = all_users
    
    all_user_ids = []
    for user in all_users:
        all_user_ids.append(user.user.id)

    all_proforma = proforma.objects.filter(user_id__in = all_user_ids)

    selected_month = request.GET.get('select_month')
    selected_user = request.GET.get('select_user')
    filters = {'user_id__in': all_user_ids, 'pi_date__range': (fy_start, fy_end)}
    if selected_user:
        filters['user_id'] = selected_user

    if selected_month:
        year, month = map(int, selected_month.split("-"))
        start_date = datetime(year, month, 1).date()
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day).date()
        filters['closed_at__range'] = (start_date, end_date)
    

    all_pi = all_proforma.filter(**filters).select_related('bank', 'bank__biller_id')


    if all_pi:
        for pi in all_pi:
            pi.user_id = get_object_or_404(Profile, user = pi.user_id)

    pi_list = []
    for pi in all_pi:
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

    action = get_action(request)

    if action:
        log_user_activity(request, action)

    logout(request)
    messages.success(request,"You have Logged Out")
    return redirect('app:login')

@login_required
def settings(request):
    if request.user.role != 'admin':
        return redirect('teams:user_password')
    
    return render(request,'admin/settings.html')

@login_required(login_url='app:login')
def logs(request):
    if not request.user.is_authenticated:
        return redirect('app:login')
    
    activity_logs = ActivityLog.objects.all()

    context = {
        'activity_logs': activity_logs,
    }

    return render(request, 'activity_log.html', context)


def custom_page_not_found(request, exception):
    return render(request, 'error/page404.html', status=404)