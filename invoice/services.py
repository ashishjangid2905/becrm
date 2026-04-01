from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from .models import *
from .serializers import *


def _check_approval_permission(proforma, user):

    pi_user = get_object_or_404(User, pk=proforma.user_id)
    owner_group = set(pi_user.groups.values_list("name", flat=True))
    approver_group = set(user.groups.values_list("name", flat=True))

    can_approve = (
        "Head" in approver_group
        or ("VP" in approver_group and "Head" not in owner_group)
        or (
            "Sr. Executive" in approver_group
            and not owner_group.intersection({"VP", "Head"})
        )
    )

    if not can_approve:
        raise PermissionDenied("You are not authorised to approve this proforma")


def _approve_proforma(proforma, user):
    now = timezone.now()

    proforma.approval_status = "approved"
    proforma.is_Approved = True
    proforma.feedback = None
    proforma.approved_by = user.id
    proforma.approved_at = now

    proforma.save(
        update_fields=[
            "approval_status",
            "is_Approved",
            "feedback",
            "approved_by",
            "approved_at",
        ]
    )


def _send_feedback(proforma, user, feedback):
    now = timezone.now()

    proforma.approval_status = "feedback"
    proforma.is_Approved = False
    proforma.feedback = feedback
    proforma.approved_by = user.id
    proforma.approved_at = now

    proforma.save(
        update_fields=[
            "approval_status",
            "is_Approved",
            "feedback",
            "approved_by",
            "approved_at",
        ]
    )


def handle_proforma_approval(proforma, decision, decided_by, feedback=None):
    """
    Handles approval logic for a proforma invoice.
    Backward compatible:
    - Uses approval_status (new)
    - Keeps is_Approved in sync (legacy)
    """

    _check_approval_permission(proforma, decided_by)

    if decision == "approve":
        _approve_proforma(proforma, decided_by)
    if decision == "feedback":
        if not feedback:
            raise ValidationError("Feedback is required")
        _send_feedback(proforma, decided_by, feedback)

    return proforma


def _handle_closed(proforma, data, user):
    if not data:
        raise ValidationError("Payment details are required to close Proforma")

    converted_pi, _ = convertedPI.objects.get_or_create(
        pi_id=proforma, defaults={"branch": proforma.branch}
    )

    converted_pi.is_closed = True
    converted_pi.is_cancel = False
    converted_pi.is_hold = False
    converted_pi.updated_by = user.id

    _update_payment_fields(converted_pi, data)

    converted_pi.save()


def _update_payment_fields(converted_pi, data):
    allowed_fields = {
        "payment_status",
        "payment1_date",
        "payment1_amt",
        "payment2_date",
        "payment2_amt",
        "payment3_date",
        "payment3_amt",
        "invoice_date",
        "invoice_number",
        "irn",
        "is_taxInvoice",
        "is_invoiceRequire",
    }

    for field in allowed_fields:
        if field in data:
            setattr(converted_pi, field, data[field])


def _handle_open_or_lost(proforma, status, data, user):
    if not data:
        return

    converted_pi = get_object_or_404(convertedPI, pi_id=proforma.id)

    _update_payment_fields(converted_pi, data)

    if status == "open":
        converted_pi.is_hold = True
        converted_pi.is_closed = False

    elif status == "lost":
        converted_pi.is_invoiceRequire = False
        converted_pi.is_closed = False
        converted_pi.is_hold = True
        converted_pi.is_cancel = True

    converted_pi.updated_by = user.id
    converted_pi.save()


@transaction.atomic
def handle_proforma_status_change(
    proforma, status: str, user, converted_pi_data: dict | None = None
    ):
    """
    Handles proforma status changes and synchronizes ConvertedPI.
    """

    # Update proforma fields
    proforma.status = status
    proforma.edited_by = user.id
    if status == "closed":
        proforma.closed_at = timezone.now().date()

    proforma.save(update_fields=["status", "edited_by", "closed_at"])

    # ConvertedPI handling
    if status == "closed":
        _handle_closed(proforma, converted_pi_data, user)
    
    elif status in {"open", "lost"}:
        _handle_open_or_lost(proforma, status, converted_pi_data, user)

    return proforma

