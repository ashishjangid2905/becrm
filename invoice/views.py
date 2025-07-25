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


# def get_biller_variable(biller_dtl, variable_name):
#     today = timezone.now().date()

#     filters = {
#         "from_date__lte": today,
#         "biller_id": biller_dtl,
#         "variable_name": variable_name,
#     }

#     variable = BillerVariable.objects.filter(
#         Q(to_date__gte=today) | Q(to_date__isnull=True), **filters
#     ).last()

#     return variable.variable_value if variable else None


# @login_required(login_url="app:login")
# def biller_detail(request, biller_id):

#     biller_dtl = biller.objects.get(pk=biller_id)
#     banks = bankDetail.objects.filter(biller_id=biller_id)
#     format_choice = FORMAT

#     biller_variables = {
#         "pi_tag": get_biller_variable(biller_dtl, "pi_tag"),
#         "pi_format": get_biller_variable(biller_dtl, "pi_format"),
#         "invoice_tag": get_biller_variable(biller_dtl, "invoice_tag"),
#         "invoice_format": get_biller_variable(biller_dtl, "invoice_format"),
#     }

#     context = {
#         "biller_dtl": biller_dtl,
#         "banks": banks,
#         "format_choice": format_choice,
#         "biller_variables": biller_variables,
#     }

#     return render(request, "invoices/biller.html", context)


# @login_required(login_url="app:login")
# def set_format(request, biller_id):
#     if request.user.role != "admin":
#         return redirect("app:dashboard")

#     biller_instanse = get_object_or_404(biller, pk=biller_id)
#     user_id = request.user.id

#     target_url = reverse("invoice:biller_detail", args=[biller_instanse.id])

#     biller_variables = {
#         "pi_tag": get_biller_variable(biller_instanse, "pi_tag"),
#         "pi_format": get_biller_variable(biller_instanse, "pi_format"),
#         "invoice_tag": get_biller_variable(biller_instanse, "invoice_tag"),
#         "invoice_format": get_biller_variable(biller_instanse, "invoice_format"),
#     }

#     if request.method == "POST":
#         pi_tag = request.POST.get("pi_tag")
#         pi_format = request.POST.get("pi_format")
#         invoice_tag = request.POST.get("invoice_tag")
#         invoice_format = request.POST.get("invoice_format")
#         from_date_str = request.POST.get("from_date")

#         try:
#             from_date = dt.strptime(from_date_str, "%Y-%m-%d").date()
#         except ValueError:
#             return HttpResponseRedirect(target_url)

#         for key, currentValue in biller_variables.items():
#             if currentValue:
#                 existing_Variables = BillerVariable.objects.filter(
#                     biller_id=biller_instanse, variable_name=key
#                 ).last()
#                 if existing_Variables:
#                     existing_Variables.to_date = from_date - timedelta(days=1)
#                     existing_Variables.save()

#             newValue = request.POST.get(key)
#             if newValue:
#                 BillerVariable.objects.create(
#                     biller_id=biller_instanse,
#                     variable_name=key,
#                     variable_value=newValue,
#                     from_date=from_date,
#                     inserted_by=user_id,
#                 )

#     return HttpResponseRedirect(target_url)


# @login_required(login_url="app:login")
# def add_biller(request):

#     if request.user.role == "admin" and request.method == "POST":
#         user = request.user.id
#         biller_name = request.POST.get("biller_name")
#         brand_name = request.POST.get("brand_name")
#         biller_gstin = request.POST.get("gstin")
#         biller_msme = request.POST.get("msme")
#         biller_pan = request.POST.get("pan")
#         reg_address1 = request.POST.get("address1")
#         reg_address2 = request.POST.get("address2")
#         reg_city = request.POST.get("city")
#         reg_state = request.POST.get("state")
#         reg_pincode = request.POST.get("pincode")
#         reg_country = request.POST.get("country")
#         corp_address1 = request.POST.get("corp_address1")
#         corp_address2 = request.POST.get("corp_address2")
#         corp_city = request.POST.get("corp_city")
#         corp_state = request.POST.get("corp_state")
#         corp_pincode = request.POST.get("corp_pincode")
#         corp_country = request.POST.get("corp_country")

