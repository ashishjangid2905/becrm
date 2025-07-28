import calendar
from celery import shared_task
from django.utils.timezone import now
from django.db.models import Count, Q, Min, Max
from datetime import datetime

from teams.models import Profile, Branch, User, UserVariable
from teams.templatetags.teams_custom_filters import get_current_position, get_current_target
from invoice.models import proforma, orderList
from invoice.templatetags.custom_filters import total_order_value, sale_category


@shared_task
def dashboard_data(user_id, selected_fy, selected_user, selected_month):
    today = now().date()

    date_range = proforma.objects.aggregate(min_date=Min('pi_date'), max_date=Max('pi_date'))
    min_year = date_range['min_date'].year if date_range['min_date'] else today.year
    max_year = date_range['max_date'].year if date_range['max_date'] else today.year

    if selected_fy:
        fy_start_year = int(selected_fy.split('-')[0])
        fy_start = datetime(fy_start_year, 4, 1).date()
        fy_end = datetime(fy_start_year + 1, 3, 31).date()
    else:
        fy_start = datetime(today.year - 1, 4, 1).date() if today.month < 4 else datetime(today.year, 4, 1).date()
        fy_end = datetime(fy_start.year + 1, 3, 31).date()

    user_profile = Profile.objects.get(user=user_id)
    user_branch = user_profile.branch

    all_users = Profile.objects.filter(branch=user_branch)

    current_position = get_current_position(user_profile)
    user_role = user_profile.user.role
    if current_position != 'Head' and user_role != 'admin':
        all_users = all_users.exclude(user__groups__name__in=['Head'])

    user_ids = list(all_users.values_list('user__id', flat=True))

    filters = {'user_id__in': user_ids, 'pi_date__range': (fy_start, fy_end)}

    if selected_user:
        filters['user_id'] = selected_user

    if selected_month:
        year, month = map(int, selected_month.split("-"))
        start_date = datetime(year, month, 1).date()
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day).date()
        filters['closed_at__range'] = (start_date, end_date)

    all_proforma = proforma.objects.filter(**filters).select_related('bank', 'bank__biller_id').prefetch_related('orderlist_set')

    if all_proforma:
        for pi in all_proforma:
            pi.user_id = Profile.objects.get(user = pi.user_id)

    order_items = orderList.objects.filter(proforma_id__in=[pi.id for pi in all_proforma])
    orders_map = {pi.id: [] for pi in all_proforma}

    for order in order_items:
        orders_map[order.proforma_id.id].append(order)

    pi_list = []
    for pi in all_proforma:
        pi_data = {
            'pi_date': pi.pi_date,
            'pi_no': pi.pi_no,
            'pi_status': pi.status,
            'pi_user': pi.user_id.id,
            'team_member': pi.user_id.user.full_name(),
            'biller': pi.bank.biller_id.biller_name,
            'bank': pi.bank.bank_name,
            'closed_at': pi.closed_at,
            'totalValue': total_order_value(pi.id),
            'sales_category': sale_category(pi.id),
            'order_list': [
                {
                'category': order.category,
                'report_type': order.report_type,
                'product': order.product,
                'is_lumpsum': order.is_lumpsum,
                'total_price': order.total_price,
                'lumpsum': order.lumpsum_amt
                }
                for order in orders_map[pi.id]
            ]
        }

        pi_list.append(pi_data)

    return pi_list
    

