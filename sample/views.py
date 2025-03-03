
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib import messages, auth
from django.template import loader

from sample.models import sample, Portmaster, sample_no, CountryMaster
from teams.models import Profile
from django.db.models import Q
import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .serializers import SampleSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import generics
from rest_framework.permissions import IsAuthenticated


class SampleViews(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SampleSerializer

    def get_queryset(self):
        user_profile = Profile.objects.get(user = self.request.user)
        return sample.objects.filter(user__profile__branch=user_profile.branch).select_related("user").order_by('-requested_at')
    


@login_required(login_url='app:login')
def sample_request(request):

    if not request.user.is_authenticated:
        return redirect('app:login')
    
    if request.method == 'POST':
        user = request.user
        sample_id = sample_no(user)
        country = request.POST.get('inputCountry')
        report_format = request.POST.get('formatReport')
        report_type = request.POST.get('typeReport')
        hs_code = request.POST.get('inputHSN','%')
        product = request.POST.get('inputProduct', '%')
        iec = request.POST.get('inputIEC', '%')
        shipper = request.POST.get('inputShiper', '%')
        consignee = request.POST.get('inputForeign', '%')
        foreign_country = request.POST.getlist('inputForeignCountry', '%')
        port = request.POST.getlist('inputPort', '%')
        month = request.POST.get('month')
        year = request.POST.get('inputyear')
        client_name = request.POST.get('inputClient')
        status = request.POST.get('sampleStatus', 'pending')

        ports = ', '.join(port)
        countries = ', '.join(foreign_country)

        Sample = sample.objects.create(user=user, sample_id =sample_id,country=country,report_format=report_format,report_type=report_type,hs_code=hs_code,product=product,iec=iec,shipper=shipper,consignee=consignee,foreign_country=countries,port=ports,month=month,year=year,client_name=client_name,status=status)
        messages.success(request, "Sample has been requested")
        return redirect('sample:samples')
    return redirect('sample:samples')

    
@login_required(login_url='app:login')
def sample_list(request):
    if not request.user.is_authenticated:
        return redirect('app:login')
    
    format_choices = sample.FORMAT
    type_choices = sample.TYPE
    month_choices = sample.MONTH
    status_choices = sample.STATUS
    port_choice = Portmaster.objects.all()
    country_choice = CountryMaster.objects.all()

    start_year = datetime.datetime.now().year - 5
    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month

    range_year = range(current_year, start_year - 1, -1)  # Reverse range

    selected_year = request.POST.get('inputyear')

    if selected_year == current_year:
        month_choices = month_choices[:current_month]
    else:
        month_choices = month_choices
    
    query = request.GET.get('q')

    # Define the fields want to search across
    search_fields = ['user__first_name','user__email','hs_code', 'report_type','product', 'shipper', 'consignee', 'foreign_country', 'client_name', 'status']

    # Create a Q object to search across all specified fields
    search_objects = Q()

    for field in search_fields:
        search_objects |= Q(**{f'{field}__icontains': query})

    user_profile = Profile.objects.get(user=request.user)
    user_branch = user_profile.branch

    all_samples = sample.objects.filter(user__profile__branch=user_branch.id).order_by('-requested_at')

    if query:
        filtered_samples = all_samples.filter(search_objects).order_by('-requested_at')  # Define all_samples outside of the if statement
    else:
        filtered_samples = all_samples
    if request.user.role == 'admin':
        user_samples = filtered_samples  # Use all_samples directly for all users
    else:
        if request.user.department == 'production':
            user_samples = filtered_samples  # Use all_samples directly for production users
        else:
            user_samples = filtered_samples # not Filter all_samples for non-production users


    # pagination of sample list
        
    paginator = Paginator(user_samples, 20)  # Show 10 samples per page
    page = request.GET.get('page')

    try:
        user_samples = paginator.get_page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        user_samples = paginator.get_page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        user_samples = paginator.get_page(paginator.num_pages)

    context = {
        'all_samples': all_samples,
        'user_samples': user_samples,
        'filtered_samples': filtered_samples,
        'user_branch':user_branch,
        'user_profile':user_profile,
        'format_choices': format_choices,
        'type_choices': type_choices,
        'month_choices': month_choices,
        'status_choices': status_choices,
        'range_year': range_year,
        'selected_year': selected_year,
        'port_choice': port_choice,
        'country_choice': country_choice,
    }


    return render(request, 'sample/sample-list.html', context)

@login_required(login_url='app:login')
def edit_sample(request, sample_slug):
    sample_instance = get_object_or_404(sample, slug=sample_slug)
    

    if not request.user.is_authenticated:
        return redirect('app:login')
    
    if sample_instance.user == request.user and sample_instance.status != 'received':
        if request.method == 'POST':
            user = request.user
            country = request.POST.get('inputCountry')
            report_format = request.POST.get('formatReport')
            report_type = request.POST.get('typeReport')
            hs_code = request.POST.get('inputHSN','%')
            product = request.POST.get('inputProduct', '%')
            iec = request.POST.get('inputIEC', '%')
            shipper = request.POST.get('inputShiper', '%')
            consignee = request.POST.get('inputForeign', '%')
            foreign_country = request.POST.getlist('inputForeignCountry', '%')
            port = request.POST.getlist('inputPort', '%')
            month = request.POST.get('month')
            year = request.POST.get('inputyear')
            client_name = request.POST.get('inputClient')
            status = request.POST.get('sampleStatus')

            ports = ', '.join(port)
            countries = ', '.join(foreign_country)

            # Update the sample object with the new data
            sample_instance.country = country
            sample_instance.report_format = report_format
            sample_instance.report_type = report_type
            sample_instance.hs_code = hs_code
            sample_instance.product = product
            sample_instance.iec = iec
            sample_instance.shipper = shipper
            sample_instance.consignee = consignee
            sample_instance.foreign_country = countries
            sample_instance.port = ports
            sample_instance.month = month
            sample_instance.year = year
            sample_instance.client_name = client_name
            sample_instance.status = status
            sample_instance.save()

            messages.success(request, "Sample request has benn updated successfully")
            return redirect('sample:samples')
    return redirect('sample:samples')