#         try:
#             newBiller = biller.objects.create(
#                 biller_name=biller_name,
#                 brand_name=brand_name,
#                 biller_gstin=biller_gstin,
#                 biller_msme=biller_msme,
#                 biller_pan=biller_pan,
#                 reg_address1=reg_address1,
#                 reg_address2=reg_address2,
#                 reg_city=reg_city,
#                 reg_state=reg_state,
#                 reg_pincode=reg_pincode,
#                 reg_country=reg_country,
#                 corp_address1=corp_address1,
#                 corp_address2=corp_address2,
#                 corp_city=corp_city,
#                 corp_state=corp_state,
#                 corp_pincode=corp_pincode,
#                 corp_country=corp_country,
#                 inserted_by=user,
#             )

#             target_url = reverse("invoice:biller_detail", args=[newBiller.id])

#             return HttpResponseRedirect(target_url)
#         except IntegrityError:
#             messages.error(request, "Biller with this GSTIN already exists.")
#             return redirect("invoice:biller_list")

#     return redirect("invoice:biller_list")


# @login_required(login_url="app:login")
# def add_bank(request, biler_id):

#     biller_obj = biller.objects.get(pk=biler_id)
#     if request.user.role == "admin" and request.method == "POST":
#         user = request.user.id
#         bnf_name = request.POST.get("beneficiary_name")
#         is_upi = request.POST.get("is_upi") == "on"
#         try:
#             if is_upi:
#                 # Handle UPI-specific bank details
#                 upi_id = request.POST.get("upi_id")
#                 upi_no = request.POST.get("upi_no")
#                 bankDetail.objects.create(
#                     biller_id=biller_obj,
#                     bnf_name=bnf_name,
#                     is_upi=is_upi,
#                     upi_id=upi_id,
#                     upi_no=upi_no,
#                     inserted_by=user,
#                 )
#             else:
#                 # Handle traditional bank details
#                 bank_name = request.POST.get("bank_name")
#                 branch_address = request.POST.get("branch_address")
#                 ac_no = request.POST.get("ac_no")
#                 ifsc = request.POST.get("ifsc_code")
#                 swift_code = request.POST.get("swift_code")
#                 bankDetail.objects.create(
#                     biller_id=biller_obj,
#                     bnf_name=bnf_name,
#                     bank_name=bank_name,
#                     branch_address=branch_address,
#                     ac_no=ac_no,
#                     ifsc=ifsc,
#                     swift_code=swift_code,
#                     inserted_by=user,
#                 )

#             messages.success(request, "Bank details added successfully.")
#             return redirect(reverse("invoice:biller_detail", args=[biler_id]))

#         except IntegrityError:
#             messages.error(
#                 request,
#                 "An error occurred while saving the bank details. Please try again.",
#             )
#             return redirect(request.path_info)

#     return redirect(reverse("invoice:biller_detail", args=[biler_id]))


# @login_required(login_url="app:login")
# def process_pi(request, pi):
#     # Get the proforma instance and check if it's already closed
#     pi_instance = get_object_or_404(proforma, pk=pi)
#     closed_pi_instance = convertedPI.objects.filter(pi_id=pi_instance).first()
#     port_choice = Portmaster.objects.all()
#     country_choice = CountryMaster.objects.all()

#     context = {
#         "pi": pi_instance,
#         "report_format": REPORT_FORMAT,
#         "reports": REPORTS,
#         "port_choice": port_choice,
#         "country_choice": country_choice,
#     }

#     if pi_instance.status == "closed":

#         if request.method == "POST" and closed_pi_instance.is_processed == False:
#             # Retrieve the lists of values from the form
#             report_types = request.POST.getlist("report_type")
#             report_formats = request.POST.getlist("report_format")
#             countries = request.POST.getlist("country")
#             hsns = request.POST.getlist("hsn")
#             products = request.POST.getlist("product")
#             iecs = request.POST.getlist("iec")
#             exporters = request.POST.getlist("exporter")
#             importers = request.POST.getlist("importer")
#             from_months = request.POST.getlist("from_month")
#             to_months = request.POST.getlist("to_month")

