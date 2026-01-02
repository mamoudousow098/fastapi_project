"""
Broker Exception for handling business errors
"""
from typing import Optional
from message_enum import MessagesEnum


class BrokerException(Exception):
    """
    Custom exception for broker business logic errors
    Equivalent to Java BrokerException
    """

    def __init__(
            self,
            message_enum: MessagesEnum,
            custom_message: Optional[str] = None,
            cause: Optional[Exception] = None
    ):
        """
        Initialize BrokerException

        Args:
            message_enum: MessagesEnum value
            custom_message: Optional custom message to override default
            cause: Original exception that caused this error
        """
        self.message_enum = message_enum
        self.error_code = message_enum.error_code
        self.error_message = custom_message or message_enum.error_message
        self.reject_reason = message_enum.reject_reason
        self.cause = cause

        # Call parent constructor
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format exception message"""
        return f"BrokerException[{self.error_message}]: {self.message_enum.name}"

    def __str__(self) -> str:
        return self._format_message()

    def __repr__(self) -> str:
        return (
            f"BrokerException(message_enum={self.message_enum.name}, "
            f"error_code={self.error_code}, error_message='{self.error_message}')"
        )

    def to_dict(self) -> dict:
        """Convert exception to dictionary"""
        return {
            "error_code": self.error_code,
            "error_message": self.error_message,
            "message_enum": self.message_enum.name,
            "reject_reason": self.reject_reason.value if self.reject_reason else None
        }


# Usage examples in your code:

# Example 1: Raise exception with default message
def example_1():
    raise BrokerException(MessagesEnum.ACCOUNT_NOT_FOUND)

# Example 2: Raise exception with custom message
def example_2():
    raise BrokerException(
        MessagesEnum.ACCOUNT_NOT_FOUND,
        custom_message="Account with ID 12345 not found"
    )

# Example 3: Raise exception with original cause
def example_3():
    try:
        # Some operation that fails
        result = 1 / 0
    except ZeroDivisionError as e:
        raise BrokerException(
            MessagesEnum.SERVER_ERROR,
            custom_message="Calculation error occurred",
            cause=e
        )

# Example 4: Catch and handle BrokerException
def example_4():
    try:
        raise BrokerException(MessagesEnum.INSUFFICIENT_BALANCE)
    except BrokerException as e:
        print(f"Error code: {e.error_code}")
        print(f"Error message: {e.error_message}")
        print(f"Enum name: {e.message_enum.name}")