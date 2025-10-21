import logging
from pprint import pformat
import sys
from typing import Sequence

import regex
import log

logger = logging.getLogger(__name__)


def hightlight(matches: Sequence[regex.Match], source_text: str) -> str:
    last_ended_idx = 0
    string_fragments = []
    for match in matches:
        prefix_str = source_text[last_ended_idx : match.start_idx]
        match_str = source_text[match.start_idx : match.end_idx]
        suffix_str = source_text[match.end_idx :]

        last_ended_idx = match.end_idx + 1
        string_fragments.extend([prefix_str, "[blue]", match_str, "[/]", suffix_str])

    return "".join(string_fragments) or source_text


def main() -> int:
    if len(sys.argv) < 2:
        logger.error("No regular expression passed in cmd args.")
        return 1

    regex_str = sys.argv[1]
    logger.info(
        f"[violet]Hello from turtle-regex! Looking for pattern=[/][blue]`{regex_str}`[/]..."
    )

    if len(sys.argv) > 2:
        source_text = sys.argv[2]
    else:
        logger.info("[yellow]Enter multiple lines (Ctrl+D to finish):[/]")
        lines = []
        for line in sys.stdin:
            lines.append(line)
        source_text = "".join(lines)

    try:
        matches = regex.search(regex_str, source_text)
        logger.info(pformat(matches))
        matches_heading = "[green]Matches are:[/]" if matches else "[red]No matches:[/]"
        logger.info(f"{matches_heading} {hightlight(matches, source_text)}")
    except Exception as e:
        logger.exception(e)
        return 1

    return 0


if __name__ == "__main__":
    log.setup()
    sys.exit(main())
