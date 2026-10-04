from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from flask import Blueprint, current_app, render_template

bp = Blueprint("frontend", __name__)


@lru_cache(maxsize=None)
def _asset_version(path):
    return sha256(Path(path).read_bytes()).hexdigest()[:12]


@bp.route("/")
def index():
    # The app applies no-store and security headers to the rendered document.
    static_folder = Path(current_app.static_folder)
    return render_template(
        "index.html",
        css_version=_asset_version(static_folder / "dashboard.css"),
        js_version=_asset_version(static_folder / "dashboard.mjs"),
    )
