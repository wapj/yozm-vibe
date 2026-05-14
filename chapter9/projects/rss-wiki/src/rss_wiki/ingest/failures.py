FAILURE_THRESHOLD: int = 5


def is_failing(consecutive_failures: int, *, threshold: int = FAILURE_THRESHOLD) -> bool:
    return consecutive_failures >= threshold
