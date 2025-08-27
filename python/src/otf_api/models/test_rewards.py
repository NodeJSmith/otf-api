"""Test reward system models - TO BE DELETED after testing AI generation."""

from datetime import datetime
from enum import Enum

from pydantic import Field

from otf_api.models.base import OtfItemBase


class RewardType(str, Enum):
    """Types of rewards available to members."""

    POINTS = "points"
    DISCOUNT = "discount"
    FREE_CLASS = "free_class"
    MERCHANDISE = "merchandise"


class RewardStatus(str, Enum):
    """Status of a reward."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REDEEMED = "redeemed"
    PENDING = "pending"


class TestReward(OtfItemBase):
    """Test reward model for validating AI TypeScript generation.

    This model represents a reward that members can earn and redeem.
    It should trigger TypeScript type generation and API client updates.
    """

    reward_uuid: str = Field(description="Unique identifier for the reward")
    member_uuid: str = Field(description="Member who owns this reward")
    reward_type: RewardType = Field(description="Type of reward")
    reward_status: RewardStatus = Field(description="Current status of the reward")
    title: str = Field(description="Display title of the reward")
    description: str = Field(description="Detailed description of the reward")
    points_value: int = Field(description="Point value of the reward", ge=0)
    discount_percentage: float | None = Field(
        description="Discount percentage if applicable", ge=0, le=100, default=None
    )
    expires_at: datetime | None = Field(description="When the reward expires", default=None)
    redeemed_at: datetime | None = Field(description="When the reward was redeemed", default=None)
    created_at: datetime = Field(description="When the reward was created")
    studio_uuid: str | None = Field(description="Studio where reward can be used", default=None)


class TestRewardRedemption(OtfItemBase):
    """Test reward redemption record."""

    redemption_uuid: str = Field(description="Unique identifier for the redemption")
    reward_uuid: str = Field(description="Reward that was redeemed")
    member_uuid: str = Field(description="Member who redeemed the reward")
    booking_uuid: str | None = Field(description="Associated booking if applicable", default=None)
    redeemed_at: datetime = Field(description="When the redemption occurred")
    studio_uuid: str = Field(description="Studio where redemption occurred")
    redemption_value: float = Field(description="Value applied during redemption", ge=0)
