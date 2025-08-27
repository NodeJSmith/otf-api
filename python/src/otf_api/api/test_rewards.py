"""Test rewards API client - TO BE DELETED after testing AI generation."""

from datetime import date
from typing import Any

from otf_api.api.base import BaseApi
from otf_api.models.test_rewards import RewardStatus, RewardType, TestReward, TestRewardRedemption


class TestRewardsApi(BaseApi):
    """Test rewards API for validating AI TypeScript generation.

    This API client demonstrates new endpoints that should trigger
    TypeScript client generation and type updates.
    """

    async def get_member_rewards(
        self,
        member_uuid: str,
        status: RewardStatus | None = None,
        reward_type: RewardType | None = None,
        limit: int = 50,
    ) -> list[TestReward]:
        """Get all rewards for a member.

        Args:
            member_uuid: UUID of the member
            status: Filter by reward status
            reward_type: Filter by reward type
            limit: Maximum number of rewards to return

        Returns:
            List of member rewards
        """
        params: dict[str, Any] = {"member_uuid": member_uuid, "limit": limit}

        if status:
            params["status"] = status.value

        if reward_type:
            params["reward_type"] = reward_type.value

        response = await self.client.request(method="GET", path="/api/v1/test-rewards/member-rewards", params=params)

        return [TestReward.model_validate(reward) for reward in response.get("rewards", [])]

    async def redeem_reward(
        self, reward_uuid: str, studio_uuid: str, booking_uuid: str | None = None
    ) -> TestRewardRedemption:
        """Redeem a reward at a studio.

        Args:
            reward_uuid: UUID of the reward to redeem
            studio_uuid: UUID of the studio where redemption occurs
            booking_uuid: Optional booking to apply reward to

        Returns:
            Redemption record

        Raises:
            RewardNotFoundError: If reward doesn't exist
            RewardExpiredError: If reward has expired
            RewardAlreadyRedeemedError: If reward was already redeemed
        """
        data = {"reward_uuid": reward_uuid, "studio_uuid": studio_uuid}

        if booking_uuid:
            data["booking_uuid"] = booking_uuid

        response = await self.client.request(method="POST", path="/api/v1/test-rewards/redeem", data=data)

        return TestRewardRedemption.model_validate(response)

    async def get_available_rewards(self, member_uuid: str, studio_uuid: str | None = None) -> list[TestReward]:
        """Get rewards available for redemption by a member.

        Args:
            member_uuid: UUID of the member
            studio_uuid: Optional studio UUID to filter location-specific rewards

        Returns:
            List of available rewards
        """
        params = {"member_uuid": member_uuid}

        if studio_uuid:
            params["studio_uuid"] = studio_uuid

        response = await self.client.request(method="GET", path="/api/v1/test-rewards/available", params=params)

        return [TestReward.model_validate(reward) for reward in response.get("rewards", [])]

    async def get_reward_history(
        self, member_uuid: str, start_date: date | None = None, end_date: date | None = None
    ) -> list[TestRewardRedemption]:
        """Get reward redemption history for a member.

        Args:
            member_uuid: UUID of the member
            start_date: Start date for history range
            end_date: End date for history range

        Returns:
            List of redemption records
        """
        params = {"member_uuid": member_uuid}

        if start_date:
            params["start_date"] = start_date.isoformat()

        if end_date:
            params["end_date"] = end_date.isoformat()

        response = await self.client.request(method="GET", path="/api/v1/test-rewards/history", params=params)

        return [TestRewardRedemption.model_validate(redemption) for redemption in response.get("redemptions", [])]
