from django.utils.translation import gettext_lazy as _
from invoice.utils import STATE_CHOICE, COUNTRY_CHOICE
import re

STATUS = [
    ('new lead', _('New Lead')),
    ('hot lead', _('Hot Lead')),
    ('client', _('Client')),
    ('not interest', _('Not Interested')),
    ('lost', _('Lost')),
]


def update_lead_full_address(lead):
    state_val = lead.state
    if isinstance(state_val, int) or (isinstance(state_val, str) and state_val.isdigit()):
        state_name = dict(STATE_CHOICE).get(int(state_val), state_val)
    else:
        state_name = state_val  # fallback if already a string name
    country = dict(COUNTRY_CHOICE).get(lead.country, lead.country)

    address_parts = [
        lead.address1,
        lead.address2,
        lead.city,
        lead.pincode,
        state_name,
        country,
    ]
    full_address = ", ".join(filter(None, address_parts)).replace(",,", ",")

    lead.full_address = re.sub(r",\s*,+", ", ", full_address)
    lead.save()