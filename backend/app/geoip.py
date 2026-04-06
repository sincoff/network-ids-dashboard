from ipaddress import ip_address

import geoip2.database
from geoip2.errors import AddressNotFoundError

from app.config import settings
from app.models import SourceLocation


class GeoIpResolver:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._reader: geoip2.database.Reader | None = None

    def _reader_or_none(self) -> geoip2.database.Reader | None:
        if self._reader is None:
            try:
                self._reader = geoip2.database.Reader(self.db_path)
            except FileNotFoundError:
                self._reader = None
        return self._reader

    def resolve(self, source_ip: str) -> SourceLocation:
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
        if self._reader is not None:
            self._reader.close()
            self._reader = None


geoip_resolver = GeoIpResolver(settings.geoip_db_path)
