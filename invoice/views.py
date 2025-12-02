# all Django imports
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q, F
from django.db.models.functions import Substr, Cast
from django.db.models import Value, Max, Case, When, BooleanField, IntegerField
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives

# All Import from apps
from .models import *
from billers.models import *
from lead.models import leads
from teams.models import User, Profile

from teams.custom_email_backend import CustomEmailBackend
from teams.templatetags.teams_custom_filters import get_current_position
from .permissions import Can_Approve, Can_Generate_TaxInvoice
from .custom_utils import (
    get_biller_variable,
    current_fy,
    fy_date_range,
    get_invoice_no_from_date,
    exportInvoicelist,
    pdf_PI,
)

from .mixins import DynamicPiFilterMixin

# Third-party imports
from datetime import datetime as dt

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework.mixins import ListModelMixin, UpdateModelMixin, CreateModelMixin
from .serializers import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters import (
    FilterSet,
    CharFilter,
    NumberFilter,
    BooleanFilter,
    ModelChoiceFilter,
)

from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
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
    orderStatus = CharFilter(
        field_name="processedorders__order_status", lookup_expr="exact"
    )
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
            "user",
        ]


class ProformaMixin:
    def get_object(self, slug):
        return get_object_or_404(proforma, slug=slug)


"""
Proforma List API View
This view provide a paginated list of Proforma invoices for the authenticated user.
It supports filtering, ordering, searching and fiscal-year-date based filtering.

Key Features:
    - User-Specific: Only return proforma invoices that created by the logged-in user.
    - Filtering: using Pifilter, field based filtering
    - Ordering: Support ordering for multiple fileds (e.g company_name, pi_no, pi_date etc)
    - Searching: Allows text-based search across fields and numeric search for subtotal.
    - Fiscal Year: Defaults to the currect fiscal year if none is provided.
"""


class ProformaView(DynamicPiFilterMixin, ListAPIView):
    serializer_class = ProformaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PiPagination

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = PiFilters
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

    ordering = ["-pi_no"]

    search_fields = [
        "company_name",
        "gstin",
        "address",
        "requistioner",
        "email_id",
        "contact",
        "pi_no",
        "summary__subtotal",
    ]

    fy_field = "pi_date"

    def get_queryset(self):
        """
        Return the queryset for the logged-in user.

        Query Parameters:
        -fy (str): Fiscal Year in format 'YYYY-YYYY'. Defaults to current fy.
        -search (str): Free-text search across allowed fields.
                        If numeric then also searches by exact 'summary_subtotal'
        Example:
        GET /api/invoice/proforma/list?fy=2024-2025&search=abc
        GET /api/invoice/proforma/list?fy=2024-2025&search=12000
        """

        request = self.request

        # base queryset: Proforma Invoices for currect user with related objects
        if request.GET.get("companyRef", None):
            queryset = (
                proforma.objects.all()
                .prefetch_related("processedorders", "orderlist")
                .select_related("convertedpi", "summary")
            )
        else:
            queryset = (
                proforma.objects.filter(user_id=request.user.id)
                .select_related("convertedpi", "summary")
                .prefetch_related("orderlist", "processedorders")
            )

        # Fiscal year query
        fy = request.GET.get("fy", current_fy())
        if fy:
            queryset = self.fy_filter(request, queryset, fy)

        # Extend search to handle numeric subtotal search
        search_query = request.GET.get("search")
        if search_query:
            try:
                value = Decimal(search_query)
                queryset = queryset | queryset.filter(summary__subtotal=value)
            except InvalidOperation:
                pass

        return queryset


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
            branch = request.user.profile.branch.id
            if serializer.is_valid():
                instance = serializer.save(user_id=user_id, branch=branch)

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

        data = request.data

        if not data["po_no"]:
            data["po_date"] = None

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
        branch = request.user.profile.branch.id
        convertedPIData = data.pop("convertedpi", None)
        if convertedPIData:
            convertedPIData["branch"] = branch

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


"""
PI Approval Request List API View
This view provide a paginated list of Proforma invoice that logged-in user can approve exclude user's proforma's.
It supports filtering, ordering, searching and fiscal-year-date based filtering.

Key features:
    - Permission-based Access: Only return proforma list that logged-in user permitted to approve, based on role and position
    - Filtering: using Pifilter, field based filtering
    - Ordering: Support ordering for multiple fileds (e.g company_name, pi_no, pi_date etc)
    - Searching: Allows text-based search across fields and numeric search for subtotal.
    - Fiscal Year: Defaults to the currect fiscal year if none is provided.
"""


