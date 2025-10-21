from dataclasses import dataclass
import logging
from typing import NamedTuple, Sequence
import matcher
import parser

logger = logging.getLogger(__name__)


class Match(NamedTuple):
    start_idx: int
    end_idx: int


def _search(match_exp: matcher.GroupNode, source_text: str) -> Sequence[Match]:
    matches = []

    idx = 0
    while idx < len(source_text):
        is_match, consumed = matcher.match(match_exp, source_text, idx)
        if is_match:
            logger.debug(f"Text match: {source_text[idx : idx + consumed]}")
            matches.append(Match(start_idx=idx, end_idx=idx + consumed))
            idx += consumed
        else:
            logger.debug(f"No match:   {source_text[idx]}")
            idx += 1

    return matches


def _compile(regex: str) -> matcher.GroupNode:
    match_exp = parser.parse(regex, 0)
    logger.debug(f"Complied match expression: {match_exp}")
    return match_exp


@dataclass
class ExpressionMatcher:
    match_exp: matcher.GroupNode

    def search(self, source_text: str):
        return _search(self.match_exp, source_text)


def search(regex: str, source_text: str) -> Sequence[Match]:
    return _search(_compile(regex), source_text)


def compile(regex: str) -> ExpressionMatcher:
    return ExpressionMatcher(match_exp=_compile(regex))


def check(
    regex: str, source_text: str, expected_matches: Sequence[Match], lazy: bool = False
):
    if not lazy:
        matches = search(regex, source_text)
    else:
        matches = compile(regex).search(source_text)

    passed = len(matches) == len(expected_matches) and all(
        match == expected for match, expected in zip(matches, expected_matches)
    )

    logger.debug(
        f"Test matches {matches} == {expected_matches} for {regex} in {source_text}"
        f"<<<<<<<<<<< {'SUCCESS' if passed else 'FAIL'}"
    )


if __name__ == "__main__":
    import log

    log.setup()

    check(
        "[BCP]at",
        "1BatCatPatRat",
        [
            Match(start_idx=1, end_idx=4),
            Match(start_idx=4, end_idx=7),
            Match(start_idx=7, end_idx=10),
        ],
    )
    check(
        ".[BCP]at",
        "1BatCatPatRat",
        [Match(start_idx=0, end_idx=4), Match(start_idx=6, end_idx=10)],
    )
    check("e{2,4}", "$$OleeeOlaOleOleOla", [Match(start_idx=4, end_idx=7)], lazy=True)
