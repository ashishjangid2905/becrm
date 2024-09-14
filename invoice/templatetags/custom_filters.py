from django import template
from datetime import datetime

register = template.Library()


@register.filter
def format_month(value):
    try:
        return datetime.strptime(value, '%Y-%m').strftime('%b-%y')
    except ValueError:
        return value
    
@register.filter
def total_month(from_month, to_month):
    try:
        from_m = datetime.strptime(from_month, '%Y-%m')
        to_m = datetime.strptime(to_month, '%Y-%m')
        return (to_m.year - from_m.year) * 12 + to_m.month - from_m.month + 1
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    try:
        return value*arg
    except (ValueError, TypeError):
        return 0
    
@register.simple_tag
def total_order_value(proforma):
    total_sum = 0
    for order in proforma.orderlist_set.all():
        total_sum += order.total_price
    return total_sum
    