"""Terminal progress display utilities for receipt processing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProgressState:
    """Current progress metrics for rendering."""

    current: int
    total: int
    added: int
    skipped: int
    errors: int
    items: int
    current_receipt: str = "-"


class ReceiptProgressDisplay:
    """Render a fixed 3-line progress block in the terminal."""

    def __init__(self, bar_width: int = 35) -> None:
        self.bar_width = bar_width
        self._initialized = False

    def render(self, state: ProgressState) -> None:
        """Render progress in-place using ANSI cursor control."""
        total = max(state.total, 1)
        fraction = min(max(state.current / total, 0.0), 1.0)
        filled = int(self.bar_width * fraction)
        cart_pos = min(filled, self.bar_width - 1)

        bar_chars = ["="] * filled + ["-"] * (self.bar_width - filled)
        if self.bar_width > 0:
            bar_chars[cart_pos] = "🛒"
        bar = "".join(bar_chars)
        percentage = fraction * 100

        line1 = f"[{bar}] {state.current}/{state.total} ({percentage:5.1f}%)"
        line2 = (
            f"Neu: {state.added} | Uebersprungen: {state.skipped} "
            f"| Fehler: {state.errors} | Artikel: {state.items}"
        )
        line3 = f"Aktuell: {state.current_receipt}"

        if self._initialized:
            print("\033[3F", end="")
        else:
            self._initialized = True

        print(f"\r\033[K{line1}")
        print(f"\r\033[K{line2}")
        print(f"\r\033[K{line3}", flush=True)

    def close(self) -> None:
        """Finalize rendering and move to the next line."""
        if self._initialized:
            print()
