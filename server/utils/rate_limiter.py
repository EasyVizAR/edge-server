import datetime
import sys

from quart_rate_limiter import RateLimit, RateLimiter, rate_limit


# Detect if we are running under pytest and increase the rate limits.
# Otherwise, we would definitely trigger them.
multiplier = 1
if "pytest" in sys.modules:
    multiplier = 10


# Main rate limiter that can be applied to all app routes.
main_rate_limiter = RateLimiter(default_limits=[RateLimit(10*multiplier, datetime.timedelta(seconds=1))])

# Function decorator that can be used on particularly expensive routes
rate_limit_expensive = rate_limit(1*multiplier, datetime.timedelta(seconds=1))
