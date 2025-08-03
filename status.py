from dataclasses import dataclass
from enum import IntEnum
import constants


class SubmissionStatus(IntEnum):
    NEW = 0
    NEW_ALT = 1
    WAITING_FOR_COMPILE = 2
    COMPILING = 3
    WAITING_FOR_RUN = 4
    RUNNING = 5
    JUDGE_ERROR = 6
    COMPILE_ERROR = 8
    RUNTIME_ERROR = 9
    MEMORY_LIMIT_EXCEEDED = 10
    OUTPUT_LIMIT_EXCEEDED = 11
    TIME_LIMIT_EXCEEDED = 12
    ILLEGAL_FUNCTION = 13
    WRONG_ANSWER = 14
    ACCEPTED = 16


@dataclass
class StatusInfo:
    """Information about a submission status."""

    name: str
    description: str
    is_final: bool
    is_success: bool


STATUS_MAP = {
    SubmissionStatus.NEW: StatusInfo(
        name="New",
        description="Submission received and queued",
        is_final=False,
        is_success=False,
    ),
    SubmissionStatus.NEW_ALT: StatusInfo(
        name="New",
        description="Submission received and queued (alternative)",
        is_final=False,
        is_success=False,
    ),
    SubmissionStatus.WAITING_FOR_COMPILE: StatusInfo(
        name="Waiting for compile",
        description="Submission is waiting to be compiled",
        is_final=False,
        is_success=False,
    ),
    SubmissionStatus.COMPILING: StatusInfo(
        name="Compiling",
        description="Source code is being compiled",
        is_final=False,
        is_success=False,
    ),
    SubmissionStatus.WAITING_FOR_RUN: StatusInfo(
        name="Waiting for run",
        description="Compiled successfully, waiting to run test cases",
        is_final=False,
        is_success=False,
    ),
    SubmissionStatus.RUNNING: StatusInfo(
        name="Running",
        description="Executing test cases",
        is_final=False,
        is_success=False,
    ),
    SubmissionStatus.JUDGE_ERROR: StatusInfo(
        name="Judge Error",
        description="Internal error in the judging system",
        is_final=True,
        is_success=False,
    ),
    SubmissionStatus.COMPILE_ERROR: StatusInfo(
        name="Compile Error",
        description="Source code failed to compile",
        is_final=True,
        is_success=False,
    ),
    SubmissionStatus.RUNTIME_ERROR: StatusInfo(
        name="Run Time Error",
        description="Program crashed during execution",
        is_final=True,
        is_success=False,
    ),
    SubmissionStatus.MEMORY_LIMIT_EXCEEDED: StatusInfo(
        name="Memory Limit Exceeded",
        description="Program used more memory than allowed",
        is_final=True,
        is_success=False,
    ),
    SubmissionStatus.OUTPUT_LIMIT_EXCEEDED: StatusInfo(
        name="Output Limit Exceeded",
        description="Program produced too much output",
        is_final=True,
        is_success=False,
    ),
    SubmissionStatus.TIME_LIMIT_EXCEEDED: StatusInfo(
        name="Time Limit Exceeded",
        description="Program took too long to execute",
        is_final=True,
        is_success=False,
    ),
    SubmissionStatus.ILLEGAL_FUNCTION: StatusInfo(
        name="Illegal Function",
        description="Program used forbidden functions or system calls",
        is_final=True,
        is_success=False,
    ),
    SubmissionStatus.WRONG_ANSWER: StatusInfo(
        name="Wrong Answer",
        description="Program output doesn't match expected output",
        is_final=True,
        is_success=False,
    ),
    SubmissionStatus.ACCEPTED: StatusInfo(
        name="Accepted",
        description="Solution is correct!",
        is_final=True,
        is_success=True,
    ),
}


def get_status_info(status_id: int) -> StatusInfo:
    """Get status information for a given status ID."""
    try:
        status = SubmissionStatus(status_id)
        return STATUS_MAP[status]
    except ValueError:
        return StatusInfo(
            name=f"Unknown Status {status_id}",
            description=f"Unrecognized status code: {status_id}",
            is_final=True,
            is_success=False,
        )


def is_final_status(status_id: int) -> bool:
    """Check if a status represents a final state."""
    return get_status_info(status_id).is_final


def is_successful_status(status_id: int) -> bool:
    """Check if a status represents a successful submission."""
    return get_status_info(status_id).is_success


def get_status_name(status_id: int) -> str:
    """Get the display name for a status."""
    return get_status_info(status_id).name
