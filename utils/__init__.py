# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#
from datetime import datetime

import babel
import dateutil


def format_datetime(value, format='medium'):
    # convert only if value is not a datetime object
    if not isinstance(value, datetime):
        date = dateutil.parser.parse(value)
    else:
        date = value

    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')
