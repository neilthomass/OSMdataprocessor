import logging
import os
import io
import gzip
import math
import zipfile
from datetime import date, timedelta
from typing import Any, Generator, Optional

import pandas as pd
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)

_IMPORTED_FOLDER = ".imported"


def get_imported_folder_path() -> str:
    return _IMPORTED_FOLDER


def set_imported_folder_path(new_path: str) -> None:
    global _IMPORTED_FOLDER
    _IMPORTED_FOLDER = new_path


def date_range(start: date, end: date) -> Generator[date, Any, None]:
    for n in range(int((end - start).days) + 1):
        yield start + timedelta(n)


def filename_to_date(filename: str) -> date:
    parts = filename.split('.')[0].split('_')[-3:]
    return date(int(parts[0]), int(parts[1]), int(parts[2]))


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class PeMSConnection(metaclass=Singleton):
    """Handle authenticated requests to the PeMS clearinghouse."""

    SITE_URL = "http://pems.dot.ca.gov/"

    def __init__(self) -> None:
        self._username: Optional[str] = None
        self.session: Optional[requests.Session] = None
        self._chunk_urls: dict[str, str] = {}

    @staticmethod
    def initialize(username: str, password: str) -> None:
        PeMSConnection()._create_new_session(username=username, password=password)

    @property
    def initialized(self) -> bool:
        return self.session is not None

    def destroy(self) -> None:
        self.session = None
        self._username = None

    def _create_new_session(self, username: str, password: str) -> None:
        self.session = requests.Session()
        self.session.get(self.SITE_URL)
        resp = self.session.post(self.SITE_URL, data={
            "username": username,
            "password": password,
            "login": "Login",
        })
        if "Incorrect username or password" in resp.text:
            self.session = None
            logger.error("Incorrect PeMS credentials")
        else:
            self._username = username
            logger.info("PeMSConnection initialized")

    def download(self, url: str, file_path: Optional[str] = None) -> io.BytesIO:
        if not self.initialized:
            raise RuntimeError("PeMSConnection not initialized")
        if url is None:
            raise ValueError("Missing URL")

        r = self.session.get(url, stream=True)
        buffer = io.BytesIO()
        total_size = int(r.headers.get("content-length", 0))
        block_size = 1024
        wrote = 0
        for data in tqdm(r.iter_content(block_size), total=math.ceil(total_size // block_size), unit="KB", unit_scale=True):
            wrote += len(data)
            buffer.write(data)
        if file_path:
            with open(file_path, "wb+") as f:
                f.write(buffer.getvalue())
        if total_size != 0 and wrote != total_size:
            logger.error("Download truncated: %s", url)
        return buffer

    def get_url(self, data_type: str, chunk_date: date, url_parser, district: int | None = None) -> Optional[str]:
        if district is None:
            district = "all"
        url_id = f"{data_type}_{chunk_date}_{district}"
        if url_id in self._chunk_urls:
            return self.SITE_URL + self._chunk_urls[url_id][1:]

        params = {
            "srq": "clearinghouse",
            "yy": chunk_date.year,
            "type": data_type,
            "returnformat": "text",
            "district_id": district,
        }
        data = self.session.get(self.SITE_URL, params=params).json()
        if not isinstance(data, dict) or "data" not in data:
            logger.warning("Missing data for %s", url_id)
            return None
        self._chunk_urls.update(url_parser(data["data"], district))
        if url_id not in self._chunk_urls:
            logger.warning("No url for %s", url_id)
            return None
        return self.SITE_URL + self._chunk_urls[url_id][1:]


class DataSourceHandler(metaclass=abc.ABCMeta):
    def __init__(self, use_cache: bool = False) -> None:
        self.use_cache = use_cache

    @property
    def path(self) -> str:
        return os.path.join(os.getcwd(), get_imported_folder_path(), self.name)

    def load_between(self, from_date: date, to_date: date, district: int | None = None):
        os.makedirs(self.path, exist_ok=True)
        for chunk_date in self._chunk_dates(from_date, to_date):
            yield self._load_chunk_date(chunk_date, district=district)

    def _load_chunk_date(self, chunk_date: date, district: int | None):
        file_path = self._file_path(chunk_date, district)
        if os.path.exists(file_path) and self.use_cache:
            logger.info("Loading from cache: %s", file_path)
            return self._load_file(file_path)
        logger.info("Downloading %s for %s", self.name, chunk_date)
        buffer = self._download_chunk(chunk_date, file_path if self.use_cache else None, district)
        if buffer is None:
            logger.error("Missing chunk for %s at %s", self.name, chunk_date)
            return None
        chunk = self._load_file(buffer)
        buffer.close()
        return chunk

    def _file_path(self, chunk_date: date, district: int | None) -> str:
        year = chunk_date.year
        month = str(chunk_date.month).zfill(2)
        day = str(chunk_date.day).zfill(2)
        district = "all" if district is None else str(district).zfill(3)
        return os.path.join(self.path, f"{self.name}_{year}_{month}_{day}_d{district}.txt.gz")

    def _download_chunk(self, chunk_date: date, file_path: str | None, district: int | None):
        url = PeMSConnection().get_url(self.name, chunk_date, self._url_parser, district)
        if not url:
            return None
        return PeMSConnection().download(url, file_path)

    @abc.abstractmethod
    def _chunk_dates(self, start: date, end: date) -> Generator[date, Any, None]:
        ...

    @abc.abstractmethod
    def _url_parser(self, url_list, district):
        ...

    @abc.abstractmethod
    def _load_file(self, file_or_buffer) -> pd.DataFrame:
        ...

    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...


class Station5MinDataHandler(DataSourceHandler):
    def _chunk_dates(self, start: date, end: date) -> Generator[date, Any, None]:
        return date_range(start, end)

    def _url_parser(self, url_list, district):
        processed_urls = {}
        for monthly_data in url_list.items():
            for recorded_day in monthly_data[1]:
                recorded_date = filename_to_date(recorded_day["file_name"])
                processed_urls[f"{self.name}_{recorded_date}_{district}"] = recorded_day["url"]
        return processed_urls

    def _load_file(self, file_or_buffer) -> Optional[pd.DataFrame]:
        try:
            if isinstance(file_or_buffer, io.BytesIO):
                file_or_buffer.seek(0)
                zip_file = gzip.GzipFile(fileobj=file_or_buffer)
            else:
                zip_file = gzip.GzipFile(file_or_buffer)
            df = pd.read_csv(zip_file, header=None, index_col=False, parse_dates=[0], infer_datetime_format=True)
            cols = [
                'timestamp', 'station_id', 'district', 'fwy_no', 'dir', 'lane_type',
                'station_length', 'sample_no', 'obs_percentage', 'total_flow',
                'avg_occupancy', 'avg_speed'
            ]
            for i in range(0, int((len(df.columns) - 12) / 5)):
                cols += [f'lane_{i}_samples', f'lane_{i}_flow', f'lane_{i}_avg_occ', f'lane_{i}_avg_speed', f'lane_{i}_observed']
            df.columns = cols
            return df
        except zipfile.BadZipFile as err:
            logger.error("Could not unzip data: %s", err)
            return None

    @property
    def name(self) -> str:
        return "station_5min"


class OneStation5MinDataHandler(Station5MinDataHandler):
    def __init__(self, station_id: int, **kwargs) -> None:
        self.station_id = station_id
        super().__init__(**kwargs)

    def _load_file(self, file_or_buffer) -> Optional[pd.DataFrame]:
        try:
            if isinstance(file_or_buffer, io.BytesIO):
                file_or_buffer.seek(0)
            sid_bytes = bytes(str(self.station_id), "utf-8")
            result = []
            with gzip.open(file_or_buffer) as f:
                for line in f:
                    if line.split(b",")[1] == sid_bytes:
                        result.append(line)
            if not result:
                logger.error("No data for station %s in chunk", self.station_id)
                return None
            df = pd.read_csv(io.BytesIO(b"".join(result)), header=None, index_col=False, parse_dates=[0], infer_datetime_format=True)
            cols = [
                'timestamp', 'station_id', 'district', 'fwy_no', 'dir', 'lane_type',
                'station_length', 'sample_no', 'obs_percentage', 'total_flow',
                'avg_occupancy', 'avg_speed'
            ]
            for i in range(0, int((len(df.columns) - 12) / 5)):
                cols += [f'lane_{i}_samples', f'lane_{i}_flow', f'lane_{i}_avg_occ', f'lane_{i}_avg_speed', f'lane_{i}_observed']
            df.columns = cols
            return df
        except zipfile.BadZipFile as err:
            logger.error("Could not unzip data: %s", err)
            return None
