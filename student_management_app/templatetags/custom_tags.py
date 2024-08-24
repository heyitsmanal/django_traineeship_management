from django import template

register = template.Library()

@register.filter
def add_css_class(field, css_class):
    """
    Adds a CSS class to a form field.
    """
    # If the field is a string, just return it with the class added
    if isinstance(field, str):
        return f'{field} class="{css_class}"'

    # For Django form fields (widgets), modify the HTML attribute
    try:
        attrs = field.field.widget.attrs.copy()
        classes = attrs.get('class', '')
        if classes:
            attrs['class'] = f'{classes} {css_class}'
        else:
            attrs['class'] = css_class
        field.field.widget.attrs.update(attrs)
        return field
    except AttributeError:
        # If the field does not have widget.attrs, return it as is
        return field
