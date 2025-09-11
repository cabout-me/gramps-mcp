"""
Parameters for transactions endpoints.
"""

from typing import Optional

from pydantic import BaseModel, Field


class TransactionHistoryParams(BaseModel):
    """
    Parameters for getting transaction history.

    Args:
        old (Optional[bool]): Whether to include the raw object data before the
            change
        new (Optional[bool]): Whether to include the raw object data after the
            change
        page (Optional[int]): Page number representing a subset of results to
            be returned
        pagesize (Optional[int]): The number of items that constitute a page
        sort (Optional[str]): Sort the transactions. Can be 'id' to sort
            ascending, '-id' to sort descending
        before (Optional[float]): Unix timestamp. Only return transactions
            committed before this time
        after (Optional[float]): Unix timestamp. Only return transactions
            committed after this time

    Returns:
        Dict[str, Any]: List of transaction history
    """

    old: Optional[bool] = Field(
        None, description="Whether to include the raw object data before the change"
    )
    new: Optional[bool] = Field(
        None, description="Whether to include the raw object data after the change"
    )
    page: Optional[int] = Field(
        None, description="Page number representing a subset of results to be returned"
    )
    pagesize: Optional[int] = Field(
        None, description="The number of items that constitute a page"
    )
    sort: Optional[str] = Field(
        None,
        description="Sort the transactions. Can be 'id' to sort ascending, "
        "'-id' to sort descending",
    )
    before: Optional[float] = Field(
        None,
        description="Unix timestamp. Only return transactions committed before "
        "this time",
    )
    after: Optional[float] = Field(
        None,
        description="Unix timestamp. Only return transactions committed after "
        "this time",
    )


class TransactionHistoryByIdParams(BaseModel):
    """
    Parameters for getting specific transaction history.

    Args:
        transaction_id (int): ID of the transaction to get details for
        old (Optional[bool]): Whether to include the raw object data before the change
        new (Optional[bool]): Whether to include the raw object data after the change

    Returns:
        Dict[str, Any]: Transaction details
    """

    transaction_id: int = Field(
        ..., description="ID of the transaction to get details for"
    )
    old: Optional[bool] = Field(
        None, description="Whether to include the raw object data before the change"
    )
    new: Optional[bool] = Field(
        None, description="Whether to include the raw object data after the change"
    )
