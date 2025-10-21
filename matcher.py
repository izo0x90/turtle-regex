from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging
from typing import ClassVar, Iterator, Literal, MutableSequence, Protocol

logger = logging.getLogger(__name__)

IS_DONE_TYPE = Literal[True]


@dataclass
class GroupState:
    str_idx: int = 0
    consumed: int = 0
    end_of_strig: bool = False
    repeat_count: int = 0
    is_done: bool = False
    has_match: bool = False
    group_iter: Iterator | None = None
    debug_results: list = field(default_factory=list)

    IS_DONE: ClassVar[IS_DONE_TYPE] = True

    def __next__(self) -> Node | IS_DONE_TYPE:
        if self.group_iter and (node := next(self.group_iter, None)):
            return node
        return self.IS_DONE


class Node(Protocol):
    is_group: bool

    def __iter__(self) -> Iterator[Node]: ...
    def is_group_match(self, state: GroupState) -> bool: ...
    def is_match(
        self, source_string: str, source_string_len: int, index: int
    ) -> bool: ...
    def process_sub_node_result(
        self, state: GroupState, result_of_node_match: bool, consumed: int
    ): ...


@dataclass
class GroupNode(ABC):
    sub_nodes: MutableSequence[Node]
    is_group: bool = True

    # def __post_init__(self):
    #     self._curr_iter = iter(self)

    def __iter__(self):
        return iter(self.sub_nodes)

    def is_match(self, source_string: str, source_string_len: int, index: int):
        assert False

    def is_group_match(self, state: GroupState) -> bool:
        if not state.is_done:
            raise ValueError("Group was not finished processing all nodes")
        return state.has_match

    @abstractmethod
    def process_sub_node_result(
        self, state: GroupState, result_of_node_match: bool, consumed: int
    ): ...


@dataclass
class GroupAnyNode(GroupNode):
    def process_sub_node_result(
        self, state: GroupState, result_of_node_match: bool, consumed: int
    ):
        state.debug_results.append(result_of_node_match)

        if state.end_of_strig:
            state.consumed = 0
            state.group_iter = None
            state.has_match = False
            return

        if result_of_node_match:
            state.consumed += consumed
            state.group_iter = None
            state.has_match = True


@dataclass
class GroupAllNode(GroupNode):
    def process_sub_node_result(
        self, state: GroupState, result_of_node_match: bool, consumed: int
    ):
        state.debug_results.append(result_of_node_match)

        if not result_of_node_match or state.end_of_strig:
            state.group_iter = None
            state.has_match = False
            state.consumed = 0
            return

        state.has_match = True
        state.consumed += consumed


@dataclass
class GroupGreadyRepeatNode(GroupNode):
    # TODO: (Hristo) Fix range matching for upper limit (if exceeded only stop, match is still true)
    # TODO: (Hristo) Fix Matching `.` any char is not lazy so consumes all
    min_repeat_count: int | None = None
    max_repeat_count: int | None = None

    def process_sub_node_result(
        self, state: GroupState, result_of_node_match: bool, consumed: int
    ):
        state.debug_results.append(result_of_node_match)

        if not result_of_node_match or state.end_of_strig:
            if (
                self.min_repeat_count is not None
                and state.repeat_count < self.min_repeat_count
            ):
                state.has_match = False
                state.consumed = 0
            else:
                state.has_match = True
            state.group_iter = None
            return

        state.consumed += consumed
        state.repeat_count += 1

        if (
            self.max_repeat_count is not None
            and state.repeat_count > self.max_repeat_count
        ):
            state.has_match = False
            state.consumed = 0
            state.group_iter = None
            return

        state.group_iter = iter(self.sub_nodes)


class BaseNode:
    is_group: bool
    str_idx: int = 0
    consumed: int = 0

    def __iter__(self) -> Iterator[Node]:
        assert False

    def __next__(self) -> Node | IS_DONE_TYPE:
        assert False

    def is_group_match(self, state: GroupState) -> bool:
        assert False
        ...

    def process_sub_node_result(
        self, state: GroupState, result_of_node_match: bool, consumed: int
    ):
        assert False
        ...


@dataclass
class MatchAnyNode(BaseNode):
    is_group: bool = False

    def is_match(self, source_string: str, source_string_len: int, index: int):
        return index < source_string_len


