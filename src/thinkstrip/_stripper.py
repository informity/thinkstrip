# thinkstrip | Stateful streaming think-block filter
# Maintainer: Informity

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass(slots=True)
class ThinkStrip:
    open_tag:        str  = '<think>'
    close_tag:       str  = '</think>'
    capture:         bool = False
    _in_think_block: bool = field(default=False, init=False, repr=False)
    _partial:        str  = field(default='', init=False, repr=False)
    _captured:       list[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.open_tag:
            raise ValueError('open_tag must not be empty')
        if not self.close_tag:
            raise ValueError('close_tag must not be empty')

    @property
    def think_content(self) -> str:
        return ''.join(self._captured)

    @property
    def in_think_block(self) -> bool:
        return self._in_think_block

    def feed(self, token: str) -> str:
        if not isinstance(token, str):
            raise TypeError('token must be a string')

        # Nested <think> tags are not supported. A second <think> that arrives
        # while already inside a think block is treated as think content and
        # swallowed. The first </think> closes the block; any subsequent
        # </think> with no matching open tag passes through as visible text.
        self._partial += token
        emitted:     list[str] = []
        open_guard  = len(self.open_tag) - 1
        close_guard = len(self.close_tag) - 1

        while self._partial:
            if not self._in_think_block:
                start_pos = self._partial.find(self.open_tag)
                if start_pos == -1:
                    safe_len = max(0, len(self._partial) - open_guard)
                    if safe_len == 0:
                        break
                    emitted.append(self._partial[:safe_len])
                    self._partial = self._partial[safe_len:]
                    break

                if start_pos > 0:
                    emitted.append(self._partial[:start_pos])
                self._partial       = self._partial[start_pos + len(self.open_tag):]
                self._in_think_block = True
                continue

            end_pos = self._partial.find(self.close_tag)
            if end_pos == -1:
                safe_len = max(0, len(self._partial) - close_guard)
                if safe_len == 0:
                    break
                if self.capture:
                    self._captured.append(self._partial[:safe_len])
                self._partial = self._partial[safe_len:]
                break

            if self.capture and end_pos > 0:
                self._captured.append(self._partial[:end_pos])
            self._partial       = self._partial[end_pos + len(self.close_tag):]
            self._in_think_block = False

        return ''.join(emitted)

    def flush(self) -> str:
        if self._in_think_block:
            if self.capture and self._partial:
                self._captured.append(self._partial)
            self._partial = ''
            return ''

        flushed       = self._partial
        self._partial = ''
        return flushed


class AsyncThinkStrip:
    def __init__(
        self,
        open_tag:  str  = '<think>',
        close_tag: str  = '</think>',
        capture:   bool = False,
    ) -> None:
        self._stripper = ThinkStrip(
            open_tag=open_tag,
            close_tag=close_tag,
            capture=capture,
        )

    @property
    def think_content(self) -> str:
        return self._stripper.think_content

    @property
    def in_think_block(self) -> bool:
        return self._stripper.in_think_block

    async def feed(self, token: str) -> str:
        return await asyncio.to_thread(self._stripper.feed, token)

    async def flush(self) -> str:
        return await asyncio.to_thread(self._stripper.flush)
