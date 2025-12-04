from django.utils.translation import gettext_lazy as _
from .models import *

DEFAULT_LABELS = {
    "CATEGORY": [
        ("offline", _("BE TRADE PUBLICATIONS")),
        ("online", _("beDATOS PORTAL")),
    ],
    "REPORT_TYPE": [
        ("export", _("Outbound Insight")),
        ("import", _("Inbound Insight")),
        ("online", _("Subscription")),
        ("domestic", _("Market Research")),
    ],
}


def get_label(branch, group, key_value):
    label = BranchLabel.objects.filter(
        branch=branch, group=group, key_value=key_value
    ).first()

    if label:
        return label.label

    return dict(DEFAULT_LABELS[group]).get(key_value, key_value)
