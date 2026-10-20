"""Site-wide settings."""

from __future__ import annotations

import os

# Google Analytics 4 Measurement ID. It is public and starts with "G-".
# Leave it empty to turn analytics off: no banner is shown and nothing
# loads from Google. The environment variable overrides the value below.
GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "")