#             foreign_countries_all = request.POST.getlist("foreign_country[]")
#             ports_all = request.POST.getlist("ports[]")

#             fc_index = 0
#             ports_index = 0

#             # Loop through each order entry, with index to handle multi-selects uniquely
#             for i in range(len(report_types)):
#                 # Calculate the slice for current form entry
#                 foreign_countries = foreign_countries_all[
#                     fc_index : fc_index + len(report_types)
#                 ]
#                 ports = ports_all[ports_index : ports_index + len(report_types)]

#                 processedOrder.objects.create(
#                     pi_id=pi_instance,
#                     report_type=report_types[i],
#                     format=report_formats[i],
#                     country=countries[i],
#                     hsn=hsns[i],
#                     product=products[i],
#                     iec=iecs[i],
#                     exporter=exporters[i],
#                     importer=importers[i],
#                     foreign_country=", ".join(
#                         foreign_countries
#                     ),  # Join list into comma-separated string
#                     port=", ".join(ports),  # Join list into comma-separated string
#                     from_month=from_months[i],
#                     to_month=to_months[i],
#                 )

#                 fc_index += len(report_types)
#                 ports_index += len(report_types)

#             # Mark the converted PI instance as processed
#             if closed_pi_instance:
#                 closed_pi_instance.is_processed = True
#                 closed_pi_instance.save()

#             return redirect("invoice:processed_list")  # Redirect after processing

#         return render(request, "invoices/process-pi.html", context)

#     return redirect("invoice:pi_list")


# def get_invoice_no(biller_id, invoice_tag, invoice_format, new_no=None):
#     fiscalyear.START_MONTH = 4
#     fy = str(fiscalyear.FiscalYear.current())[-2:]
#     py = str(int(fy) - 1)

#     if not isinstance(invoice_format, str):
#         raise ValueError(
#             f"Expected pi_format to be a string, got {type(invoice_format)}"
#         )

#     search_prefix = invoice_format.format(py=py, fy=fy, tag=invoice_tag, num=0).rstrip(
#         "0"
#     )

#     if not new_no:
#         last_invoice = (
#             convertedPI.objects.filter(
#                 invoice_no__startswith=search_prefix, pi_id__bank__biller_id=biller_id
#             )
#             .order_by("pi_no")
#             .last()
#         )

#         if last_invoice:
#             try:
#                 last_no = int(last_invoice.pi_no.split(search_prefix)[-1])
#             except:
#                 last_no = 0
#             new_no = last_no + 1
#         else:
#             new_no = 1

#     invoice_no = invoice_format.format(py=py, fy=fy, tag=invoice_tag, num=new_no)

#     return invoice_no


# @login_required(login_url="app:login")
# def bulkInvoiceUpdate(request):

#     if request.user.role != "admin" and request.user.department != "account":
#         messages.error(request, "You are not Authorized User to Update")
#         return redirect("invoice:invoice_list")

#     target_url = reverse("invoice:invoice_list")

#     if request.method == "POST" and request.FILES.get("file"):
#         uploaded_file = request.FILES["file"]
#         if not uploaded_file.name.endswith(".xlsx"):
#             messages.error(
#                 request, "Invalid file type. Please upload an Excel (.xlsx) file."
#             )
#             return redirect("invoice:invoice_list")

#         updated_count = 0
#         skipped_count = 0
#         skipped_rows = []

#         try:
#             wd = load_workbook(uploaded_file)
#             ws = wd.active

#             expected_headers = [
#                 "S.N",
#                 "Team Member",
#                 "Company Name",
#                 "GSTIN",
#                 "Address",
#                 "State",
#                 "Country",
#                 "PI No",
#                 "PI Date",
#                 "Contact Person Name",
#                 "Email",
#                 "Contact Number",
#                 "Bank",
#                 "A/C No",
#                 "Beneficry Name",
#                 "Payment Status",
#                 "1st Payment",
#                 "1st Payment Date",
#                 "2nd Payment",
#                 "2nd Payment Date",
#                 "3rd Payment",
#                 "3rd Payment Date",
#                 "Amount",
#                 "Amount (inc. tax)",
#                 "Total Received",
#                 "Is Generated",
#                 "Invoice No",
#                 "Invoice Date",
#             ]

