# -*- coding: utf-8 -*-
"""🍁 Bridge Deal & Auction Studio — English edition.

Logic lives in core.py; the Chinese edition is app.py.
Both editions share the same Google Drive webhook, so every exported PNG
lands in the same Drive folder.
"""

from core import run_app

run_app("en")
