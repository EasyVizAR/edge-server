import datetime

from quart_rate_limiter import RateLimit, RateLimiter, rate_limit


# Main rate limiter that can be applied to all app routes
main_rate_limiter = RateLimiter(default_limits=[RateLimit(10, datetime.timedelta(seconds=1))])

# Function decorator that can be used on particularly expensive routes
rate_limit_expensive = rate_limit(1, datetime.timedelta(seconds=1))