class ApproveRequestPIView(DynamicPiFilterMixin, ListAPIView):
    serializer_class = ProformaSerializer
    permission_classes = [IsAuthenticated, Can_Approve]
    pagination_class = PiPagination

    # Filter set
    filterset_class = PiFilters
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
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

    search_fields = [
        "company_name",
        "gstin",
        "user_name",
        "address",
        "requistioner",
        "email_id",
        "contact",
        "pi_no",
        "summary__subtotal",
    ]

    fy_field = "pi_date"

    def get_queryset(self):
        """
        Return a queryset for the logged-in user based-on user's role and current_position
        Query Parameters:
        - fy (str): Fiscal Year in format 'YYYY-YYYY'. Defaults to current fy.
        - search (str): Free-text search across allowed fields.
                        If numeric then also searches by exact 'summary_subtotal'

        Notes:
            - User role and position determine which Proforma records are visible
                (e.g., `Head`, `VP`, `Sr. Executive` exclusions).
            - Admin users can see all Proforma requests for their branch, excluding their own.
        """

        request = self.request

        profile = Profile.objects.select_related("user").get(user=request.user)

        # Base queryset: Proforma Invoices for currect user with related objects that exclude logged-in user's proforma
        queryset = (
            proforma.objects.filter(branch=profile.branch.id)
            .select_related("convertedpi", "summary")
            .prefetch_related("orderlist", "processedorders")
            .exclude(user_id=request.user.id)
        )

        # define position based user exclusion
        user_exclusion = {
            "Head": ["Head"],
            "VP": ["Head", "VP"],
            "Sr. Executive": ["Head", "VP", "Sr. Executive"],
        }
        all_users = User.objects.filter(profile__branch=profile.branch).exclude(
            id=request.user.id
        )

        # Fetch users as per user exclusion dict
        current_position = get_current_position(profile)
        if current_position in user_exclusion:
            all_users = all_users.exclude(
                groups__name__in=user_exclusion[current_position]
            )

        # Queryset if logged-in user is not admin
        if request.user.role != "admin":
            queryset = proforma.objects.filter(
                user_id__in=list(all_users.values_list("id", flat=True))
            )

        # Fiscal year query
        fy = request.GET.get("fy", current_fy())
        if fy:
            queryset = self.fy_filter(request, queryset, fy)

        # Extend search to handle numeric subtotal search
        search_query = request.GET.get("search")
        if search_query:
            try:
                value = Decimal(search_query)
                queryset = queryset | queryset.filter(summary__subtotal=value)
            except InvalidOperation:
                pass

        return queryset


class InvoiceListView(DynamicPiFilterMixin, ListAPIView):
    serializer_class = ProformaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PiPagination

    filterset_class = PiFilters
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
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

    search_fields = [
        "company_name",
        "gstin",
        "user_name",
        "address",
        "requistioner",
        "email_id",
        "contact",
        "pi_no",
        "summary__subtotal",
    ]

    fy_field = "convertedpi__invoice_date"
    alt_fy_field = "convertedpi__requested_at"

    def get_queryset(self):

        request = self.request
        profile = Profile.objects.select_related("user").get(user=request.user)

        # Base queryset
        queryset = (
            proforma.objects.filter(branch=profile.branch.id)
            .select_related("convertedpi", "summary")
            .prefetch_related("orderlist", "processedorders")
        )

        # Filter queryset based-on user's role and department
        if request.user.role != "admin" and request.user.department != "account":
            queryset = queryset.filter(user_id=request.user.id)
        else:
            queryset = queryset.filter(convertedpi__is_taxInvoice=True)

        # Fiscal year query
        fy = request.GET.get("fy", current_fy())
        if fy:
            queryset = self.fy_filter(request, queryset, fy)

        # Extend search  to handle numeric search for subtotal
        search_query = request.GET.get("search", None)
        if search_query:
            try:
                value = Decimal(search_query)
                queryset = queryset | queryset.filter(summary__subtotal=value)
            except InvalidOperation:
                pass

        return queryset

    def list(self, request, *args, **kwargs):
        # Export queryset in excel file
        export_req = request.GET.get("action", None)
        if export_req == "export":
            queryset = self.filter_queryset(self.get_queryset())
            date_range = request.GET.get("dateRange", None)
            if date_range:
                start_date, end_date = date_range.split(",")
                queryset = queryset.filter(
                    convertedpi__invoice_date__range=(start_date, end_date)
                ).order_by("convertedpi__formatted_invoice")

            return exportInvoicelist(queryset)

        return super().list(request, *args, **kwargs)


