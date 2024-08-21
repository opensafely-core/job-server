from dataclasses import dataclass


@dataclass
class LinkableObject:
    display_value: str
    link: str

    def __str__(self):
        return self.display_value

    @classmethod
    def build(cls, *, obj, field="", link_func=""):
        """
        Build a LinkableObject from the given object

        We have 3 states for any "object" tracked in an event:
         * unknown object -> keep as a string
         * known object -> use the given field, fall back to __str__
         * linked object -> we want to also link the object in the UI

        So that templates don't have to do much work to deal with these states
        we're doing it here, letting the templates rely on the str() of this
        object and check if they need to generate link markup.
        """
        if isinstance(obj, str):
            return cls(display_value=obj, link=None)

        try:
            display_value = getattr(obj, field)
        except AttributeError:
            display_value = str(obj)

        try:
            link = getattr(obj, link_func)()
        except AttributeError:
            link = None

        return cls(display_value=display_value, link=link)


@dataclass
class PresentableAuditableEvent:
    context: dict[str, str]
    template_name: str
