from collections import deque
from collections.abc import Callable
from math import ceil
from threading import Lock
from time import monotonic


class LoginRateLimiter:
    """
    In-process failed-login rate limiter.

    Tracks failures by:

    1. Client IP
    2. Client IP + normalized email

    This implementation is appropriate for the
    current single-process ChargeOps environment.

    Multi-worker production deployment should use
    shared rate-limit storage such as Redis or an
    API gateway.
    """

    def __init__(
        self,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._clock = clock

        self._ip_failures: dict[
            str,
            deque[float],
        ] = {}

        self._account_failures: dict[
            tuple[str, str],
            deque[float],
        ] = {}

        self._lock = Lock()

        self._last_cleanup = (
            self._clock()
        )

    @staticmethod
    def _prune_attempts(
        attempts: deque[float],
        now: float,
        window_seconds: int,
    ) -> None:
        cutoff = (
            now
            - window_seconds
        )

        while (
            attempts
            and attempts[0] <= cutoff
        ):
            attempts.popleft()

    def _cleanup_expired(
        self,
        now: float,
        window_seconds: int,
    ) -> None:
        if (
            now - self._last_cleanup
            < window_seconds
        ):
            return

        expired_ips: list[str] = []

        for (
            client_ip,
            attempts,
        ) in self._ip_failures.items():
            self._prune_attempts(
                attempts=attempts,
                now=now,
                window_seconds=(
                    window_seconds
                ),
            )

            if not attempts:
                expired_ips.append(
                    client_ip
                )

        for client_ip in expired_ips:
            self._ip_failures.pop(
                client_ip,
                None,
            )

        expired_accounts: list[
            tuple[str, str]
        ] = []

        for (
            account_key,
            attempts,
        ) in (
            self
            ._account_failures
            .items()
        ):
            self._prune_attempts(
                attempts=attempts,
                now=now,
                window_seconds=(
                    window_seconds
                ),
            )

            if not attempts:
                expired_accounts.append(
                    account_key
                )

        for account_key in (
            expired_accounts
        ):
            self._account_failures.pop(
                account_key,
                None,
            )

        self._last_cleanup = now

    @staticmethod
    def _calculate_retry_after(
        attempts: deque[float],
        limit: int,
        now: float,
        window_seconds: int,
    ) -> int | None:
        if len(attempts) < limit:
            return None

        remaining = (
            window_seconds
            - (
                now
                - attempts[0]
            )
        )

        return max(
            1,
            ceil(
                remaining
            ),
        )

    def get_retry_after(
        self,
        *,
        client_ip: str,
        email: str,
        ip_attempt_limit: int,
        account_attempt_limit: int,
        window_seconds: int,
    ) -> int | None:
        now = self._clock()

        account_key = (
            client_ip,
            email,
        )

        with self._lock:
            self._cleanup_expired(
                now=now,
                window_seconds=(
                    window_seconds
                ),
            )

            ip_attempts = (
                self._ip_failures.get(
                    client_ip
                )
            )

            if ip_attempts is None:
                ip_attempts = deque()

            else:
                self._prune_attempts(
                    attempts=ip_attempts,
                    now=now,
                    window_seconds=(
                        window_seconds
                    ),
                )

            account_attempts = (
                self
                ._account_failures
                .get(
                    account_key
                )
            )

            if account_attempts is None:
                account_attempts = (
                    deque()
                )

            else:
                self._prune_attempts(
                    attempts=(
                        account_attempts
                    ),
                    now=now,
                    window_seconds=(
                        window_seconds
                    ),
                )

            retry_values: list[int] = []

            ip_retry = (
                self
                ._calculate_retry_after(
                    attempts=ip_attempts,
                    limit=(
                        ip_attempt_limit
                    ),
                    now=now,
                    window_seconds=(
                        window_seconds
                    ),
                )
            )

            if ip_retry is not None:
                retry_values.append(
                    ip_retry
                )

            account_retry = (
                self
                ._calculate_retry_after(
                    attempts=(
                        account_attempts
                    ),
                    limit=(
                        account_attempt_limit
                    ),
                    now=now,
                    window_seconds=(
                        window_seconds
                    ),
                )
            )

            if (
                account_retry
                is not None
            ):
                retry_values.append(
                    account_retry
                )

            if not retry_values:
                return None

            return max(
                retry_values
            )

    def record_failure(
        self,
        *,
        client_ip: str,
        email: str,
        window_seconds: int,
    ) -> None:
        now = self._clock()

        account_key = (
            client_ip,
            email,
        )

        with self._lock:
            self._cleanup_expired(
                now=now,
                window_seconds=(
                    window_seconds
                ),
            )

            ip_attempts = (
                self
                ._ip_failures
                .setdefault(
                    client_ip,
                    deque(),
                )
            )

            self._prune_attempts(
                attempts=ip_attempts,
                now=now,
                window_seconds=(
                    window_seconds
                ),
            )

            ip_attempts.append(
                now
            )

            account_attempts = (
                self
                ._account_failures
                .setdefault(
                    account_key,
                    deque(),
                )
            )

            self._prune_attempts(
                attempts=(
                    account_attempts
                ),
                now=now,
                window_seconds=(
                    window_seconds
                ),
            )

            account_attempts.append(
                now
            )

    def clear_account_failures(
        self,
        *,
        client_ip: str,
        email: str,
    ) -> None:
        account_key = (
            client_ip,
            email,
        )

        with self._lock:
            self._account_failures.pop(
                account_key,
                None,
            )

    def reset(
        self,
    ) -> None:
        """
        Clear rate-limit state.

        Used primarily by automated tests.
        """

        with self._lock:
            self._ip_failures.clear()
            self._account_failures.clear()

            self._last_cleanup = (
                self._clock()
            )


login_rate_limiter = (
    LoginRateLimiter()
)