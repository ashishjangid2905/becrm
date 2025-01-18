# Import from Django
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect, FileResponse
from django.db.models import OuterRef, Subquery, Max, F, Q
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

# Import from  app models, utils
from .models import leads, contactPerson, Conversation, conversationDetails
from teams.models import User, Profile
from invoice.models import proforma, orderList
from invoice.utils import STATUS_CHOICES, STATE_CHOICE, COUNTRY_CHOICE
from teams.templatetags.teams_custom_filters import get_current_position

# Import Third Party Module
import csv, os
from datetime import date
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
import logging
# Create your views here.

@login_required(login_url='app:login')
def leads_list(request):

    if not request.user.is_authenticated:
        return redirect('app:login')
    
    query = request.GET.get('q')
    user_id = request.user.id

    profile_instance = get_object_or_404(Profile, user=request.user)
    user_branch = profile_instance.branch
    all_users = Profile.objects.filter(user__profile__branch=user_branch.id, user__department="sales")

    search_fields = [
        'company_name', 'gstin', 'city', 'state', 'country', 
        'industry', 'source', 'contactperson__person_name','contactperson__email_id', 'contactperson__contact_no',
        'conversation__title', 'conversation__conversationdetails__details'
    ]

    search_objects = Q()

    if query:
        # Fetch user IDs based on first name matching
        matching_user_ids = User.objects.filter(first_name__icontains=query).values_list('id', flat=True)
        
        # Build the Q object for searching leads
        for field in search_fields:
            search_objects |= Q(**{f'{field}__icontains': query})

        # Add matching user IDs to the Q object
        for user_id in matching_user_ids:
            search_objects |= Q(user__exact=user_id)

    all_leads = leads.objects.all().order_by('-id')


    if query:
        all_lead = all_leads.filter(search_objects).distinct()
    else:
        all_lead = all_leads

    selected_user = request.GET.get('user')

    if selected_user:
        all_lead = all_lead.filter(user=selected_user)

    if request.user.role == 'admin':
        user_leads = all_lead
    else:
        user_leads = all_lead.filter(user=request.user.id)

    if user_leads:
        for lead in user_leads:
            lead.user = User.objects.get(pk=lead.user)

    if request.GET.get('excel') == 'excel':
        return exportlead(user_leads)

    pageSize = request.GET.get('pageSize', 20)

    leads_per_page = Paginator(user_leads, pageSize)
    page = request.GET.get('page')

    try:
        user_leads = leads_per_page.get_page(page)
    except PageNotAnInteger:
        user_leads = leads_per_page.get_page(1)
    except EmptyPage:
        user_leads = leads_per_page.get_page(leads_per_page.num_pages)

    source_choice = leads.SOURCE
    states = STATE_CHOICE
    countries = COUNTRY_CHOICE

    context = {
        'user_leads': user_leads,
        'user_id': user_id,
        'source_choice': source_choice,
        'states': states,
        'countries': countries,
        'all_users':all_users,
        'pageSize': pageSize,
        'selected_user': selected_user,
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

    Q = request.GET.get('chat')

    chats = conversationDetails.objects.all().order_by('-inserted_at')

    if Q:
        try:
            chat_title = Conversation.objects.get(pk=Q)
            chat_details = chats.filter(chat_no=Q)
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

    if not request.user.is_authenticated:
        return redirect('app:login')
    
    user_id = request.user.id

    # allFollowups = conversationDetails.objects.filter(chat_no = OuterRef('chat_no')).values('chat_no').annotate(latest_follow_up=Max('follow_up')).values('latest_follow_up')
    
    # latest_conversation_details = conversationDetails.objects.filter(follow_up__in=allFollowups).order_by('chat_no','-follow_up', '-inserted_at')

    if request.user.role == 'admin':
        allchat = conversationDetails.objects.all()
    else:
        allchat = conversationDetails.objects.filter(chat_no__company_id__user = user_id)

    # Subquery to get the latest inserted_at for each chat
    latest_inserted_at = allchat.values('chat_no').annotate(max_inserted_at=Max('inserted_at'))

    # Query to get the latest entry for each chat
    latest_conversation_details = allchat.filter(
        inserted_at__in=Subquery(
            latest_inserted_at.values('max_inserted_at')
        )
    )

    today = date.today()

    Filter = request.GET.get('filter')

    if Filter == 'today' :
        latest_conversation_details = latest_conversation_details.filter(follow_up=today)
    elif Filter == 'previous':
        latest_conversation_details = latest_conversation_details.filter(follow_up__lt=today)
    elif Filter == 'future':
        latest_conversation_details = latest_conversation_details.filter(follow_up__gt=today)
    else:
        latest_conversation_details = latest_conversation_details.filter(follow_up=today)
        
    if latest_conversation_details:
        for lead in latest_conversation_details:
            lead.chat_no.company_id.user = User.objects.get(pk=lead.chat_no.company_id.user)

    context = {
        'latest_conversation_details':latest_conversation_details,
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