@dataclass
class MatchCharNode(BaseNode):
    char: str
    is_group: bool = False

    def is_match(self, source_string: str, source_string_len: int, index: int):
        return (index < source_string_len) and (source_string[index] == self.char)


def match(
    start_node: GroupNode, source_string: str, start_index: int = 0
) -> tuple[bool, int]:
    SOURCE_STRING_LEN = len(source_string)
    stack: list[tuple[Node, GroupState]] = [
        (start_node, GroupState(str_idx=start_index, group_iter=iter(start_node)))
    ]

    result = (False, -1)
    while stack:
        curr_group, curr_state = stack[-1]
        curr_node = next(curr_state)

        if curr_node == GroupState.IS_DONE:
            curr_state.is_done = True
            stack.pop()
            has_group_match = curr_group.is_group_match(curr_state)
            curr_state.end_of_strig = (
                curr_state.str_idx + curr_state.consumed
            ) < SOURCE_STRING_LEN

            if stack:
                parent_group, parent_state = stack[-1]
                parent_group.process_sub_node_result(
                    parent_state, has_group_match, curr_state.consumed
                )
            else:
                result = (has_group_match, curr_state.consumed)
                break

        elif curr_node.is_group:
            new_group_state = GroupState(
                str_idx=curr_state.str_idx + curr_state.consumed,
                group_iter=iter(curr_node),
            )
            stack.append((curr_node, new_group_state))
        else:
            has_node_match = curr_node.is_match(
                source_string,
                SOURCE_STRING_LEN,
                curr_state.str_idx + curr_state.consumed,
            )
            curr_group.process_sub_node_result(curr_state, has_node_match, 1)

    return result


def test_hristo(string: str):
    match_exp = GroupAllNode(
        sub_nodes=[
            MatchAnyNode(),
            MatchCharNode(char="r"),
            GroupAnyNode(
                sub_nodes=[
                    MatchCharNode(char="#"),
                    MatchCharNode(char="i"),
                ]
            ),
            MatchAnyNode(),
            MatchCharNode(char="t"),
        ]
    )
    return match(match_exp, string)


def test_greedy_repeat_zero_or_many(string: str):
    match_exp = GroupGreadyRepeatNode(
        sub_nodes=[
            GroupAllNode(
                sub_nodes=[
                    MatchCharNode(char="a"),
                    MatchCharNode(char="b"),
                ]
            )
        ]
    )
    return match(match_exp, string)


def test_greedy_repeat_one_or_many(string: str):
    match_exp = GroupGreadyRepeatNode(
        min_repeat_count=1,
        sub_nodes=[
            GroupAllNode(
                sub_nodes=[
                    MatchCharNode(char="a"),
                    MatchCharNode(char="b"),
                ]
            )
        ],
    )
    return match(match_exp, string)


def check(
    test_result: tuple[bool, int], expected_is_match: bool, expected_consumed_idx: int
):
    test_is_match, test_consumed_idx = test_result
    logger.debug(
        f"Test match {test_is_match}=={expected_is_match}, "
        f"test consumed {test_consumed_idx}=={expected_consumed_idx} "
        f"<<<<<<<<<<< {'SUCCESS' if test_is_match == expected_is_match and test_consumed_idx == expected_consumed_idx else 'FAIL'}"
    )


def test_all():
    import log

    log.setup()

    check(test_hristo("Hristo"), True, 5)
    check(test_hristo("Hri_to"), True, 5)
    check(test_hristo("Hr#sto"), True, 5)
    check(test_hristo("Hr$sto"), False, 0)
    check(test_hristo("Hris*o"), False, 0)

    logger.debug("Test repeat, zero or many:")
    check(test_greedy_repeat_zero_or_many("ab"), True, 2)
    check(test_greedy_repeat_zero_or_many("ababab"), True, 6)
    check(test_greedy_repeat_zero_or_many("abbcab"), True, 2)

    logger.debug("Test repeat, one or many:")
    check(test_greedy_repeat_one_or_many("ab-suffix"), True, 2)
    check(test_greedy_repeat_one_or_many("abab-suffix"), True, 4)
    check(test_greedy_repeat_one_or_many("ababab-suffix"), True, 6)
    check(test_greedy_repeat_one_or_many("baabab-suffix"), False, 0)


if __name__ == "__main__":
    test_all()
