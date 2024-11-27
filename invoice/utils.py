from django.utils.translation import gettext_lazy as _

STATUS_CHOICES = {
    ('open', _('OPEN')),
    ('closed', _('CLOSED')),
    ('lost', _('LOST')),
}

SUBSCRIPTION_MODE = {
    ('email', _('EMAIL')),
    ('online', _('ONLINE')),
}

PAYMENT_TERM = {
    ('advance', _('ADVANCED')),
    ('credit', _('CREDIT')),
}

CATEGORY = {
    ('offline', _('BE USA TRADE PUBLICATIONS')),
    ('online', _('BE USA TRADE SUBSCRIPTION'))
}

REPORT_TYPE = {
    ('export', _('Outbound Insight')),
    ('import', _('Inbound Insight')),
    ('online', _('Subscription')),
    ('domestic', _('Market Research')),
}

REPORTS = {
    ('export', _('EXPORT')),
    ('import', _('IMPORT')),
}

REPORT_FORMAT ={
    ('monthly', _('Monthly')),
    ('weekly', _('weekly')),
    ('10 days', _('10 Days')),
    ('sez', _('SEZ')),
    ('sez(weekly)', _('SEZ (Weekly)')),
    ('incoterm', _('Incoterm')),
}


ORDER_STATUS = {
    ('complete', _('Complete')),
    ('pending', _('Pending')),
}

PAYMENT_STATUS = {
    ('full', _('Full')),
    ('credit', _('Credit')),
    ('partial', _('Partial')),
}


COUNTRY_CHOICE ={
    ('IN', _('INDIA')),
    ('US', _('UNITED STATES')),
}



STATE_CHOICE = {
    (1, 'JAMMU AND KASHMIR'),
    (2, 'HIMACHAL PRADESH'),
    (3, 'PUNJAB'),
    (4, 'CHANDIGARH'),
    (5, 'UTTARAKHAND'),
    (6, 'HARYANA'),
    (7, 'DELHI'),
    (8, 'RAJASTHAN'),
    (9, 'UTTAR PRADESH'),
    (10, 'BIHAR'),
    (11, 'SIKKIM'),
    (12, 'ARUNACHAL PRADESH'),
    (13, 'NAGALAND'),
    (14, 'MANIPUR'),
    (15, 'MIZORAM'),
    (16, 'TRIPURA'),
    (17, 'MEGHALAYA'),
    (18, 'ASSAM'),
    (19, 'WEST BENGAL'),
    (20, 'JHARKHAND'),
    (21, 'ODISHA'),
    (22, 'CHATTISGARH'),
    (23, 'MADHYA PRADESH'),
    (24, 'GUJARAT'),
    (26, 'DADRA AND NAGAR HAVELI AND DAMAN AND DIU (NEWLY MERGED UT)'),
    (27, 'MAHARASHTRA'),
    (28, 'ANDHRA PRADESH(BEFORE DIVISION)'),
    (29, 'KARNATAKA'),
    (30, 'GOA'),
    (31, 'LAKSHADWEEP'),
    (32, 'KERALA'),
    (33, 'TAMIL NADU'),
    (34, 'PUDUCHERRY'),
    (35, 'ANDAMAN AND NICOBAR ISLANDS'),
    (36, 'TELANGANA'),
    (37, 'ANDHRA PRADESH (NEWLY ADDED)'),
    (38, 'LADAKH (NEWLY ADDED)'),
    (97, 'OTHER TERRITORY'),
    (99, 'CENTRE JURISDICTION')
    }