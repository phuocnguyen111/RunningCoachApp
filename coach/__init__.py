import logging

from flask import Flask

from .config import Config
from .plans import PlanCatalog
from .repo import AthleteRepo, GroupRepo
from .store import JsonStore
from .uploads import UploadService


class Services:
    def __init__(self, config):
        self.config = config
        self.catalog = PlanCatalog(config.plans_dir)
        self.store = JsonStore(config.data_dir)
        self.groups = GroupRepo(self.store, self.catalog)
        self.athletes = AthleteRepo(self.store, self.groups)
        self.uploads = UploadService(config, self.catalog, self.groups, self.athletes)

    def startup(self):
        self.uploads.cleanup_expired()


def create_app(config=None):
    from pathlib import Path

    from .web.routes_api import register_api_routes
    from .web.routes_pages import register_page_routes

    config = config or Config(base_dir=Path(__file__).resolve().parent.parent)
    root = Path(__file__).resolve().parent.parent
    app = Flask(__name__, template_folder=str(root / "templates"), static_folder=str(root / "static"))
    app.config["MAX_CONTENT_LENGTH"] = config.max_upload_bytes
    app.config["JSON_AS_ASCII"] = False
    app.json.ensure_ascii = False
    app.extensions["coach"] = Services(config)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    register_api_routes(app)
    register_page_routes(app)
    return app
