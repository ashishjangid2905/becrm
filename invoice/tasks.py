from celery import shared_task
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from datetime import datetime

from .models import proforma, processedOrder
from teams.models import Profile, User
from teams.templatetags.teams_custom_filters import get_current_position

@shared_task
def get_pi_list(user_ids, selected_fy, selected_user, selected_ap, selected_status, query, page_size, page_number):
    
    today = datetime.now().date()

    if selected_fy:
        start_year = int(selected_fy.split('-')[0])
        end_year = start_year+1

        fy_start = datetime(start_year, 4, 1).date()
        fy_end = datetime(end_year, 3, 31).date()
    else:
        if today.month > 4:
            fy_start = datetime(today.year, 4, 1).date()
            fy_end = datetime(today.year + 1, 3, 31).date()
        else:
            fy_start = datetime(today.year - 1, 4, 1).date()
            fy_end = datetime(today.year, 3, 31).date()

    filters = {'pi_date__gte': fy_start, 'pi_date__lte': fy_end}

    if selected_user:
        filters['user_id'] = selected_user

    if selected_ap:
        filters['is_Approved'] = selected_ap

    if selected_status:
        filters['status'] = selected_status

    
    all_proforma = proforma.objects.filter(user_id__in = user_ids)

    all_proforma = all_proforma.filter(**filters).order_by( '-pi_date','-pi_no')

    if query:

        search_fields = [
        'company_name', 'gstin', 'state', 'country', 'requistioner','email_id', 'contact', 'status',
        'pi_no', 'orderlist__product', 'orderlist__report_type'
        ]

        search_objects = Q()

        for field in search_fields:
            search_objects |= Q(**{f'{field}__icontains': query})

        all_proforma = all_proforma.filter(search_objects).distinct()

    
    paginator = Paginator(all_proforma.values_list('id', flat=True), page_size)

    try:
        page_ids = list(paginator.page(page_number))
    except:
        page_ids = list(paginator.page(1))

    return page_ids


@shared_task
def pi_count(user_ids, selected_fy, selected_user, selected_ap, selected_status, query):
    
    today = datetime.now().date()

    if selected_fy:
        start_year = int(selected_fy.split('-')[0])
        end_year = start_year+1

        fy_start = datetime(start_year, 4, 1).date()
        fy_end = datetime(end_year, 3, 31).date()
    else:
        if today.month > 4:
            fy_start = datetime(today.year, 4, 1).date()
            fy_end = datetime(today.year + 1, 3, 31).date()
        else:
            fy_start = datetime(today.year - 1, 4, 1).date()
            fy_end = datetime(today.year, 3, 31).date()

    filters = {'pi_date__gte': fy_start, 'pi_date__lte': fy_end}

    if selected_user:
        filters['user_id'] = selected_user

    if selected_ap:
        filters['is_Approved'] = selected_ap

    if selected_status:
        filters['status'] = selected_status

    
    all_proforma = proforma.objects.filter(user_id__in = user_ids)

    all_proforma = all_proforma.filter(**filters).order_by( '-pi_date','-pi_no')

    if query:

        search_fields = [
        'company_name', 'gstin', 'state', 'country', 'requistioner','email_id', 'contact', 'status',
        'pi_no', 'orderlist__product', 'orderlist__report_type'
        ]

        search_objects = Q()

        for field in search_fields:
            search_objects |= Q(**{f'{field}__icontains': query})

        all_proforma = all_proforma.filter(search_objects).distinct()

    
    return all_proforma.count()