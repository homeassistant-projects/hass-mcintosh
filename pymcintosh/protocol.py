"""McIntosh RS232/IP protocol implementation."""

import asyncio
import functools
import logging
import time
from typing import Optional

LOG = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 2.0


async def async_get_protocol(
    serial_port: str,
    min_time_between_commands: float,
    response_eol: str,
    serial_config: dict,
    loop,
):
    """Create async protocol for McIntosh communication."""

    def locked_method(method):
        """Decorator to ensure only one command is sent at a time."""
        @functools.wraps(method)
        async def wrapper(self, *method_args, **method_kwargs):
            async with self._lock:
                return await method(self, *method_args, **method_kwargs)

        return wrapper

    def ensure_connected(method):
        """Decorator to check connection before sending."""
        @functools.wraps(method)
        async def wrapper(self, *method_args, **method_kwargs):
            try:
                await asyncio.wait_for(self._connected.wait(), self._timeout)
            except Exception:
                LOG.debug(f'Timeout sending data to {self._serial_port}, no connection')
                return
            return await method(self, *method_args, **method_kwargs)

        return wrapper

    class McIntoshProtocol(asyncio.Protocol):
        """Async protocol for McIntosh communication."""

        def __init__(
            self,
            serial_port: str,
            min_time_between_commands: float,
            response_eol: str,
            serial_config: dict,
            loop,
        ):
            super().__init__()
            self._serial_port = serial_port
            self._min_time_between_commands = min_time_between_commands
            self._response_eol = response_eol
            self._serial_config = serial_config
            self._loop = loop

            self._last_send = time.time() - 1
            self._timeout = serial_config.get('timeout', DEFAULT_TIMEOUT)

            self._transport = None
            self._connected = asyncio.Event()
            self._q = asyncio.Queue()
            self._lock = asyncio.Lock()

            LOG.info(f'McIntosh protocol timeout set to {self._timeout}s')

        def connection_made(self, transport):
            """Handle connection established."""
            self._transport = transport
            LOG.debug(f'Port {self._serial_port} opened')
            self._connected.set()

        def data_received(self, data):
            """Handle data received from device."""
            asyncio.ensure_future(self._q.put(data))

        def connection_lost(self, exc):
            """Handle connection lost."""
            LOG.debug(f'Port {self._serial_port} closed')
            self._connected.clear()

        async def _throttle_requests(self):
            """Throttle RS232 sends to avoid causing timeouts."""
            delta = time.time() - self._last_send

            if delta < self._min_time_between_commands:
                delay = max(0, self._min_time_between_commands - delta)
                LOG.debug(f'Throttling: sleeping {delay:.3f}s before next command')
                await asyncio.sleep(delay)

        @locked_method
        @ensure_connected
        async def send(self, request: bytes, wait_for_reply: bool = True) -> Optional[str]:
            """Send command and optionally wait for response."""
            await self._throttle_requests()

            # clear buffers
            self._transport.serial.reset_output_buffer()
            self._transport.serial.reset_input_buffer()
            while not self._q.empty():
                self._q.get_nowait()

            # send command
            LOG.debug(f'Sending: {request}')
            self._last_send = time.time()
            self._transport.serial.write(request)

            if not wait_for_reply:
                return None

            # read response
            data = bytearray()
            response_eol_bytes = self._response_eol.encode('ascii')

            try:
                while True:
                    data += await asyncio.wait_for(self._q.get(), self._timeout)

                    if response_eol_bytes in data:
                        LOG.debug(
                            f'Received: {data.decode("ascii", errors="ignore")} (len={len(data)})'
                        )

                        # split by EOL and filter empty lines
                        lines = data.split(response_eol_bytes)
                        lines = [line for line in lines if line]

                        if not lines:
                            return ''

                        if len(lines) > 1:
                            LOG.debug(f'Multiple response lines, using first: {lines}')

                        return lines[0].decode('ascii', errors='ignore')

            except asyncio.TimeoutError:
                LOG.warning(
                    f'Timeout waiting for response to {request}: received={data} ({self._timeout}s)'
                )
                raise

    # create protocol factory
    factory = functools.partial(
        McIntoshProtocol,
        serial_port,
        min_time_between_commands,
        response_eol,
        serial_config,
        loop,
    )

    LOG.info(f'Creating connection to {serial_port}: {serial_config}')

    # lazy import to avoid blocking
    def _import_serial_asyncio():
        from serial_asyncio import create_serial_connection

        return create_serial_connection

    create_serial_connection = await loop.run_in_executor(None, _import_serial_asyncio)

    # create connection
    _, protocol = await create_serial_connection(loop, factory, serial_port, **serial_config)
    return protocol
