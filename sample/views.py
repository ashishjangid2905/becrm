
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib import messages, auth
from django.template import loader

from sample.models import sample
from django.db.models import Q
import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@login_required(login_url='app:login')
def sample_request(request):
    format_choices = sample.FORMAT
    type_choices = sample.TYPE
    month_choices = sample.MONTH
    status_choices = sample.STATUS

    start_year = datetime.datetime.now().year - 5
    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month

    range_year = range(current_year, start_year - 1, -1)  # Reverse range

    selected_year = request.POST.get('inputyear')

    if selected_year == current_year:
        month_choices = month_choices[:current_month]
    else:
        month_choices = month_choices

    context = {
        'format_choices': format_choices,
        'type_choices': type_choices,
        'month_choices': month_choices,
        'status_choices': status_choices,
        'range_year': range_year,
        'selected_year': selected_year
    }

    if request.user.is_authenticated:
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
            foreign_country = request.POST.get('inputForeignCountry', '%')
            port = request.POST.get('inputPort', '%')
            month = request.POST.get('month')
            year = request.POST.get('inputyear')
            client_name = request.POST.get('inputClient')
            status = request.POST.get('sampleStatus', 'pending')

            Sample = sample.objects.create(user=user,country=country,report_format=report_format,report_type=report_type,hs_code=hs_code,product=product,iec=iec,shipper=shipper,consignee=consignee,foreign_country=foreign_country,port=port,month=month,year=year,client_name=client_name,status=status)
            messages.success(request, "Sample Request Submited")
            return redirect('sample:samples')
        return render(request, 'sample/sample-request.html', context)
    else:
        return redirect('app:login')
    
@login_required(login_url='app:login')
def sample_list(request):
    if not request.user.is_authenticated:
        return redirect('app:login')
    
    query = request.GET.get('q')

    # Define the fields want to search across
    search_fields = ['user__email','hs_code', 'report_type','product', 'shipper', 'consignee', 'foreign_country', 'client_name', 'status']

    # Create a Q object to search across all specified fields
    search_objects = Q()

    for field in search_fields:
        search_objects |= Q(**{f'{field}__icontains': query})

    all_samples = sample.objects.all()

    if query:
        filtered_samples = sample.objects.filter(search_objects)  # Define all_samples outside of the if statement
    else:
        filtered_samples = all_samples
    if request.user.role == 'admin':
        user_samples = filtered_samples  # Use all_samples directly for all users
    else:
        if request.user.department == 'production':
            user_samples = filtered_samples  # Use all_samples directly for production users
        else:
            user_samples = filtered_samples  # not Filter all_samples for non-production users


    # pagination of sample list
        
    paginator = Paginator(user_samples, 10)  # Show 10 samples per page
    page = request.GET.get('page')

    try:
        user_samples = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        user_samples = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        user_samples = paginator.page(paginator.num_pages)

    context = {
        'all_samples': all_samples,
        'user_samples': user_samples,
        'filtered_samples': filtered_samples,
    }


    return render(request, 'sample/sample-list.html', context)

@login_required(login_url='app:login')
def edit_sample(request, sample_slug):
    sample_instance = get_object_or_404(sample, slug=sample_slug)
    format_choices = sample.FORMAT
    type_choices = sample.TYPE
    month_choices = sample.MONTH
    status_choices = sample.STATUS

    start_year = datetime.datetime.now().year - 5
    current_year = datetime.datetime.now().year
    range_year = range(current_year, start_year - 1, -1)  # Reverse range


    context = {
        'sample_instance': sample_instance,
        'format_choices': format_choices,
        'type_choices': type_choices,
        'month_choices': month_choices,
        'status_choices': status_choices,
        'range_year': range_year,
    }

    if request.user.is_authenticated:
        if sample_instance.user == request.user:
            if sample_instance.status != 'received':
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
                    foreign_country = request.POST.get('inputForeignCountry', '%')
                    port = request.POST.get('inputPort', '%')
                    month = request.POST.get('month')
                    year = request.POST.get('inputyear')
                    client_name = request.POST.get('inputClient')
                    status = request.POST.get('sampleStatus')

                    # Update the sample object with the new data
                    sample_instance.country = country
                    sample_instance.report_format = report_format
                    sample_instance.report_type = report_type
                    sample_instance.hs_code = hs_code
                    sample_instance.product = product
                    sample_instance.iec = iec
                    sample_instance.shipper = shipper
                    sample_instance.consignee = consignee
                    sample_instance.foreign_country = foreign_country
                    sample_instance.port = port
                    sample_instance.month = month
                    sample_instance.year = year
                    sample_instance.client_name = client_name
                    sample_instance.status = status
                    sample_instance.save()

                    messages.success(request, "Sample Update successfully")
                    return redirect('sample:samples')
                return render(request, 'sample/edit-sample.html', context)
            return redirect('sample:samples')
        return redirect('sample:samples')
    return redirect('app:login')