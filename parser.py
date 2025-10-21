from enum import Enum
import logging
from typing import MutableSequence, NamedTuple
from string import Template

import matcher

logger = logging.getLogger(__name__)


class ParserErrors(Enum):
    PARSE_RANGE_MIN = Template(
        "Syntax error: Parsing repeat range minium, Expected digit, `}` or `,` ... got `${char}`!"
    )
    PARSE_RANGE_MAX = Template(
        "Syntax error: Parsing repeat range maximum, Expected digit, `}` ... got `${char}`!"
    )
    PARSE_RANGE_INVALID = Template(
        "SyntaxError: Repeat range invalid, min=${min_} > max=${max_}!"
    )


class ParsedRange(NamedTuple):
    min_: int
    max_: int | None
    str_idx: int


def parse_range(regex: str, str_idx: int, str_len: int):
    min_repeat_count_digits = []
    idx = str_idx
    is_done = False
    for idx in range(str_idx, str_len):
        char = regex[idx]
        if char.isdigit():
            min_repeat_count_digits.append(char)
        elif char == " ":
            continue
        elif char == ",":
            break
        elif char == "}":
            is_done = True
            break
        else:
            raise SyntaxError(ParserErrors.PARSE_RANGE_MIN.value.substitute(char=char))

    max_repeat_count_digits = []
    if not is_done:
        for idx in range(idx + 1, str_len):
            char = regex[idx]
            if char.isdigit():
                max_repeat_count_digits.append(char)
            elif char == " ":
                continue
            elif char == "}":
                break
            else:
                raise SyntaxError(
                    ParserErrors.PARSE_RANGE_MAX.value.substitute(char=char)
                )
    else:
        # Exact number of matches range where min == max
        max_repeat_count_digits = min_repeat_count_digits

    min_repeat_count = int("".join(min_repeat_count_digits) or 0)

    if max_repeat_count_digits:
        max_repeat_count = int("".join(max_repeat_count_digits))
    else:
        max_repeat_count = None

    if max_repeat_count and (min_repeat_count > max_repeat_count):
        raise SyntaxError(
            ParserErrors.PARSE_RANGE_INVALID.value.substitute(
                min_=min_repeat_count, max_=max_repeat_count
            )
        )

    return ParsedRange(min_=min_repeat_count, max_=max_repeat_count, str_idx=idx)


def add_range_wrapped(
    curr_group_node: matcher.GroupNode, min_: int | None = None, max_: int | None = None
):
    node_to_repeat = curr_group_node.sub_nodes.pop()
    curr_group_node.sub_nodes.append(
        matcher.GroupGreadyRepeatNode(
            sub_nodes=[node_to_repeat], min_repeat_count=min_, max_repeat_count=max_
        )
    )


def parse(regex: str, str_idx: int) -> matcher.GroupNode:
    regex_len = len(regex)
    gourp_stack: MutableSequence[matcher.GroupNode] = [
        matcher.GroupAllNode(sub_nodes=[])
    ]

    while str_idx < regex_len:
        curr_char = regex[str_idx]
        curr_group_node = gourp_stack[-1]

        match curr_char:
            case "[":
                match_any_of_node = matcher.GroupAnyNode(sub_nodes=[])
                curr_group_node.sub_nodes.append(match_any_of_node)
                gourp_stack.append(match_any_of_node)
            case "]":
                gourp_stack.pop()
            case "+":
                add_range_wrapped(curr_group_node, min_=1)
            case "*":
                add_range_wrapped(curr_group_node)
            case "{":
                parsed_range = parse_range(
                    regex=regex, str_idx=str_idx + 1, str_len=regex_len
                )
                add_range_wrapped(curr_group_node, parsed_range.min_, parsed_range.max_)
                str_idx = parsed_range.str_idx
            case ".":
                curr_group_node.sub_nodes.append(matcher.MatchAnyNode())
            case _:
                curr_group_node.sub_nodes.append(matcher.MatchCharNode(char=curr_char))

        str_idx += 1

    return gourp_stack[0]


def check(regex: str, expected_match_exp: matcher.GroupNode | None):
    try:
        match_exp = parse(regex, 0)
    except SyntaxError:
        passed = expected_match_exp is None
        logger.debug(
            f"SyntaxError for {regex} is correcty issued? "
            f"<<<<<<<<<<< {'SUCCESS' if passed else 'FAIL'}"
        )
        return

    if expected_match_exp is not None:
        passed = match_exp == expected_match_exp
        logger.debug(
            f"Match exp {match_exp} == {expected_match_exp} for {regex} "
            f"<<<<<<<<<<< {'SUCCESS' if passed else 'FAIL'}"
        )
    else:
        raise ValueError("Parsable regex strings can not have None expression")


