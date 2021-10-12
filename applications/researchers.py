from django.forms.models import model_to_dict

from .forms import ResearcherRegistrationSubmissionForm


def build_researcher_form(researcher):
    """
    Create a bound ResearcherRegistrationSubmissionForm

    Errors can only be generated on a Django form once it is bound to data,
    which doesn't include a model instance in the case of a ModelForm.  This
    function takes the given ResearcherRegistration instance, creates a
    dictionary from it, and then builds the submission form with both that and
    the passed in instance.  We get fields defined from the the forms parent
    class, and a bound form which we can call is_valid() to get errors from.
    """
    data = model_to_dict(researcher)

    return ResearcherRegistrationSubmissionForm(data, instance=researcher)