#             headers = [cell.value for cell in ws[1]]

#             if headers != expected_headers:
#                 messages.error(
#                     request,
#                     "Invalid file format. Please upload a file exported from the system.",
#                 )
#                 return redirect("invoice:invoice_list")

#             for row in ws.iter_rows(min_row=2, values_only=True):
#                 pi_no = row[7]
#                 invoice_no = row[26]
#                 invoice_date = row[27]

#                 if not pi_no:
#                     skipped_rows.append((*row, "Missing PI No"))
#                     skipped_count += 1
#                     continue

#                 try:
#                     update_invoice = convertedPI.objects.filter(
#                         pi_id__pi_no=pi_no
#                     ).first()

#                     biller_id = update_invoice.pi_id.bank.biller_id

#                     invoice_tag = get_biller_variable(biller_id, "invoice_tag")
#                     invoice_format = get_biller_variable(biller_id, "invoice_format")

#                     new_invoice_no = get_invoice_no(
#                         biller_id, invoice_tag, invoice_format, int(invoice_no)
#                     )

#                     if not update_invoice:
#                         skipped_rows.append(
#                             (
#                                 *row,
#                                 f"User does not request Tax invoice for PI No {pi_no}",
#                             )
#                         )
#                         skipped_count += 1
#                         continue

#                     if (
#                         update_invoice.is_taxInvoice
#                         and update_invoice.invoice_no != new_invoice_no
#                     ):
#                         skipped_rows.append(
#                             (
#                                 *row,
#                                 f"Invoice already generate against PI and Invoice No is {update_invoice.invoice_no}",
#                             )
#                         )
#                         skipped_count += 1
#                         continue

#                     if (
#                         convertedPI.objects.filter(invoice_no=new_invoice_no)
#                         .exclude(pi_id__pi_no=pi_no)
#                         .exists()
#                     ):
#                         skipped_rows.append(
#                             (*row, f"Invoice No {invoice_no} already Exists")
#                         )
#                         skipped_count += 1
#                         continue

#                     update_invoice.invoice_no = new_invoice_no
#                     update_invoice.invoice_date = invoice_date
#                     update_invoice.is_taxInvoice = True
#                     update_invoice.save()
#                     updated_count += 1

#                 except Exception as e:
#                     skipped_rows.append((*row, f"Error: {e}"))
#                     skipped_count += 1

#             if skipped_rows:
#                 skipped_wd = Workbook()
#                 skipped_ws = skipped_wd.active

#                 skipped_ws.title = "Not Uploaded"

#                 headers = [cell.value for cell in ws[1]] + ["Error Reason"]
#                 skipped_ws.append(headers)

#                 for skipped_row in skipped_rows:
#                     skipped_ws.append(skipped_row)

#                 today = timezone.now().date()
#                 response = HttpResponse(
#                     content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#                 )
#                 response["Content-Disposition"] = (
#                     f"attachment; filename=Not Uploaded-list{today}.xlsx"
#                 )

#                 # Save the workbook to the response object
#                 skipped_wd.save(response)

#                 return response

#             messages.success(
#                 request,
#                 f"Total Invoice Update {updated_count} and Error {skipped_count}",
#             )
#             return HttpResponseRedirect(target_url)

#         except Exception as e:
#             messages.error(request, f"An error occurred: {e}")
#             return redirect("invoice:invoice_list")
#     messages.error(request, f"file is not Uploaded")
#     return redirect("invoice:invoice_list")


# def int_to_roman(num):
#     val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
#     syms = ["m", "cm", "d", "cd", "c", "xc", "l", "xl", "x", "ix", "v", "iv", "i"]

#     roman_num = ""
#     i = 0
#     while num > 0:
#         for _ in range(num // val[i]):
#             roman_num += syms[i]
#             num -= val[i]
#         i += 1
#     return roman_num

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
