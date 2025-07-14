# Import from Django
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect, FileResponse
from django.db.models import OuterRef, Subquery, Max, F, Q
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction, IntegrityError

# Import from  app models, utils
from .models import leads, contactPerson, Conversation, conversationDetails
from teams.models import User, Profile
from invoice.models import proforma, orderList
from invoice.utils import STATUS_CHOICES, STATE_CHOICE, COUNTRY_CHOICE, PAYMENT_STATUS
from teams.templatetags.teams_custom_filters import get_current_position

# Import Third Party Module
import csv, os, math
from datetime import date
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
import logging
from django.utils.timezone import now
from .tasks import process_leads, total_leads
# Create your views here.

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import FilterSet


class BasePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class LeadsFilters(FilterSet):
    class Meta:
        model = leads
        fields = ['company_name', 'gstin', 'full_address', 'industry']


class lead_list(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = BasePagination
    search_fields = ['company_name', 'gstin', 'full_address', 'industry']
    ordering_fields = ['company_name', 'gstin', 'full_address', 'industry', 'user_name', 'created_at']
    ordering = ['-created_at']

    def get(self, request):
        try:
            all_leads = leads.objects.filter(user=request.user.id).prefetch_related("contactpersons")
            search_query = request.GET.get('search', None)
            if search_query:
                search_filter = SearchFilter()
                all_leads = search_filter.filter_queryset(request, all_leads, self)

            filtered_leads = LeadsFilters(request.GET, queryset=all_leads)
            if filtered_leads.is_valid():
                all_leads = filtered_leads.qs

            ordering_query = request.GET.get('ordering', None)
            if ordering_query:
                ordering_filter = OrderingFilter()
                all_leads = ordering_filter.filter_queryset(request, all_leads, self)

            paginator = self.pagination_class()
            paginated_leads = paginator.paginate_queryset(all_leads, request)
            serializer = leadsSerializer(paginated_leads, many = True)
            return paginator.get_paginated_response(serializer.data)
        except leads.DoesNotExist:
            return Response({"message": "No Lead founded"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        serializer = leadsSerializer(data = request.data)
        user_id = request.user.id

        if serializer.is_valid():
            company_name = request.data.get('company_name')
            gstin = request.data.get('gstin')

            if leads.objects.filter(company_name=company_name, gstin=gstin, user=user_id).exists():
                return Response({'error': f'The Company {company_name} already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            lead_instance = serializer.save(user = user_id)

            contactpersons_data = request.data.get('contactpersons', [])
            lead = get_object_or_404(leads, pk=lead_instance.id)

            contact_persons = [contactPerson(company = lead, **contact) for contact in contactpersons_data]

            if contact_persons:
                contactPerson.objects.bulk_create(contact_persons)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LeadListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            all_leads = leads.objects.filter(user=request.user.id).prefetch_related("contactpersons").order_by("company_name")

            serializer = leadsSerializer(all_leads, many = True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except leads.DoesNotExist:
            return Response({"message": "No Lead founded"}, status=status.HTTP_404_NOT_FOUND)

class LeadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            lead = get_object_or_404(leads, pk=id)
            serializer = leadsSerializer(lead)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def patch(self, request, id):
        try:
            instance = get_object_or_404(leads, pk=id)
            data = request.data
            serializer = leadsSerializer(instance, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ContactView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            leadInstance = get_object_or_404(leads, id=id)
            data = request.data
            company_id = data.pop("company")
            print(data)
            serializer = contactPersonSerializer(data=data)
            if serializer.is_valid():
                serializer.save(company = leadInstance)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def patch(self, request, lead_id ,id):
        try:
            instance = get_object_or_404(contactPerson, id=id)
            data = request.data
            data.pop("id")
            serializer = contactPersonSerializer(instance, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error":str(e)}, status=status.HTTP_400_BAD_REQUEST)




class ConversationView(APIView):
    permission_classes = [IsAuthenticated]

    # get conversation object
    def get_object(self, id):
        return get_object_or_404(Conversation, id=id)

    # fetch conversation list with respect to lead
    def get(self, request, id):
        try:
            conversation = Conversation.objects.filter(company_id = id).select_related("company_id").order_by("-start_at")
            serializer = ConversationSerializer(conversation, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Conversation.DoesNotExist:
            return Response({"message": "No Conversation found for this Company"}, status=status.HTTP_404_NOT_FOUND)
        
    # Create/Start New Conversation
    def post(self, request, id):
        try:
            data = request.data.copy()
            title = data.get("title")
            company_id = data.get("company")
            if not title or not company_id:
                return Response({"error": "Missing 'title' or 'company' in request data"}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                deal_data = {
                    "title": title,
                    "company_id": company_id
                }
                dealSerializer = ConversationSerializer(data=deal_data)
                if not dealSerializer.is_valid():
                    raise IntegrityError(dealSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
                deal = dealSerializer.save()
                
                serializer = ConversationDetailsSerializer(data=data)
                if not serializer.is_valid():
                    raise IntegrityError(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
                serializer.save(chat_no = deal)
                return Response(dealSerializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as ie:
            return Response({'error': str(ie)}, status=status.HTTP_400_BAD_REQUEST)


        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        


class dealActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, id):
        return get_object_or_404(Conversation, id=id)
    
    def get(self, request, id):
        try:
            deal = self.get_object(id)

            activities = conversationDetails.objects.filter(chat_no=deal).select_related('chat_no')
            if activities:
                serializer = ConversationDetailsSerializer(activities, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, id):
        try:
            deal = self.get_object(id)
            # print(deal)
            data = request.data
            chat_no = data.pop("chat_no")
            if data.get("follow_up") == "":
                data["follow_up"] = None
            
            print(data)

            serializer = ConversationDetailsSerializer(data=data)

            if serializer.is_valid():
                serializer.save(chat_no=deal)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



@login_required(login_url='app:login')
def leads_list(request):
    
    query = request.GET.get('q')
    user_id = request.user.id
    selected_user = request.GET.get('user')
    page_size = int(request.GET.get('pageSize', 20))
    page_number = request.GET.get('page', 1)

    task = process_leads.apply_async(args=[query, user_id, selected_user, page_size, page_number])

    task_id = task.id

    leads_result = task.get(timeout=30)

    all_leads = leads.objects.filter(id__in=leads_result).order_by('-created_at')

    for lead in all_leads:
        lead.user = User.objects.get(pk=lead.user)

    profile_instance = get_object_or_404(Profile, user=request.user)
    user_branch = profile_instance.branch
    all_users = Profile.objects.filter(branch=user_branch.id, user__department="sales")
    source_choice = leads.SOURCE
    states = STATE_CHOICE
    countries = COUNTRY_CHOICE

    task2 = total_leads.apply_async(args=[query, user_id, selected_user])
    task2_id = task2.id
    
    lead_r = task2.get(timeout=30)

    total_page = math.ceil(lead_r/page_size)
    min_page = int(page_number) - 2 if int(page_number)>2 else 1
    max_page = int(page_number) + 2 if total_page >= int(page_number)+2 else total_page
    pages = [page for page in range(min_page, max_page+1)]

    context = {
        'user_leads': all_leads,
        'user_id': user_id,
        'source_choice': source_choice,
        'states': states,
        'countries': countries,
        'all_users':all_users,
        'pageSize': page_size,
        'selected_user': selected_user,
        'lead_count': lead_r,
        'page_number': int(page_number),
        'page_range': pages,
        'total_page': total_page,
    }
    
    return render(request, 'lead/lead-list.html', context)

@login_required(login_url='app:login')
def add_lead(request):

    if not request.user.is_authenticated:
        return redirect('app:login')
    
    source_choice = leads.SOURCE

    context = {
        'source_choice': source_choice,
    }

    if request.method == 'POST':
        user = request.user.id
        company_name = request.POST.get("company_name")
        gstin = request.POST.get("gstin")
        address1 = request.POST.get("address1")
        address2 = request.POST.get("address2")
        city = request.POST.get("city")
        state = request.POST.get("state")
        country = request.POST.get("country")
        pincode = request.POST.get("pincode")
        industry = request.POST.get("industry")
        source = request.POST.get("source")

        if leads.objects.filter(company_name = company_name, gstin=gstin, user=user).exists():
            messages.error(request, f"The company '{company_name}' already exists.")
            return redirect('lead:leads_list')
        
        company = leads.objects.create(company_name=company_name, gstin=gstin, address1=address1, address2=address2, city=city, state=state, country=country, pincode=pincode, industry=industry, source=source, user=user)

        person_name = request.POST.get("contact_person")
        email_id = request.POST.get("email")
        contact_no = request.POST.get("contact_no")
        is_active = request.POST.get("is_active") == "on"

        Contact_person = contactPerson.objects.create(person_name=person_name, email_id=email_id, contact_no=contact_no, is_active=is_active,company=company)
        
        print(request.POST.get('action'))
        if request.POST.get('action') == 'Add & Create_PI':
            company_id = company.id
            target_url = reverse('invoice:create_pi_lead_id', args=[company_id])
            return HttpResponseRedirect(target_url)
        return redirect(reverse('lead:lead', kwargs={'leads_id': company.id}))

    return redirect('lead:leads_list')

@login_required(login_url='app:login')
def edit_lead(request, leads_id):

    if not request.user.is_authenticated:
        return redirect('app:login')
    
    source_choice = leads.SOURCE
    lead_instance = leads.objects.get(pk=leads_id)

    context = {
        'source_choice': source_choice,
        'lead_instance': lead_instance,
    }


    if lead_instance.user == request.user.id:
        if request.method == 'POST':
            user = request.user.id
            company_name = request.POST.get("company_name")
            gstin = request.POST.get("gstin")
            address1 = request.POST.get("address1")
            address2 = request.POST.get("address2")
            city = request.POST.get("city")
            state = request.POST.get("state")
            country = request.POST.get("country")
            pincode = request.POST.get("pincode")
            industry = request.POST.get("industry")
            source = request.POST.get("source")

            lead_instance.company_name = company_name
            lead_instance.gstin = gstin
            lead_instance.address1 = address1
            lead_instance.address2 = address2
            lead_instance.city = city
            lead_instance.state = state
            lead_instance.country = country
            lead_instance.pincode = pincode
            lead_instance.industry = industry
            lead_instance.source = source
            lead_instance.save()

            return redirect(reverse('lead:lead', args=[leads_id]))

    return redirect(reverse('lead:lead', args=[leads_id]))


@login_required(login_url='app:login')
def lead(request, leads_id):

    if not request.user.is_authenticated:
        return redirect('app:login')
    
    profile_instance = get_object_or_404(Profile, user = request.user)
    current_position = get_current_position(profile_instance)
    user_role = request.user.role
    
    company = leads.objects.get(pk=leads_id)

    contact_person = contactPerson.objects.filter(company=leads_id).order_by('-is_active')

    all_pi = proforma.objects.filter(company_ref = company)

    if all_pi:
        for pi in all_pi:
            if pi.approved_by:
                pi.approved_by = get_object_or_404(User, pk=pi.approved_by)

    status_choices = STATUS_CHOICES
    payment_status = PAYMENT_STATUS
    states = STATE_CHOICE
    countries = COUNTRY_CHOICE
    source_choice = leads.SOURCE
    company.source = dict(source_choice).get(company.source) if company.state else None
    try:
        company.state = int(company.state) if company.state else None
    except:
        pass


    query = request.GET.get('q')

    search_fields = [
        'company_name', 'gstin', 'state', 'country', 'requistioner','email_id', 'contact',
        'pi_no', 'orderlist__product'
    ]

    search_objects = Q()

    if query:
        # matching_user_ids = User.objects.filter(first_name__icontains=query).values_list('id', flat=True)
        
        # Build the Q object for searching leads
        for field in search_fields:
            search_objects |= Q(**{f'{field}__icontains': query})

        # Add matching user IDs to the Q object
        # for user_id in matching_user_ids:
        #     search_objects |= Q(user__exact=user_id)

        piList = all_pi.filter(search_objects).distinct()
    else:
        piList = all_pi

    context={
        'company': company,
        'contact_person': contact_person,
        'piList': piList,
        'status_choices': status_choices,
        'source_choice':source_choice,
        'payment_status': payment_status,
        'states': states,
        'countries': countries,
        'current_position': current_position,
        'user_role': user_role
    }

    return render(request, 'lead/pi-list.html', context)


@login_required(login_url='app:login')
def lead_chat(request, leads_id):

    if not request.user.is_authenticated:
        return redirect('app:login')
    
    company = leads.objects.get(pk=leads_id)

    contact_person = contactPerson.objects.filter(company=leads_id).order_by('-is_active')

    chat_titles = Conversation.objects.filter(company_id=leads_id).order_by('-start_at')

    status_choice = conversationDetails.STATUS
    states = STATE_CHOICE
    countries = COUNTRY_CHOICE
    source_choice = leads.SOURCE

    q = request.GET.get('chat')

    chats = conversationDetails.objects.filter(chat_no__company_id = leads_id).order_by('-inserted_at')

    if q:
        try:
            chat_title = Conversation.objects.get(pk=q, company_id = leads_id)
            chat_details = chats.filter(chat_no=q)
        except Conversation.DoesNotExist:
            return HttpResponseRedirect(request.path_info)
    else:
        chat_title = Conversation.objects.filter(company_id=leads_id).last()
        chat_details = chats.filter(chat_no=chat_title)

    context={
        'company': company,
        'contact_person': contact_person,
        'chat_titles': chat_titles,
        'chat_title': chat_title,
        'chat_details': chat_details,
        'status_choice':status_choice,
        'source_choice':source_choice,
        'states': states,
        'countries': countries
    }

    return render(request, 'lead/chat-details.html', context)


@login_required(login_url='app:login')
def add_contact(request, leads_id):
    if not request.user.is_authenticated:
        return redirect('app:login')  
    
    target_url = reverse("lead:leads_pi", args=[leads_id])

    if request.method == 'POST':
        company = leads.objects.get(pk=leads_id)
        person_name = request.POST.get("contact_person")
        email_id = request.POST.get("email")
        contact_no = request.POST.get("contact_no")
        is_active = request.POST.get("is_active") == "on"

        Contact_person = contactPerson.objects.create(person_name=person_name, email_id=email_id, contact_no=contact_no, is_active=is_active, company=company)
    
    return HttpResponseRedirect(target_url)

@login_required(login_url='app:login')
def edit_contact(request, contact_id):
    if not request.user.is_authenticated:
        return redirect('app:login')

    person_instance = get_object_or_404(contactPerson, pk=contact_id)
    target_url = reverse("lead:leads_pi", args=[person_instance.company.id])

    if request.method == 'POST':
        person_instance.person_name = request.POST.get("contact_person")
        person_instance.email_id = request.POST.get("email")
        person_instance.contact_no = request.POST.get("contact_no")
        person_instance.is_active = request.POST.get("is_active") == "on"
        person_instance.save()

    return HttpResponseRedirect(target_url)

@login_required(login_url='app:login')
def new_chat(request, leads_id):

    if not request.user.is_authenticated:
        return redirect('app:login')
    
    target_url = reverse("lead:leads_chat", args=[leads_id])
    if request.method == 'POST':
        company_id = leads.objects.get(pk=leads_id)
        title = request.POST.get("chat_title")
        chat = Conversation.objects.create(title=title,company_id=company_id)
        details = request.POST.get("feeds")
        contact_person_id = request.POST.get("contactPerson")
        contact_person = contactPerson.objects.get(pk=contact_person_id)
        status = request.POST.get("status")
        follow_up = request.POST.get("follow_up")
        if follow_up == "":
            follow_up = None
        conversation = conversationDetails.objects.create(details=details, chat_no=chat, contact_person=contact_person, status=status, follow_up=follow_up)

        return HttpResponseRedirect(target_url + "?chat=" + str(chat.id))
    return HttpResponseRedirect(target_url)

@login_required(login_url='app:login')
def chat_insert(request, chat_id):
    chat_title = get_object_or_404(Conversation, pk=chat_id)


    target_url = reverse("lead:leads_chat", args=[chat_title.company_id.id])

    if chat_title.company_id.user == request.user.id and request.method == 'POST':
        details = request.POST.get("feeds")
        contact_person_id = request.POST.get("contactPerson")
        status = request.POST.get("status")
        follow_up = request.POST.get("follow_up")
        contact_person = get_object_or_404(contactPerson, pk=contact_person_id)
        if follow_up == "":
            follow_up = None
        feedDetail = conversationDetails.objects.create(chat_no=chat_title, details=details, contact_person=contact_person, status=status, follow_up=follow_up)
        
    return HttpResponseRedirect(target_url + "?chat=" + str(chat_id) )

@login_required(login_url='app:login')
def follow_ups(request):

    user_id = request.user.id

    profile_instance = get_object_or_404(Profile, user=request.user)
    user_branch = profile_instance.branch.id
    all_users = Profile.objects.filter(branch=user_branch)

    users_ids = [user.user.id for user in all_users]


    if request.user.role == 'admin':
        leads_ids = leads.objects.filter(user__in = users_ids).values_list('id', flat=True)
    else:
        leads_ids = leads.objects.filter(user = user_id).values_list('id', flat=True)
    
    conversations_ids = Conversation.objects.filter(company_id__in = leads_ids).values_list('id', flat=True)

    allchat = conversationDetails.objects.filter(chat_no__in = conversations_ids).select_related('chat_no__company_id', 'contact_person')

    latest_inserted = allchat.values('chat_no').annotate(latest_insert = Max('inserted_at'))

    allchat = allchat.filter(inserted_at__in = Subquery(latest_inserted.values('latest_insert')))

    today = now().date()

    filter_value  = request.GET.get('filter', 'today')


    if filter_value  == 'today' :
        filtered_conversations  = allchat.filter(follow_up=today)
    elif filter_value  == 'previous':
        filtered_conversations  = allchat.filter(follow_up__lt=today)
    elif filter_value  == 'future':
        filtered_conversations  = allchat.filter(follow_up__gt=today)
    else:
        filtered_conversations  = allchat.filter(follow_up=today)
        
    if filtered_conversations:
        for lead in filtered_conversations:
            lead.chat_no.company_id.user = get_object_or_404(User,pk=lead.chat_no.company_id.user)

    context = {
        'latest_conversation_details':filtered_conversations ,
    }

    return render(request, 'lead/follow-up-list.html', context)


@login_required(login_url='app:login')
def upload_Leads(request):

    if not request.user.is_authenticated:
        return redirect('app:login')
    logger = logging.getLogger(__name__)
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        if uploaded_file.name.endswith('.csv'):
            try:
                decoded_file = uploaded_file.read().decode('utf-8').splitlines()
                csv_reader = csv.DictReader(decoded_file)
            except Exception as e:
                logger.error(f"Error reading file: {str(e)}")
                return HttpResponse(f"Error reading file: {e}")
            # Handle potential BOM (Byte Order Mark) in the first column name
            fieldnames = csv_reader.fieldnames
            if fieldnames[0].startswith('\ufeff'):
                fieldnames[0] = fieldnames[0].replace('\ufeff', '')

            # Ensure the CSV DictReader knows about the corrected fieldnames
            csv_reader.fieldnames = fieldnames

            for row in csv_reader:
                try:
                    # Check if lead already exists based on company name and GSTIN
                    lead_instance, created = leads.objects.update_or_create(
                        company_name=row['company_name'],
                        gstin=row['gstin'],
                        user= request.user.id,
                        defaults={
                            'address1': row['address1'],
                            'address2': row.get('address2', ''),
                            'city': row['city'],
                            'state': row['state'],
                            'country': row['country'],
                            'pincode': row.get('pincode', ''),
                            'industry': row.get('industry', ''),
                            'source': row['source'],
                        }
                    )

                    # Update or create contact person associated with the lead
                    contact_person_instance, contact_created = contactPerson.objects.update_or_create(
                        person_name=row['person_name'],
                        email_id=row.get('email_id', ''),
                        contact_no=row.get('contact_no', ''),
                        company=lead_instance,
                        defaults={
                            'is_active': row.get('is_active', 'TRUE').lower() == 'true'
                        }
                    )
                except Exception as e:
                    # Log the error or handle it
                    print(f"Error processing row: {row}. Error: {str(e)}")
                    continue  # Skip to the next row

            return redirect('lead:leads_list')
        else:
            return HttpResponse("Invalid file format")
        

@login_required(login_url='app:login')
def download_template(request):
    file_path = os.path.join(settings.BASE_DIR, 'static', 'becrm/template.csv')
    return FileResponse(open(file_path,'rb'), as_attachment=True, filename='template.csv')


def exportlead(all_lead):

    wb = Workbook()
    ws = wb.active
    ws.title = 'Leads'

    headers = [
        'Team Member','Company Name', 'GSTIN', 'Address', 'City', 'State', 'Country', 'Pincode',
        'Industry', 'Source', 'Contact Person Name', 'Email', 'Contact Number', 'Is Active'
    ]

    ws.append(headers)

    header_fill = PatternFill(fill_type='solid', start_color="0099CCFF", end_color="0099CCFF")
    header_font = Font(name='Calibri', size=11, bold=True, color="00000000")

    for col in range(1, len(headers)+1):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = header_font

    # Add data rows to the sheet
    for lead in all_lead:
        # Iterate over each contact person associated with the lead
        contact_person = contactPerson.objects.filter(company = lead)

        for contact_person in contact_person:
            user_name = User.objects.get(pk=contact_person.company.user).get_full_name()
            address = contact_person.company.get_full_address()
            row = [
                user_name, contact_person.company.company_name, contact_person.company.gstin, address, contact_person.company.city, contact_person.company.state,
                contact_person.company.country, contact_person.company.pincode, contact_person.company.industry, contact_person.company.source,
                contact_person.person_name, contact_person.email_id,
                contact_person.contact_no, contact_person.is_active
            ]
            ws.append(row)


    for column in ws.columns:
        max_length = 0
        column = list(column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass

        adjusted_width = (max_length+2)
        ws.column_dimensions[get_column_letter(column[0].column)].width = adjusted_width

    # Create a response object with MIME type for Excel files
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=leads.xlsx'

    # Save the workbook to the response object
    wb.save(response)

    return response