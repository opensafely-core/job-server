import attr


def less_than_60(instance, attribute, value):
    if value > 59:
        raise ValueError(f"{attribute} should be less than 60")


@attr.s
class Runtime:
    hours: int = attr.ib(default=0)
    minutes: int = attr.ib(default=0, validator=[less_than_60])
    seconds: int = attr.ib(default=0, validator=[less_than_60])
