from typing import Any
from nightcrawler.helpers.utils import create_output_dir
from nightcrawler.settings import Settings
from datetime import datetime

try:
    from libnightcrawler.context import Context as StorageContext
except ImportError:
    StorageContext = object


class Context(StorageContext):
    """
    Context class that holds configuration options for the application.

    Attributes:
        settings (Settings): An instance of the Settings class that holds application-specific settings.
        output_path (str): The directory path where output files will be saved.
        serpapi_filename (str): The filename for storing URLs retrieved from Serpapi, including a timestamp.
        zyte_filename (str): The filename for storing URLs retrieved from zyte, including a timestamp.
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Initializes the Context with default configuration options.

        Args:
            **kwargs (Any): Additional keyword arguments that might be used to customize the context.
        """
        super().__init__()
        self.settings = Settings()
        self.today = datetime.now()
        self.today_ts = self.today.strftime("%Y-%m-%d_%H-%M-%S")
        self.crawlStatus: str = "processing"

        from nightcrawler.base import Organization

        self.organizations = Organization.get_all()

        # ----------------------------------------------------------------------------------------
        # Scraping
        # ----------------------------------------------------------------------------------------
        self.output_path: str = "./data/output"
        self.serpapi_filename_keyword_enrichement: str = (
            "extract_keyword_enrichement.json"
        )
        self.serpapi_filename_google_lens_search: str = (
            "extract_serpapi_google_lens_search.json"
        )
        self.serpapi_filename: str = "extract_serpapi_keywords.json"
        self.zyte_filename: str = "extract_zyte.json"
        # ----------------------------------------------------------------------------------------
        # Processing
        # ----------------------------------------------------------------------------------------
        self.filename_final_results: str = "results.json"

    def update_output_dir(self, path: str):
        self.output_dir = create_output_dir(
            path, self.output_path, skip=not self.settings.use_file_storage
        )

    def get_crawl_requests(self, **kwargs):
        """
        Add pipeline organization attributes to database organization attributes

        Attributes:
            **kwargs (Any): Arguments forwarded to base class.
        """
        requests = super().get_crawl_requests(**kwargs)
        for request in requests:
            org = self.organizations[request.organization.name]
            org.blacklist = request.organization.blacklist
            org.whitelist = request.organization.whitelist
            request.organization = org
        return requests
