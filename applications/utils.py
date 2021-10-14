from django.template.defaultfilters import yesno


def value_for_presentation(value):
    """Convert a value ready for presentation in a template"""
    # we only deal with values that are the literals True, False, & None
    # currently.
    if value not in [True, False, None]:
        return value

    # Use Django's yesno template filter to map:
    #  * True->Yes
    #  * False->No
    #  * None->"" (empty string)
    return yesno(value, "Yes,No,")
