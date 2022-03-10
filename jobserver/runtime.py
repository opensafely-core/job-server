import attr


def less_than_60(instance, attribute, value):
    if value > 59:
        raise ValueError(f"{attribute} should be less than 60")


@attr.s
class Runtime:
    hours: int = attr.ib(default=0)
    minutes: int = attr.ib(default=0, validator=[less_than_60])
    seconds: int = attr.ib(default=0, validator=[less_than_60])
    total_seconds: int = attr.ib(default=0)

    def __bool__(self):
        if self.hours == 0 and self.minutes == 0 and self.seconds == 0:
            return False

        return True

    def __str__(self):
        if not self:
            return "-"

        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}"
