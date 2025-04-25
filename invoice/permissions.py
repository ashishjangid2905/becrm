from rest_framework.permissions import BasePermission
from .decorators import can_approve_proforma


class Can_Approve(BasePermission):

    def has_permission(self, request, view):
        return can_approve_proforma(request.user)
    
class Can_Generate_TaxInvoice(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'admin' or request.user.department == 'accounts'