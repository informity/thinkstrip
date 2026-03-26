# thinkstrip | Stateful streaming think-block filter
# Maintainer: Informity

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ThinkStrip:
    open_tag:        str  = '<think>'
    close_tag:       str  = '</think>'
    capture:         bool = False
    _in_think_block: bool      = field(default=False, init=False, repr=False)
    _partial:        str       = field(default='',    init=False, repr=False)
    _captured:       list[str] = field(default_factory=list, init=False, repr=False)
    _open_guard:     int       = field(default=0,     init=False, repr=False)
    _close_guard:    int       = field(default=0,     init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.open_tag:
            raise ValueError('open_tag must not be empty')
        if not self.close_tag:
            raise ValueError('close_tag must not be empty')
        self._open_guard  = len(self.open_tag) - 1
        self._close_guard = len(self.close_tag) - 1

    @property
    def think_content(self) -> str:
        return ''.join(self._captured)

    @property
    def in_think_block(self) -> bool:
        return self._in_think_block

    def _normalize(self, text: str) -> str:
        # Normalize double-angle tag variants emitted by some model templates.
        # <<think>> → <think>   (extra leading '<' and trailing '>')
        # </think>> → </think>  (extra trailing '>')
        # Operates on the full buffer so split-token sequences are caught once
        # both halves have arrived (e.g. '<<thi' + 'nk>>' → '<<think>>' → '<think>').
        double_open  = '<' + self.open_tag  + '>'
        double_close = self.close_tag + '>'
        if double_open  in text: text = text.replace(double_open,  self.open_tag)
        if double_close in text: text = text.replace(double_close, self.close_tag)
        return text

    def feed(self, token: str) -> str:
        if not isinstance(token, str):
            raise TypeError('token must be a string')

        # Nested <think> tags are not supported. A second <think> that arrives
        # while already inside a think block is treated as think content and
        # swallowed. The first </think> closes the block; any subsequent
        # </think> with no matching open tag passes through as visible text.
        self._partial += token
        self._partial  = self._normalize(self._partial)
        emitted: list[str] = []

        while self._partial:
            if not self._in_think_block:
                start_pos = self._partial.find(self.open_tag)
                if start_pos == -1:
                    safe_len = max(0, len(self._partial) - self._open_guard)
                    if safe_len == 0:
                        break
                    emitted.append(self._partial[:safe_len])
                    self._partial = self._partial[safe_len:]
                    break

                if start_pos > 0:
                    emitted.append(self._partial[:start_pos])
                self._partial        = self._partial[start_pos + len(self.open_tag):]
                self._in_think_block = True
                continue

            end_pos = self._partial.find(self.close_tag)
            if end_pos == -1:
                safe_len = max(0, len(self._partial) - self._close_guard)
                if safe_len == 0:
                    break
                if self.capture:
                    self._captured.append(self._partial[:safe_len])
                self._partial = self._partial[safe_len:]
                break

            if self.capture and end_pos > 0:
                self._captured.append(self._partial[:end_pos])
            self._partial        = self._partial[end_pos + len(self.close_tag):]
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

    def reset(self) -> None:
        """Reset to initial state so the instance can process a new stream."""
        self._in_think_block = False
        self._partial        = ''
        self._captured       = []
