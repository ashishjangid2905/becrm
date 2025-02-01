from celery import shared_task
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404


from .models import leads, contactPerson, Conversation, conversationDetails
from teams.models import User, Profile
from invoice.utils import STATUS_CHOICES, STATE_CHOICE, COUNTRY_CHOICE, PAYMENT_STATUS

@shared_task
def process_leads(query, user_id, selected_user, page_size, page_number):
    
    profile_instance = get_object_or_404(Profile, user=user_id)
    user_branch = profile_instance.branch
    all_users = Profile.objects.filter(branch=user_branch, user__department="sales")

    users_ids = [user.user.id for user in all_users]

    all_leads = leads.objects.filter(user__in = users_ids).order_by('-id')

    state_mapping = {value: key for key, value in STATE_CHOICE}
    country_mapping = {value: key for key, value in COUNTRY_CHOICE}

    if query:
        search_fields = [
            'company_name', 'gstin', 'city', 'industry', 'source', 'contactperson__person_name','contactperson__email_id',
            'contactperson__contact_no', 'conversation__title', 'conversation__conversationdetails__details'
        ]

        search_objects = Q()

        for field in search_fields:
            search_objects |= Q(**{f'{field}__icontains': query})

        if query.upper() in state_mapping:
            search_objects |= Q(state=state_mapping[query.upper()])
        if query.capitalize() in country_mapping:
            search_objects |= Q(country=country_mapping[query.capitalize()])

        all_leads = all_leads.filter(search_objects).distinct()


    if selected_user:
        all_leads = all_leads.filter(user=selected_user)

    if profile_instance.user.role != 'admin':
        all_leads = all_leads.filter(user=user_id)

    leads_per_page = Paginator(all_leads, page_size)
    try:
        all_leads_page = leads_per_page.get_page(page_number)
    except PageNotAnInteger:
        all_leads_page = leads_per_page.get_page(1)
    except EmptyPage:
        all_leads_page = leads_per_page.get_page(leads_per_page.num_pages)

    return [lead.id for lead in all_leads_page]


@shared_task
def total_leads(query, user_id, selected_user):
    profile_instance = get_object_or_404(Profile, user=user_id)
    user_branch = profile_instance.branch
    all_users = Profile.objects.filter(branch=user_branch, user__department="sales")

    users_ids = [user.user.id for user in all_users]

    all_leads = leads.objects.filter(user__in = users_ids).order_by('-id')

    state_mapping = {value: key for key, value in STATE_CHOICE}
    country_mapping = {value: key for key, value in COUNTRY_CHOICE}

    if query:
        search_fields = [
            'company_name', 'gstin', 'city', 'industry', 'source', 'contactperson__person_name','contactperson__email_id',
            'contactperson__contact_no', 'conversation__title', 'conversation__conversationdetails__details'
        ]

        search_objects = Q()

        for field in search_fields:
            search_objects |= Q(**{f'{field}__icontains': query})

        if query.upper() in state_mapping:
            search_objects |= Q(state=state_mapping[query.upper()])
        if query.capitalize() in country_mapping:
            search_objects |= Q(country=country_mapping[query.capitalize()])

        all_leads = all_leads.filter(search_objects).distinct()


    if selected_user:
        all_leads = all_leads.filter(user=selected_user)

    if profile_instance.user.role != 'admin':
        all_leads = all_leads.filter(user=user_id)

    return all_leads.count()