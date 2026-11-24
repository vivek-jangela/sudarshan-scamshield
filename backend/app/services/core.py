"""Loads the SATARK NETRA engine modules (they use flat imports, so their folder is put on sys.path)."""
import sys
from .. import config

if str(config.CORE_DIR) not in sys.path:
    sys.path.insert(0, str(config.CORE_DIR))

import engine              # noqa: E402  message / url / website / apk fusion engine
import url_features        # noqa: E402  rule-based URL risk + identifier extractor
import url_intelligence    # noqa: E402  domain age, redirects, SSL (needs internet)
import website_analyzer    # noqa: E402
import apk_analyzer        # noqa: E402


def warm_up():
    """Load the pickled message model once at start-up so the first request is fast."""
    engine._msg()
