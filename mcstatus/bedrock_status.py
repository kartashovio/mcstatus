from __future__ import annotations

import asyncio
import socket
import struct
from time import perf_counter

import asyncio_dgram

from mcstatus.address import Address
from mcstatus.status_response import BedrockStatusResponse

# TODO Remove this useless __all__ after 2023-08
__all__ = ("BedrockServerStatus", "BedrockStatusResponse")


class BedrockServerStatus:
    request_status_data = (
        b"\x01\x00\x00\x00\x00\x00\xda\\\xb1\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x124Vxu4] \xf7B\xb9\xf4"
    )


    def __init__(self, address: Address, timeout: float = 3):
        self.address = address
        self.timeout = timeout

    @staticmethod
    def parse_response(data: bytes, latency: float) -> BedrockStatusResponse:
        data = data[1:]
        name_length = struct.unpack(">H", data[32:34])[0]
        decoded_data = data[34 : 34 + name_length].decode().split(";")

        return BedrockStatusResponse.build(decoded_data, latency)

    def read_status(self) -> BedrockStatusResponse:
        start = perf_counter()
        data = self._read_status()
        end = perf_counter()
        return self.parse_response(data, (end - start) * 1000)

    def _read_status(self) -> bytes:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(self.timeout)

        s.sendto(self.request_status_data, self.address)
        data, _ = s.recvfrom(2048)

        return data

    async def read_status_async(self) -> BedrockStatusResponse:
        start = perf_counter()
        data = await self._read_status_async()
        end = perf_counter()

        return self.parse_response(data, (end - start) * 1000)

    async def _read_status_async(self) -> bytes:
        stream = None
        try:
            conn = asyncio_dgram.connect(self.address)
            stream = await asyncio.wait_for(conn, timeout=self.timeout)

            await asyncio.wait_for(stream.send(self.request_status_data), timeout=self.timeout)
            data, _ = await asyncio.wait_for(stream.recv(), timeout=self.timeout)
        finally:
            if stream is not None:
                stream.close()

        return data
