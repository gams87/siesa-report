from django import template

register = template.Library()


@register.filter
def get_item(queryset_or_dict, key):
    """Get an item from a dictionary or QuerySet using a variable key."""
    if queryset_or_dict is None:
        return None

    # Si es un diccionario
    if isinstance(queryset_or_dict, dict):
        return queryset_or_dict.get(key)

    # If it is a QuerySet or list of objects
    try:
        for item in queryset_or_dict:
            if hasattr(item, "column_id") and item.column_id == key:
                return item.display_name
            elif hasattr(item, "id") and item.id == key:
                return item
        return None
    except (TypeError, AttributeError):
        return None


@register.simple_tag
def get_item_or(dictionary, key, default=""):
    """Get an item from a dictionary with a default value."""
    if dictionary is None:
        return default
    return dictionary.get(key, default)


@register.simple_tag
def get_queryset_value(queryset, lookup_field, lookup_value, return_field, default=""):
    """
    Get a value from a queryset by matching a field.

    Args:
        queryset: The queryset to search
        lookup_field: The field name to match (e.g., 'column_id')
        lookup_value: The value to match
        return_field: The field name to return (e.g., 'display_name')
        default: Default value if not found

    Example:
        {% get_queryset_value report_columns 'column_id' column.id 'display_name' column.column_name %}
    """
    if queryset is None:
        return default

    try:
        for item in queryset:
            if hasattr(item, lookup_field) and getattr(item, lookup_field) == lookup_value:
                return getattr(item, return_field, default)
        return default
    except (TypeError, AttributeError):
        return default
