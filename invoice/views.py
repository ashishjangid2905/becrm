# all Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives

# All Import from apps
from .models import (
    proforma,
    orderList,
    convertedPI,
    processedOrder,
)
from billers.models import *
from lead.models import leads
from teams.models import User, Profile
from .utils import (
    SUBSCRIPTION_MODE,
    STATUS_CHOICES,
    PAYMENT_TERM,
    COUNTRY_CHOICE,
    STATE_CHOICE,
    CATEGORY,
    REPORT_TYPE,
    PAYMENT_STATUS,
    REPORT_FORMAT,
    ORDER_STATUS,
    REPORTS,
    FORMAT,
)
from teams.custom_email_backend import CustomEmailBackend
from teams.templatetags.teams_custom_filters import get_current_position
from .permissions import Can_Approve, Can_Generate_TaxInvoice
from .custom_utils import (
    get_biller_variable,
    current_fy,
    get_invoice_no_from_date,
    exportInvoicelist,
    pdf_PI,
)

# Third-party imports
import fiscalyear
from datetime import datetime as dt

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .serializers import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter
from django_filters import (
    FilterSet,
    CharFilter,
    NumberFilter,
    BooleanFilter,
    ModelChoiceFilter,
)
from decimal import Decimal, InvalidOperation


class PiPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class PiFilters(FilterSet):
    company_name = CharFilter(field_name="company_name", lookup_expr="icontains")
    gstin = CharFilter(field_name="gstin", lookup_expr="icontains")
    address = CharFilter(field_name="address", lookup_expr="icontains")
    subtotal = NumberFilter(field_name="summary__subtotal")
    status = CharFilter(field_name="status", lookup_expr="exact")
    isApproved = BooleanFilter(field_name="is_Approved")
    isTaxInvoice = BooleanFilter(field_name="convertedpi__is_taxInvoice")
    paymentStatus = CharFilter(
        field_name="convertedpi__payment_status", lookup_expr="exact"
    )
    country = CharFilter(field_name="processedorders__country", lookup_expr="exact")
    user = NumberFilter(field_name="user_id")
    companyRef = ModelChoiceFilter(
        field_name="company_ref", queryset=leads.objects.all()
    )

    class Meta:
        model = proforma
        fields = [
            "company_name",
            "gstin",
            "address",
            "subtotal",
            "status",
            "isApproved",
            "country",
            "companyRef",
            "user"
        ]


class ProformaMixin:
    def get_object(self, slug):
        return get_object_or_404(proforma, slug=slug)


# View for Fetch Proforma Invoice List
class ProformaView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PiPagination
    ordering_fields = [
        "company_name",
        "gstin",
        "address",
        "pi_no",
        "pi_date",
        "user_name",
        "summary__subtotal",
        "created_at",
    ]
    ordering = ["-created_at"]

    def get(self, request):
        try:
            pi_list = (
                proforma.objects.filter(user_id=request.user.id)
                .prefetch_related("processedorders", "orderlist")
                .select_related("convertedpi", "summary")
            )

            selected_fy = request.GET.get("fy", current_fy())
            if selected_fy:
                start_fy = dt(int(selected_fy.split("-")[0]), 4, 1).date()
                end_fy = dt(int(selected_fy.split("-")[1]), 3, 31).date()
                pi_list = pi_list.filter(pi_date__range=(start_fy, end_fy))

            search_query = request.GET.get("search", None)
            if search_query:
                filters = (
                    Q(company_name__icontains=search_query)
                    | Q(gstin__icontains=search_query)
                    | Q(user_name__icontains=search_query)
                    | Q(address__icontains=search_query)
                    | Q(requistioner__icontains=search_query)
                    | Q(pi_no__icontains=search_query)
                )
                try:
                    value = Decimal(search_query)
                    filters |= Q(summary__subtotal__exact=value)
                except InvalidOperation:
                    pass

                pi_list = pi_list.filter(filters)

            filtered_pi = PiFilters(request.GET, queryset=pi_list)
            if filtered_pi.is_valid():
                pi_list = filtered_pi.qs
            else:
                print("Filter errors:", filtered_pi.errors)

            ordering_query = request.GET.get("ordering", None)
            if ordering_query:
                ordering_filter = OrderingFilter()
                pi_list = ordering_filter.filter_queryset(request, pi_list, self)
            paginator = self.pagination_class()
            paginated_pi = paginator.paginate_queryset(pi_list, request)
            serializer = ProformaSerializer(paginated_pi, many=True)
            return paginator.get_paginated_response(serializer.data)
        except proforma.DoesNotExist:
            return Response({"message": "No Proforma Invoice exists"})


