"""Pure-logic J1939 PGN decoder — no GUI imports."""

from typing import Dict, List, Tuple, Optional


class PGNDecoder:
    """Decodes J1939 PGN messages into physical values using channel definitions."""

    def __init__(self, pgn_channels: List[Dict]) -> None:
        """
        Initialise the decoder with a list of channel definitions.

        Args:
            pgn_channels: List of channel dicts from configuration, e.g.:
                {
                    "label": "Engine RPM",
                    "pgn": 0xF004,          # integer (already parsed by config_loader)
                    "bytes": [3, 4],
                    "byte_order": "little_endian",
                    "scale": 0.125,
                    "offset": 0,
                    "unit": "rpm",
                    "format": "{:.0f}"
                }
        """
        self._channels: List[Dict] = pgn_channels
        # Cache channels grouped by PGN integer for fast lookup
        self._pgn_map: Dict[int, List[Dict]] = {}
        for ch in pgn_channels:
            pgn = ch.get('pgn')
            if pgn is None:
                continue
            self._pgn_map.setdefault(pgn, []).append(ch)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decode(self, can_id: int, data: List[int]) -> Dict[str, Tuple[float, str]]:
        """
        Decode a CAN message and return physical values for all matching channels.

        The PGN is extracted from the 29-bit J1939 CAN identifier using:
            pgn = (can_id >> 8) & 0x3FFFF

        Args:
            can_id: 29-bit J1939 arbitration ID.
            data:   List of byte values from the CAN frame payload.

        Returns:
            Dict mapping channel label to (physical_value, unit).
            Empty dict if no channels match the received PGN.
        """
        pgn = (can_id >> 8) & 0x3FFFF
        channels = self._pgn_map.get(pgn)
        if not channels:
            return {}

        result: Dict[str, Tuple[float, str]] = {}
        for ch in channels:
            label = ch.get('label', '')
            byte_indices: List[int] = ch.get('bytes', [])
            byte_order: str = ch.get('byte_order', 'little_endian')
            scale: float = float(ch.get('scale', 1.0))
            offset: float = float(ch.get('offset', 0.0))
            unit: str = ch.get('unit', '')

            try:
                raw = self._assemble_raw(data, byte_indices, byte_order)
            except (IndexError, ValueError):
                # Skip channel if bytes are missing or malformed
                continue

            if raw is None:
                continue

            physical = raw * scale + offset
            result[label] = (physical, unit)

        return result

    def get_channel_labels(self) -> List[str]:
        """Return all channel labels in the order they appear in the configuration."""
        return [ch.get('label', '') for ch in self._channels]

    def get_format(self, label: str) -> str:
        """
        Return the format string for a channel label.

        Args:
            label: Channel label string.

        Returns:
            Python format string, e.g. "{:.0f}". Defaults to "{:.1f}".
        """
        for ch in self._channels:
            if ch.get('label') == label:
                return ch.get('format', '{:.1f}')
        return '{:.1f}'

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _assemble_raw(data: List[int], byte_indices: List[int], byte_order: str) -> Optional[int]:
        """
        Assemble a raw integer from the specified byte indices of the data payload.

        Args:
            data:         List of byte values.
            byte_indices: Ordered list of byte positions to combine.
            byte_order:   "little_endian" or "big_endian".

        Returns:
            Assembled integer, or None if byte_indices is empty.

        Raises:
            IndexError: If any byte index is out of range for data.
        """
        if not byte_indices:
            return None

        # Collect bytes — raises IndexError if any index is out of range
        raw_bytes = [data[i] for i in byte_indices]

        if byte_order == 'big_endian':
            # MSB first
            raw = 0
            for b in raw_bytes:
                raw = (raw << 8) | b
        else:
            # little_endian: first index is LSB
            raw = 0
            for shift, b in enumerate(raw_bytes):
                raw |= b << (8 * shift)

        return raw
