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

    def _valid_base_60(self, attribute):
        if getattr(self, attribute) > 59:
            raise ValueError(f"{attribute} should be < 60")

    def _valid_positive(self, attribute):
        if getattr(self, attribute) < 0:
            raise ValueError(f"{attribute} should be positive")

    # This validation being invariant relies on the dataclass being frozen.
    # If the dataclass objects are to be modified,
    # then this validation should also be checked on modification
    # (for example, with a property.setter).
    def __post_init__(self):
        for attribute in vars(self):
            self._valid_positive(attribute)
            if attribute not in ("hours", "total_seconds"):
                self._valid_base_60(attribute)