if __name__ == "__main__":
    import log

    log.setup()

    from matcher import (
        GroupAnyNode,
        GroupAllNode,
        MatchCharNode,
        GroupGreadyRepeatNode,
    )

    check(
        "ababab[QAD]*",
        GroupAllNode(
            sub_nodes=[
                MatchCharNode(char="a", is_group=False),
                MatchCharNode(char="b", is_group=False),
                MatchCharNode(char="a", is_group=False),
                MatchCharNode(char="b", is_group=False),
                MatchCharNode(char="a", is_group=False),
                MatchCharNode(char="b", is_group=False),
                GroupGreadyRepeatNode(
                    sub_nodes=[
                        GroupAnyNode(
                            sub_nodes=[
                                MatchCharNode(char="Q", is_group=False),
                                MatchCharNode(char="A", is_group=False),
                                MatchCharNode(char="D", is_group=False),
                            ],
                            is_group=True,
                        )
                    ],
                    is_group=True,
                    min_repeat_count=None,
                    max_repeat_count=None,
                ),
            ],
            is_group=True,
        ),
    )

    check(
        "a[b]+",
        GroupAllNode(
            sub_nodes=[
                MatchCharNode(char="a", is_group=False),
                GroupGreadyRepeatNode(
                    sub_nodes=[
                        GroupAnyNode(
                            sub_nodes=[MatchCharNode(char="b", is_group=False)],
                            is_group=True,
                        )
                    ],
                    is_group=True,
                    min_repeat_count=1,
                    max_repeat_count=None,
                ),
            ],
            is_group=True,
        ),
    )

    check(
        "ababab12345-_=;'`",
        GroupAllNode(
            sub_nodes=[
                MatchCharNode(char="a", is_group=False),
                MatchCharNode(char="b", is_group=False),
                MatchCharNode(char="a", is_group=False),
                MatchCharNode(char="b", is_group=False),
                MatchCharNode(char="a", is_group=False),
                MatchCharNode(char="b", is_group=False),
                MatchCharNode(char="1", is_group=False),
                MatchCharNode(char="2", is_group=False),
                MatchCharNode(char="3", is_group=False),
                MatchCharNode(char="4", is_group=False),
                MatchCharNode(char="5", is_group=False),
                MatchCharNode(char="-", is_group=False),
                MatchCharNode(char="_", is_group=False),
                MatchCharNode(char="=", is_group=False),
                MatchCharNode(char=";", is_group=False),
                MatchCharNode(char="'", is_group=False),
                MatchCharNode(char="`", is_group=False),
            ],
            is_group=True,
        ),
    )

    check(
        "a{1,      20}",
        GroupAllNode(
            sub_nodes=[
                GroupGreadyRepeatNode(
                    sub_nodes=[MatchCharNode(char="a", is_group=False)],
                    is_group=True,
                    min_repeat_count=1,
                    max_repeat_count=20,
                )
            ],
            is_group=True,
        ),
    )

    check(
        "a{,      9      }",
        GroupAllNode(
            sub_nodes=[
                GroupGreadyRepeatNode(
                    sub_nodes=[MatchCharNode(char="a", is_group=False)],
                    is_group=True,
                    min_repeat_count=0,
                    max_repeat_count=9,
                )
            ],
            is_group=True,
        ),
    )

    check(
        "a{1,      }",
        GroupAllNode(
            sub_nodes=[
                GroupGreadyRepeatNode(
                    sub_nodes=[MatchCharNode(char="a", is_group=False)],
                    is_group=True,
                    min_repeat_count=1,
                    max_repeat_count=None,
                )
            ],
            is_group=True,
        ),
    )

    check(
        "a{      9999999999      }",
        GroupAllNode(
            sub_nodes=[
                GroupGreadyRepeatNode(
                    sub_nodes=[MatchCharNode(char="a", is_group=False)],
                    is_group=True,
                    min_repeat_count=9999999999,
                    max_repeat_count=9999999999,
                )
            ],
            is_group=True,
        ),
    )

    # Should error with - SyntaxError: Repeat range invalid, min=10 > max=9!
    check("a{10,      9      }", None)