# View for Create and Edit Proforma Invoice
class ProformaCreateUpdateView(APIView, ProformaMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        try:
            insatance = self.get_object(slug=slug)
            serializer = ProformaCreateSerializer(insatance)
            exportReq = request.GET.get("download")
            invoiceType = request.GET.get("is_invoice", False) == "true"
            if exportReq == "pdf":
                return pdf_PI(insatance.id, invoiceType)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def post(self, request):
        try:
            serializer = ProformaCreateSerializer(data=request.data)
            user_id = request.user.id
            if serializer.is_valid():
                instance = serializer.save(user_id=user_id)

                result = ProformaSerializer(instance)
                return Response(result.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def put(self, request, slug):
        # handle full update of Proforma
        instance = self.get_object(slug)
        if not instance:
            return Response(
                {"error": "Proforma not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProformaCreateSerializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save(edited_by=request.user.id)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def patch(self, request, slug):
        # handle full update of Proforma
        instance = self.get_object(slug=slug)
        data = request.data

        convertedPIData = data.pop("convertedpi", None)

        if not instance:
            return Response(
                {"error": "Proforma not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProformaCreateSerializer(instance, data=data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pi_user = get_object_or_404(User, pk=instance.user_id)
        if "is_Approved" in data:
            owner_group = set(pi_user.groups.values_list("name", flat=True))
            user_group = set(request.user.groups.values_list("name", flat=True))

            can_approve = (
                "Head" in user_group
                or ("VP" in user_group and "Head" not in owner_group)
                or (
                    "Sr. Executive" in user_group
                    and not owner_group.intersection({"VP", "Head"})
                )
            )

            if not can_approve:
                return Response(
                    {"messages": "You are not an authorised to approve this proforma"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer.save(approved_by=request.user.id, partial=True)
            result = ProformaSerializer(instance)
            return Response(result.data, status=status.HTTP_200_OK)
        elif "status" in data:
            serializer.save(edited_by=request.user.id, partial=True)
            if data["status"] == "closed":
                if not convertedPIData:
                    return Response(
                        {"error": "need to update payment status"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                convertedPI_id = convertedPIData.get("id", None)
                convertedPIData["is_closed"] = True
                convertedPIData["is_hold"] = False
                convertedPIData["is_cancel"] = False
                if convertedPI_id:
                    convertedPiInstance = get_object_or_404(
                        convertedPI, pk=convertedPI_id
                    )
                    CPISerializer = ConvertedPISerializer(
                        convertedPiInstance, data=convertedPIData, partial=True
                    )
                else:
                    CPISerializer = ConvertedPISerializer(data=convertedPIData)

                if CPISerializer.is_valid():
                    CPISerializer.save()
                else:
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                convertedPI_id = convertedPIData.get("id")
                if convertedPI_id:
                    convertedPiInstance = get_object_or_404(
                        convertedPI, pk=convertedPI_id
                    )
                    if data["status"] == "open":
                        convertedPIData["is_hold"] = True
                        convertedPIData["is_closed"] = False
                    elif data["status"] == "lost":
                        convertedPIData["is_invoiceRequire"] = False
                        convertedPIData["is_hold"] = True
                        convertedPIData["is_cancel"] = True
                        convertedPIData["is_closed"] = False
                    CPISerializer = ConvertedPISerializer(
                        convertedPiInstance, data=convertedPIData, partial=True
                    )
                    if CPISerializer.is_valid():
                        CPISerializer.save()
                    else:
                        return Response(
                            CPISerializer.errors, status=status.HTTP_400_BAD_REQUEST
                        )
            result = ProformaSerializer(instance)
            return Response(result.data, status=status.HTTP_200_OK)
        return Response(
            {"error": "need to check error"}, status=status.HTTP_400_BAD_REQUEST
        )


# View for Approval of Proforma Invoice
class ApproveRequestPIView(APIView):
    permission_classes = [IsAuthenticated, Can_Approve]
    pagination_class = PiPagination
    ordering_fields = [
        "company_name",
        "gstin",
        "address",
        "pi_no",
        "pi_date",
        "summary__subtotal",
        "user_name",
        "created_at",
    ]
    ordering = ["-created_at"]

    def get(self, request):
        try:
            profile_instance = get_object_or_404(Profile, user=request.user)
            current_position = get_current_position(profile_instance)
            all_users = User.objects.filter(profile__branch=profile_instance.branch).exclude(id=request.user.id)
            user_exclusion = {
                "Head": ["Head"],
                "VP": ["Head", "VP"],
                "Sr. Executive": ["Head", "VP", "Sr. Executive"],
            }

            if request.user.role != "admin":
                if current_position in user_exclusion:
                    all_users = all_users.exclude(
                        groups__name__in=user_exclusion[current_position]
                    )

            pi_list = (
                proforma.objects.filter(
                    user_id__in=list(all_users.values_list("id", flat=True))
                )
                .prefetch_related("orderlist", "processedorders")
                .select_related("convertedpi", "summary")
            )

            selected_fy = request.GET.get("fy", current_fy())
            if selected_fy:
                start_fy = dt(int(selected_fy.split("-")[0]), 4, 1).date()
                end_fy = dt(int(selected_fy.split("-")[1]), 3, 31).date()
                pi_list = pi_list.filter(pi_date__range=(start_fy, end_fy))

            search_query = request.GET.get("search", None)
            if search_query:
                filters = (
                    Q(company_name__icontains=search_query)
                    | Q(gstin__icontains=search_query)
                    | Q(user_name__icontains=search_query)
                    | Q(address__icontains=search_query)
                    | Q(requistioner__icontains=search_query)
                    | Q(pi_no__icontains=search_query)
                )
                try:
                    value = Decimal(search_query)
                    filters |= Q(summary__subtotal__exact=value)
                except InvalidOperation:
                    pass

                pi_list = pi_list.filter(filters)

            filtered_pi = PiFilters(request.GET, queryset=pi_list)
            if filtered_pi.is_valid():
                pi_list = filtered_pi.qs
            else:
                print("Filter errors:", filtered_pi.errors)

            ordering_query = request.GET.get("ordering", None)
            if ordering_query:
                ordering_filter = OrderingFilter()
                pi_list = ordering_filter.filter_queryset(request, pi_list, self)
            paginator = self.pagination_class()
            paginated_pi = paginator.paginate_queryset(pi_list, request)
            serializer = ProformaSerializer(paginated_pi, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# View for Invoice List and Invoice request List
class InvoiceListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PiPagination
    ordering_fields = [
        "company_name",
        "gstin",
        "address",
        "pi_no",
        "pi_date",
        "summary__subtotal",
        "convertedpi__formatted_invoice",
        "convertedpi__invoice_date",
        "convertedpi__requested_at",
        "user_name",
        "created_at",
    ]
    ordering = ["-convertedpi__requested_at"]

    def get(self, request):
        try:

            profile_instance = get_object_or_404(Profile, user=request.user)
            current_position = get_current_position(profile_instance)
            all_users = User.objects.filter(
                profile__branch=profile_instance.branch
            ).values_list("id", flat=True)

            pi_list = (
                proforma.objects.filter(
                    user_id__in=list(all_users), convertedpi__is_invoiceRequire=True
                )
                .prefetch_related("orderlist", "processedorders")
                .select_related("convertedpi", "summary")
            )

            if current_position != "Head" and request.user.role != "admin":
                pi_list = pi_list.filter(user_id=request.user.id)
            else:
                pi_list = pi_list.filter(convertedpi__is_taxInvoice=True)

            selected_fy = request.GET.get("fy", current_fy())
            if selected_fy:
                start_fy = dt(int(selected_fy.split("-")[0]), 4, 1).date()
                end_fy = dt(int(selected_fy.split("-")[1]), 3, 31).date()
                pi_list = pi_list.filter(
                    Q(convertedpi__invoice_date__range=(start_fy, end_fy))
                    | Q(
                        convertedpi__invoice_date__isnull=True,
                        convertedpi__requested_at__range=(start_fy, end_fy),
                    )
                )

            search_query = request.GET.get("search", None)
            if search_query:
                filters = (
                    Q(company_name__icontains=search_query)
                    | Q(gstin__icontains=search_query)
                    | Q(address__icontains=search_query)
                    | Q(requistioner__icontains=search_query)
                    | Q(pi_no__icontains=search_query)
                )
                try:
                    value = Decimal(search_query)
                    filters |= Q(summary__subtotal__exact=value)
                except InvalidOperation:
                    pass

                pi_list = pi_list.filter(filters)

            filtered_pi = PiFilters(request.GET, queryset=pi_list)
            if filtered_pi.is_valid():
                pi_list = filtered_pi.qs
            else:
                print("Filter errors:", filtered_pi.errors)

            ordering_query = request.GET.get("ordering", None)
            if ordering_query:
                ordering_filter = OrderingFilter()
                pi_list = ordering_filter.filter_queryset(request, pi_list, self)

            exportReq = request.GET.get("action", None)
            if exportReq == "export":
                date_range = request.GET.get("dateRange", None)
                if date_range:
                    start_date = date_range.split(",")[0]
                    end_date = date_range.split(",")[1]
                    pi_list = pi_list.filter(
                        Q(convertedpi__invoice_date__range=(start_date, end_date))
                    ).order_by("convertedpi__formatted_invoice")
                return exportInvoicelist(pi_list)

            paginator = self.pagination_class()
            paginated_pi = paginator.paginate_queryset(pi_list, request)
            serializer = ProformaSerializer(paginated_pi, many=True)
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Get list of proforma invoice requested for Tax Invoiceand managed by accounts and admin only
class InvoiceUpdateListView(APIView):
    permission_classes = [IsAuthenticated, Can_Generate_TaxInvoice]
    pagination_class = PiPagination
    ordering_fields = [
        "company_name",
        "gstin",
        "address",
        "pi_no",
        "pi_date",
        "summary__subtotal",
        "convertedpi__invoice_no",
        "convertedpi__invoice_date",
        "convertedpi__requested_at",
        "user_name",
        "created_at",
    ]
    ordering = ["-convertedpi__requested_at"]

    def get(self, request):
        try:
            profile_instance = get_object_or_404(Profile, user=request.user)
            all_users = User.objects.filter(
                profile__branch=profile_instance.branch
            ).values_list("id", flat=True)

            pi_list = (
                proforma.objects.filter(
                    user_id__in=list(all_users),
                    convertedpi__is_invoiceRequire=True,
                    convertedpi__is_taxInvoice=False,
                )
                .prefetch_related("orderlist", "processedorders")
                .select_related("convertedpi", "summary")
            )

            selected_fy = request.GET.get("fy", current_fy())
            if selected_fy:
                start_fy = dt(int(selected_fy.split("-")[0]), 4, 1).date()
                end_fy = dt(int(selected_fy.split("-")[1]), 3, 31).date()
                pi_list = pi_list.filter(
                    Q(convertedpi__invoice_date__range=(start_fy, end_fy))
                    | Q(
                        convertedpi__invoice_date__isnull=True,
                        convertedpi__requested_at__range=(start_fy, end_fy),
                    )
                )

            search_query = request.GET.get("search", None)
            if search_query:
                filters = (
                    Q(company_name__icontains=search_query)
                    | Q(gstin__icontains=search_query)
                    | Q(user_name__icontains=search_query)
                    | Q(address__icontains=search_query)
                    | Q(requistioner__icontains=search_query)
                    | Q(pi_no__icontains=search_query)
                )
                try:
                    value = Decimal(search_query)
                    filters |= Q(summary__subtotal__exact=value)
                except InvalidOperation:
                    pass

                pi_list = pi_list.filter(filters)

            filtered_pi = PiFilters(request.GET, queryset=pi_list)
            if filtered_pi.is_valid():
                pi_list = filtered_pi.qs
            else:
                print("Filter errors:", filtered_pi.errors)

            ordering_query = request.GET.get("ordering", None)
            if ordering_query:
                ordering_filter = OrderingFilter()
                pi_list = ordering_filter.filter_queryset(request, pi_list, self)

            exportReq = request.GET.get("action", None)
            if exportReq == "export":
                return exportInvoicelist(pi_list)

            paginator = self.pagination_class()
            paginated_pi = paginator.paginate_queryset(pi_list, request)
            serializer = ProformaSerializer(paginated_pi, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        try:
            print(id)
            convertedpiInstance = get_object_or_404(convertedPI, id=id)

            data = request.data
            biller_id = convertedpiInstance.pi_id.bank.biller_id

            invoice_tag = get_biller_variable(biller_id, "invoice_tag")
            invoice_format = get_biller_variable(biller_id, "invoice_format")
            invoice_number = int(data.get("invoice_number"))
            invoice_date = data.get("invoice_date")
            if isinstance(invoice_date, str):
                invoice_date = dt.strptime(invoice_date, "%Y-%m-%d").date()

            target_fy = current_fy(invoice_date)

            def get_fy_filter():
                all_records = convertedPI.objects.filter(invoice_date__isnull=False)
                filtered = []

                for obj in all_records:
                    if current_fy(obj.invoice_date) == target_fy:
                        filtered.append(obj.id)
                return all_records.filter(id__in=filtered)

            same_fy_invoices = get_fy_filter()

            lower_conflict = same_fy_invoices.filter(
                invoice_number__lt=invoice_number, invoice_date__gt=invoice_date
            )
            # print(f"lower_conflict: {lower_conflict}")

            higher_conflict = same_fy_invoices.filter(
                invoice_number__gt=invoice_number, invoice_date__lt=invoice_date
            )
            # print(f"higher_conflict: {higher_conflict}")

            if lower_conflict.exists():
                return Response(
                    {
                        "error": "There are lower invoice numbers with future dates in the same FY."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if higher_conflict.exists():
                return Response(
                    {
                        "error": "There are higher invoice numbers with past dates in the same FY."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                formatedInvoiceNo = get_invoice_no_from_date(
                    invoice_tag,
                    invoice_format,
                    data.get("invoice_date"),
                    invoice_number,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            if convertedPI.objects.filter(formatted_invoice=formatedInvoiceNo).exists():
                return Response(
                    {"error": "Invoice No already exists"},
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )

            data["formatted_invoice"] = formatedInvoiceNo
            data["is_taxInvoice"] = True
            data["is_closed"] = True
            data["generated_by"] = request.user.id
            serializer = ConvertedPISerializer(
                convertedpiInstance, data=data, partial=True
            )

            if serializer.is_valid():
                serializer.save(partial=True)
                result = ProformaSerializer(convertedpiInstance.pi_id)
                return Response(result.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Processed Proform list to view and update order status by production department
class ProcessedPIUpdateListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PiPagination
    ordering_fields = [
        "company_name",
        "gstin",
        "address",
        "pi_no",
        "pi_date",
        "convertedpi__invoice_no",
        "convertedpi__invoice_date",
        "convertedpi__requested_at",
        "user_name",
        "created_at",
    ]
    ordering = ["-convertedpi__requested_at"]

    @staticmethod
    def get_object(id):
        return get_object_or_404(processedOrder, pk=id)

    def get(self, request):
        try:
            profile_instance = get_object_or_404(Profile, user=request.user)
            all_users = User.objects.filter(
                profile__branch=profile_instance.branch
            ).values_list("id", flat=True)

            pi_list = (
                proforma.objects.filter(
                    user_id__in=list(all_users), convertedpi__is_processed=True
                )
                .prefetch_related("orderlist", "processedorders")
                .select_related("convertedpi", "summary")
            )

            if request.user.role != "admin" and request.user.department != "production":
                pi_list = pi_list.filter(user_id=request.user.id)

            selected_fy = request.GET.get("fy", current_fy())
            if selected_fy:
                start_fy = dt(int(selected_fy.split("-")[0]), 4, 1).date()
                end_fy = dt(int(selected_fy.split("-")[1]), 3, 31).date()
                pi_list = pi_list.filter(
                    convertedpi__requested_at__range=(start_fy, end_fy)
                )

            search_query = request.GET.get("search", None)
            if search_query:
                filters = (
                    Q(company_name__icontains=search_query)
                    | Q(gstin__icontains=search_query)
                    | Q(user_name__icontains=search_query)
                    | Q(address__icontains=search_query)
                    | Q(requistioner__icontains=search_query)
                    | Q(pi_no__icontains=search_query)
                    | Q(pi_no__icontains=search_query)
                    | Q(pi_no__icontains=search_query)
                    | Q(processedorders__report_type__icontains=search_query)
                    | Q(processedorders__country__icontains=search_query)
                    | Q(processedorders__plan__icontains=search_query)
                    | Q(processedorders__hsn__icontains=search_query)
                    | Q(processedorders__product__icontains=search_query)
                )
                try:
                    value = Decimal(search_query)
                    filters |= Q(summary__subtotal__exact=value)
                except InvalidOperation:
                    pass

                pi_list = pi_list.filter(filters)

            pending_month = request.GET.get("month", None)

            if pending_month:
                pi_list = pi_list.filter(
                    processedorders__from_month__lte=pending_month,
                    processedorders__to_month__gte=pending_month,
                    processedorders__last_dispatch_month__lt=pending_month,
                ).distinct()

            filtered_pi = PiFilters(request.GET, queryset=pi_list)
            if filtered_pi.is_valid():
                pi_list = filtered_pi.qs
            else:
                print("Filter errors:", filtered_pi.errors)

            ordering_query = request.GET.get("ordering", None)
            if ordering_query:
                ordering_filter = OrderingFilter()
                pi_list = ordering_filter.filter_queryset(request, pi_list, self)

            paginator = self.pagination_class()
            paginated_pi = paginator.paginate_queryset(pi_list, request)
            serializer = ProformaSerializer(paginated_pi, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        try:
            orderInstance = self.get_object(id=id)
            data = request.data
            serializer = ProcessedOrderSerializer(
                orderInstance, data=data, partial=True
            )
            if serializer.is_valid():
                serializer.save(partial=True)
                # pi_Instance = get_object_or_404(proforma, pk=orderInstance.pi_id)
                result = ProformaSerializer(orderInstance.pi_id)
                return Response(result.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, slug):
        try:
            pi_instance = get_object_or_404(proforma, slug=slug)
            convertedPiInstance = get_object_or_404(convertedPI, pi_id=pi_instance)
            data = request.data.pop("processedorders")

            print(data)
            if (
                pi_instance.status != "closed"
                and pi_instance.convertedpi.is_processed == True
            ):
                return Response(
                    {"message": "You can not process this order."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = ProcessedOrderSerializer(data=data, many=True)
            if serializer.is_valid():
                serializer.save(pi_id=pi_instance)
                if convertedPiInstance:
                    convertedPiInstance.is_processed = True
                    convertedPiInstance.save()
                result = ProformaSerializer(pi_instance)
                return Response(result.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@login_required(login_url="app:login")
def biller_list(request):
    billers = biller.objects.all()

    profile_instance = get_object_or_404(Profile, user=request.user)
    user_branch = profile_instance.branch

    all_users = User.objects.filter(profile__branch=user_branch)

    all_users_id = []

    for user in all_users:
        all_users_id.append(user.id)

    billers = billers.filter(inserted_by__in=all_users_id)

    context = {
        "billers": billers,
    }
    return render(request, "invoices/biller-list.html", context)



# @login_required(login_url="app:login")
# def email_form(request, pi):
#     pi_instance = get_object_or_404(proforma, pk=pi)
#     smtp_details = SmtpConfig.objects.filter(user=request.user).first()
#     password = smtp_details.email_host_password
#     context = {"pi_instance": pi_instance, "smtp_details": password}

#     if pi_instance.user_id != request.user.id:
#         return HttpResponse("You are not Authorised to Process the order.")

#     return render(request, "invoices/emailForm.html", context)


# @login_required(login_url="app:login")
# def send_test_mail(request, pi):
#     pi_instance = get_object_or_404(proforma, pk=pi)

#     smtp_details = SmtpConfig.objects.filter(user=request.user).first()

#     if pi_instance.user_id != request.user.id:
#         return HttpResponse("You are not Authorised to Process the order.")

#     if request.method == "GET":
#         to_mail = request.GET.get("to")
#         subject = request.GET.get("mailSubject")
#         msg = request.GET.get("mailMessage")

#     smtp_settings = {
#         "host": smtp_details.smtp_server,
#         "port": smtp_details.smtp_port,
#         "username": smtp_details.user.email,
#         "password": smtp_details.email_host_password,
#         "use_tls": smtp_details.use_tls,
#     }

#     html_message = f"{msg}"
#     recipient_list = [email.strip() for email in to_mail.split(",")]

#     email_backend = CustomEmailBackend(**smtp_settings)

#     email = EmailMultiAlternatives(
#         subject=subject,
#         body="plain_message",
#         from_email="info@besmartexim.com",
#         to=recipient_list,  # Replace with actual recipient
#         connection=email_backend,
#     )

#     email.attach_alternative(html_message, "text/html")

#     fileValue = pdf_PI(pi_instance.id)

#     fileName = (
#         f"PI_{pi_instance.company_name}_{pi_instance.pi_no}_{pi_instance.pi_date}.pdf"
#     )

#     email.attach(fileName, fileValue, "application/pdf")

#     email.send()
#     return HttpResponse(f"status: success, message: Email has been sent")
