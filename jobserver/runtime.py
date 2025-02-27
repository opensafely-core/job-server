from dataclasses import dataclass


@dataclass(frozen=True)
class Runtime:
    hours: int = 0
    minutes: int = 0
    seconds: int = 0
    total_seconds: int = 0

    def __bool__(self):
        if self.hours == 0 and self.minutes == 0 and self.seconds == 0:
            return False

        return True

    def __str__(self):
        if not self:
            return "-"

        return f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}"

    def _less_than_60(self, attribute, value):
        if value > 59:
            raise ValueError(f"{attribute} should be less than 60")

    def __post_init__(self):
        self._less_than_60("minutes", self.minutes)
        self._less_than_60("seconds", self.seconds)
