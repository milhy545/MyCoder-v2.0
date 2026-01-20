from mycoder.api_providers import CircuitBreaker, CircuitState


def test_circuit_breaker_opens_on_failures() -> None:
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

    assert breaker.state == CircuitState.CLOSED
    breaker.record_failure()
    assert breaker.state == CircuitState.CLOSED
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN


def test_circuit_breaker_half_open_after_timeout() -> None:
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN

    assert breaker.can_execute() is True
    assert breaker.state == CircuitState.HALF_OPEN


def test_circuit_breaker_closes_after_successes() -> None:
    breaker = CircuitBreaker(
        failure_threshold=1, recovery_timeout=0, half_open_max_calls=2
    )
    breaker.record_failure()
    breaker.can_execute()
    assert breaker.state == CircuitState.HALF_OPEN

    breaker.record_success()
    assert breaker.state == CircuitState.HALF_OPEN
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED
