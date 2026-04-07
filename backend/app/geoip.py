"""Network IDS Dashboard — GeoIP resolution.

Resolves source IP addresses to geographic coordinates using
the MaxMind GeoLite2-City database. Falls back gracefully when
the database file is not available.
"""

import logging
from ipaddress import ip_address

import geoip2.database
from geoip2.errors import AddressNotFoundError

from app.config import settings
from app.models import SourceLocation

logger = logging.getLogger(__name__)


class GeoIpResolver:
    """Resolves IP addresses to geographic locations via MaxMind GeoLite2.

    Handles private/loopback IPs with a synthetic "Lab Network" location
    and gracefully degrades when the database file is missing.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._reader: geoip2.database.Reader | None = None
        self._initialized = False

    def _reader_or_none(self) -> geoip2.database.Reader | None:
        """Lazy-load the GeoIP database reader."""
        if not self._initialized:
            self._initialized = True
            try:
                self._reader = geoip2.database.Reader(self.db_path)
                logger.info("GeoIP database loaded from %s", self.db_path)
            except FileNotFoundError:
                logger.warning(
                    "GeoIP database not found at %s — geographic resolution disabled. "
                    "Download GeoLite2-City.mmdb and place it in the data/ directory.",
                    self.db_path,
                )
                self._reader = None
        return self._reader

    def resolve(self, source_ip: str) -> SourceLocation:
        """Resolve an IP address to a geographic location.

        Args:
            source_ip: The IP address string to resolve.

        Returns:
            A SourceLocation with geographic data, or defaults if resolution fails.
        """
        ip = ip_address(source_ip)
        if ip.is_private or ip.is_loopback:
            return SourceLocation(
                source_ip=source_ip,
                country="Lab Network",
                city="Sandbox",
                latitude=0.0,
                longitude=0.0,
            )

        reader = self._reader_or_none()
        if reader is None:
            return SourceLocation(source_ip=source_ip)

        try:
            result = reader.city(source_ip)
        except AddressNotFoundError:
            return SourceLocation(source_ip=source_ip)

        return SourceLocation(
            source_ip=source_ip,
            country=result.country.name,
            city=result.city.name,
            latitude=result.location.latitude,
            longitude=result.location.longitude,
        )

    def close(self) -> None:
        """Close the GeoIP database reader and release resources."""
        if self._reader is not None:
            self._reader.close()
            self._reader = None
            self._initialized = False
            logger.info("GeoIP database reader closed.")


geoip_resolver = GeoIpResolver(settings.geoip_db_path)