# Get list of proforma invoice requested for Tax Invoiceand managed by accounts and admin only
"""
Invoice Create and pending List View
This view provide the proforma invoice list that request for invoice and assign the invoice number to respective proforma
It supports filtering, ordering, searching and fiscal-year-date based filtering.

Key Features:
    - Permission Based: Can access if logged-in user Role is 'admin' or department is 'accounts' 
    - List: Only provide proforma invoices that need to generate tax invoice based on branch
    - Generate Invoice: Can generate tax invoice and handle invoice generation logic (e.g check duplicates, invoice number and date sequence)
"""


class InvoiceUpdateListView(
    DynamicPiFilterMixin, ListModelMixin, UpdateModelMixin, GenericAPIView
):
    serializer_class = ProformaSerializer
    pagination_class = PiPagination
    permission_classes = [IsAuthenticated, Can_Generate_TaxInvoice]

    filterset_class = PiFilters
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

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

    ordering = ["convertedpi__requested_at"]

    search_fields = [
        "company_name",
        "gstin",
        "user_name",
        "address",
        "requistioner",
        "email_id",
        "contact",
        "pi_no",
        "convertedpi__formatted_invoice",
        "summary__subtotal",
    ]

    fy_field = "convertedpi__requested_at"

    def get_queryset(self):
        """
        Return a queryset for the logged-in user based on role or department
        Query Parameters:
            -invoice require: filter proform invoice if is_invoiceRequire = True
            -fy (str): Fiscal Year in format 'YYYY-YYYY'. Defaults to current fy.
            -search (str): Free-text search across allowed fields.
                            If numeric then also searches by exact 'summary_subtotal'
        Note:
            - If User from 'accounts' department: Proforma records are visible.
            - Admin can see all records on respective branch
        """

        request = self.request
        profile = Profile.objects.select_related("user").get(user=request.user)

        # Base queryset: Proforma requested for tax invoice that still pending
        queryset = (
            proforma.objects.filter(
                convertedpi__is_invoiceRequire=True,
                branch=profile.branch.id,
                convertedpi__is_taxInvoice=False,
            )
            .select_related("convertedpi", "summary")
            .prefetch_related("orderlist", "processedorders")
        )

        # Fiscal year query
        fy = request.GET.get("fy", current_fy())
        if fy:
            queryset = self.fy_filter(request, queryset, fy)

        # Extend search for numeric values
        search_query = request.GET.get("search")
        if search_query:
            try:
                value = Decimal(search_query)
                queryset = queryset | queryset.filter(summary__subtotal=value)
            except InvalidOperation:
                pass

        return queryset

    def get(self, request, *args, **kwargs):

        # Handle Export queryset records in excel file
        exportReq = request.GET.get("action", None)
        queryset = self.get_queryset()
        if exportReq == "export":
            return exportInvoicelist(queryset)

        return self.list(request, *args, **kwargs)

    def patch(self, request, id):
        """
        To generate tax invoice require fields:
            - Invoice Number, Invoice Date

            check validation of invoice_number and date from serializers validate method
        """
        try:
            # Fetch convertedpi instance
            convertedpiInstance = get_object_or_404(convertedPI, id=id)
            data = request.data

            serializer = ConvertedPISerializer(
                convertedpiInstance,
                data=data,
                partial=True,
                context={"request": request},
            )

            # check serializer is valid or not
            serializer.is_valid(raise_exception=True)
            serializer.save(partial=True)  # Save serializer

            # Return proforma invoice with related objects after invoice created
            result = ProformaSerializer(convertedpiInstance.pi_id)

            return Response(result.data, status=status.HTTP_201_CREATED)
        # Handle Validation Error if serializer raise any error
        except ValidationError as ve:
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProcessedPIUpdateListView(
    DynamicPiFilterMixin,
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    GenericAPIView,
):
    serializer_class = ProformaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PiPagination

    filterset_class = PiFilters
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = [
        "company_name",
        "gstin",
        "address",
        "pi_no",
        "pi_date",
        "convertedpi__invoice_no",
        "convertedpi__invoice_date",
        "convertedpi__processed_at",
        "user_name",
        "created_at",
    ]
    ordering = ["-convertedpi__processed_at"]

    search_fields = [
        "company_name",
        "gstin",
        "address",
        "requistioner",
        "pi_no",
        "summary__subtotal",
        "processedorders__report_type",
        "processedorders__country",
        "processedorders__hsn",
        "processedorders__plan",
        "processedorders__product",
    ]

    fy_field = "convertedpi__processed_at"

    def get_queryset(self):

        request = self.request
        profile = Profile.objects.select_related("user").get(user=request.user)

        queryset = (
            proforma.objects.select_related("convertedpi", "summary")
            .filter(convertedpi__is_processed=True, branch=profile.branch.id)
            .prefetch_related("orderlist", "processedorders")
        )

        if request.user.role != "admin" and request.user.department != "production":
            queryset = queryset.filter(user_id=request.user.id)

        fy = request.GET.get("fy", current_fy())
        if fy:
            queryset = self.fy_filter(request, queryset, fy)

        pending_month = request.GET.get("month", None)
        if pending_month:
            queryset = (
                queryset.filter(
                    processedorders__from_month__lte=pending_month,
                    processedorders__to_month__gte=pending_month,
                )
                .filter(
                    Q(processedorders__last_dispatch_month__lt=pending_month)
                    | Q(processedorders__last_dispatch_month__isnull=True)
                )
                .distinct()
            )

        return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def patch(self, request, id):
        try:
            orderInstance = get_object_or_404(processedOrder, pk=id)
            data = request.data
            serializer = ProcessedOrderSerializer(
                orderInstance, data=data, partial=True
            )
            if serializer.is_valid():
                serializer.save(partial=True)
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
            if not data:
                return Response(
                    {"message": "No processed orders provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                pi_instance.status != "closed"
                and pi_instance.convertedpi.is_processed == True
            ):
                return Response(
                    {"message": "You can not process this order."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = ProcessedOrderSerializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(pi_id=pi_instance)
            if convertedPiInstance:
                convertedPiInstance.is_processed = True
                convertedPiInstance.processed_at = timezone.now().date()
                convertedPiInstance.save()
            result = ProformaSerializer(pi_instance)
            return Response(result.data, status=status.HTTP_201_CREATED)
            # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("Error in processing PI:", e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RenewalPIView(ListAPIView):
    serializer_class = ProformaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PiPagination

    # Important: DO NOT USE PiFilters (causes get_object issues)
    filterset_class = PiFilters
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ["pi_no", "company_name"]  # optional
    search_fields = ["pi_no", "company_name"]  # optional

    def get_queryset(self):

        request = self.request

        user = request.user

        branch = user.profile.branch.id

        curr_month = timezone.now().month
        curr_year = timezone.now().year

        curr_index = curr_year * 12 + curr_month

        queryset = (
            proforma.objects.annotate(
                from_year_int=Cast(
                    Substr("processedorders__from_month", 1, 4), IntegerField()
                ),
                from_mon_int=Cast(
                    Substr("processedorders__from_month", 6, 2), IntegerField()
                ),
                to_year_int=Cast(
                    Substr("processedorders__to_month", 1, 4), IntegerField()
                ),
                to_mon_int=Cast(
                    Substr("processedorders__to_month", 6, 2), IntegerField()
                ),
                from_index=F("from_year_int") * 12 + F("from_mon_int"),
                to_index=F("to_year_int") * 12 + F("to_mon_int"),
                month_diff=F("to_index") - F("from_index"),
                # Boolean → INTEGER (SQL Server safe)
                order_can_renew_int=Case(
                    When(month_diff__gte=6, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            )
            .annotate(max_order_can_renew=Max("order_can_renew_int"))
            .annotate(
                canRenew=Case(
                    When(max_order_can_renew=1, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
            .distinct()
        )

        queryset = queryset.annotate(
            remaining_month=curr_index - F("to_index")
        ).filter(
            canRenew=True,
            status="closed",
            renewal_status = 'pending',
            remaining_month__gte=0,
            remaining_month__lte=6,
            branch=branch
        )

        if user.role != "admin":
            queryset = queryset.filter(user_id=user.id)

        return queryset


class EmailView(APIView):
    pass

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
