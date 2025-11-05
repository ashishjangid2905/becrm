from django.db.models import Q
from .custom_utils import current_fy, fy_date_range


class DynamicPiFilterMixin:

    fy_field = None
    alt_fy_field = None

    def fy_filter(self, request, queryset, fy=current_fy()):
        # fy = request.query_params.get("fy", current_fy())
        if not fy:
            return queryset
        start, end = fy_date_range(fy)

        filters = Q()
        if self.fy_field:
            filters |= Q(**{f"{self.fy_field}__range": (start, end)})
        if self.alt_fy_field:
            filters |= Q(**{f"{self.alt_fy_field}__range": (start, end)})

        return queryset.filter(filters)

