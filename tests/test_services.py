import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from core.services import UserService, StoryPointService, TeamService
from core.models import User, StoryPoint, Team, TeamMember


class TestUserService:
    def test_get_or_create_user_new_user(self, db_session, sample_user_data):
        user_service = UserService()
        
        user = user_service.get_or_create_user(**sample_user_data)
        
        assert user.id is not None
        assert user.telegram_id == sample_user_data["telegram_id"]
        assert user.username == sample_user_data["username"]
        assert user.first_name == sample_user_data["first_name"]
        assert user.last_name == sample_user_data["last_name"]

    def test_get_or_create_user_existing_user(self, db_session, sample_user_data):
        user_service = UserService()
        
        # Create user first time
        user1 = user_service.get_or_create_user(**sample_user_data)
        user1_id = user1.id
        
        # Get same user second time
        user2 = user_service.get_or_create_user(**sample_user_data)
        
        assert user1_id == user2.id
        assert user1.telegram_id == user2.telegram_id

    def test_get_or_create_user_update_existing(self, db_session, sample_user_data):
        user_service = UserService()
        
        # Create user with initial data
        user1 = user_service.get_or_create_user(**sample_user_data)
        
        # Update user data
        updated_data = sample_user_data.copy()
        updated_data["first_name"] = "Updated"
        updated_data["last_name"] = "Name"
        
        user2 = user_service.get_or_create_user(**updated_data)
        
        assert user1.id == user2.id
        assert user2.first_name == "Updated"
        assert user2.last_name == "Name"

    def test_get_user_by_telegram_id_existing(self, db_session, sample_user_data):
        user_service = UserService()
        
        # Create user
        created_user = user_service.get_or_create_user(**sample_user_data)
        
        # Get user by telegram_id
        found_user = user_service.get_user_by_telegram_id(sample_user_data["telegram_id"])
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.telegram_id == sample_user_data["telegram_id"]

    def test_get_user_by_telegram_id_not_found(self, db_session):
        user_service = UserService()
        
        user = user_service.get_user_by_telegram_id("nonexistent")
        
        assert user is None


class TestStoryPointService:
    def test_add_story_point_success(self, db_session, sample_user_data):
        user_service = UserService()
        story_service = StoryPointService()
        
        # Create user first
        user = user_service.get_or_create_user(**sample_user_data)
        
        # Add story point
        story_point = story_service.add_story_point(
            telegram_id=user.telegram_id,
            points=5.0,
            description="Test implementation"
        )
        
        assert story_point.id is not None
        assert story_point.user_id == user.id
        assert story_point.points == 5.0
        assert story_point.description == "Test implementation"
        assert story_point.date_completed is not None

    def test_add_story_point_user_not_found(self, db_session):
        story_service = StoryPointService()
        
        with pytest.raises(ValueError, match="User with telegram_id nonexistent not found"):
            story_service.add_story_point(
                telegram_id="nonexistent",
                points=3.0,
                description="Test"
            )

    def test_add_story_point_custom_date(self, db_session, sample_user_data):
        user_service = UserService()
        story_service = StoryPointService()
        
        user = user_service.get_or_create_user(**sample_user_data)
        custom_date = datetime(2023, 1, 1, 12, 0, 0)
        
        story_point = story_service.add_story_point(
            telegram_id=user.telegram_id,
            points=8.0,
            description="Custom date task",
            date_completed=custom_date
        )
        
        assert story_point.date_completed == custom_date

    def test_get_user_stats_with_data(self, db_session, sample_user_data):
        user_service = UserService()
        story_service = StoryPointService()
        
        user = user_service.get_or_create_user(**sample_user_data)
        
        # Add multiple story points
        story_service.add_story_point(user.telegram_id, 5.0, "Task 1")
        story_service.add_story_point(user.telegram_id, 3.0, "Task 2")
        story_service.add_story_point(user.telegram_id, 8.0, "Task 3")
        
        stats = story_service.get_user_stats(user.telegram_id)
        
        assert stats["total_points"] == 16.0
        assert stats["total_tasks"] == 3
        assert abs(stats["avg_points"] - 5.333333333333333) < 0.001

    def test_get_user_stats_no_data(self, db_session, sample_user_data):
        user_service = UserService()
        story_service = StoryPointService()
        
        user = user_service.get_or_create_user(**sample_user_data)
        
        stats = story_service.get_user_stats(user.telegram_id)
        
        assert stats["total_points"] == 0.0
        assert stats["total_tasks"] == 0
        assert stats["avg_points"] == 0.0

    def test_get_user_stats_user_not_found(self, db_session):
        story_service = StoryPointService()
        
        stats = story_service.get_user_stats("nonexistent")
        
        assert stats is None

    def test_get_user_stats_date_filter(self, db_session, sample_user_data):
        user_service = UserService()
        story_service = StoryPointService()
        
        user = user_service.get_or_create_user(**sample_user_data)
        
        # Add old story point (outside date range)
        old_date = datetime.utcnow() - timedelta(days=35)
        story_service.add_story_point(
            user.telegram_id, 10.0, "Old task", old_date
        )
        
        # Add recent story point
        story_service.add_story_point(user.telegram_id, 5.0, "Recent task")
        
        stats = story_service.get_user_stats(user.telegram_id, days=30)
        
        assert stats["total_points"] == 5.0
        assert stats["total_tasks"] == 1

    def test_get_leaderboard_with_data(self, db_session, sample_user_data):
        user_service = UserService()
        story_service = StoryPointService()
        
        # Create multiple users
        user1 = user_service.get_or_create_user(**sample_user_data)
        
        user2_data = sample_user_data.copy()
        user2_data["telegram_id"] = "987654321"
        user2_data["first_name"] = "User2"
        user2 = user_service.get_or_create_user(**user2_data)
        
        # Add story points
        story_service.add_story_point(user1.telegram_id, 15.0, "Task 1")
        story_service.add_story_point(user2.telegram_id, 10.0, "Task 2")
        
        leaderboard = story_service.get_leaderboard(limit=10)
        
        assert len(leaderboard) == 2
        assert leaderboard[0]["name"] == "Test User"
        assert leaderboard[0]["points"] == 15.0
        assert leaderboard[1]["name"] == "User2 User"
        assert leaderboard[1]["points"] == 10.0

    def test_get_leaderboard_empty(self, db_session):
        story_service = StoryPointService()
        
        leaderboard = story_service.get_leaderboard()
        
        assert len(leaderboard) == 0

    def test_get_user_story_points(self, db_session, sample_user_data):
        user_service = UserService()
        story_service = StoryPointService()
        
        user = user_service.get_or_create_user(**sample_user_data)
        
        # Add story points
        story_service.add_story_point(user.telegram_id, 5.0, "Task 1")
        story_service.add_story_point(user.telegram_id, 3.0, "Task 2")
        
        story_points = story_service.get_user_story_points(user.telegram_id)
        
        assert len(story_points) == 2
        assert story_points[0].points in [5.0, 3.0]
        assert story_points[1].points in [5.0, 3.0]

    def test_get_user_story_points_user_not_found(self, db_session):
        story_service = StoryPointService()
        
        story_points = story_service.get_user_story_points("nonexistent")
        
        assert len(story_points) == 0


class TestTeamService:
    def test_create_team(self, db_session, sample_team_data):
        team_service = TeamService()
        
        team = team_service.create_team(**sample_team_data)
        
        assert team.id is not None
        assert team.name == sample_team_data["name"]
        assert team.description == sample_team_data["description"]

    def test_create_team_minimal(self, db_session):
        team_service = TeamService()
        
        team = team_service.create_team(name="Minimal Team")
        
        assert team.id is not None
        assert team.name == "Minimal Team"
        assert team.description is None

    def test_add_team_member(self, db_session, sample_team_data, sample_user_data):
        team_service = TeamService()
        user_service = UserService()
        
        team = team_service.create_team(**sample_team_data)
        user = user_service.get_or_create_user(**sample_user_data)
        
        team_member = team_service.add_team_member(
            team_id=team.id,
            telegram_id=user.telegram_id,
            role="developer"
        )
        
        assert team_member.id is not None
        assert team_member.team_id == team.id
        assert team_member.user_id == user.id
        assert team_member.role == "developer"

    def test_add_team_member_default_role(self, db_session, sample_team_data, sample_user_data):
        team_service = TeamService()
        user_service = UserService()
        
        team = team_service.create_team(**sample_team_data)
        user = user_service.get_or_create_user(**sample_user_data)
        
        team_member = team_service.add_team_member(
            team_id=team.id,
            telegram_id=user.telegram_id
        )
        
        assert team_member.role == "member"

    def test_add_team_member_user_not_found(self, db_session, sample_team_data):
        team_service = TeamService()
        
        team = team_service.create_team(**sample_team_data)
        
        with pytest.raises(ValueError, match="User with telegram_id nonexistent not found"):
            team_service.add_team_member(
                team_id=team.id,
                telegram_id="nonexistent"
            )

    def test_get_team_stats_with_data(self, db_session, sample_team_data, sample_user_data):
        team_service = TeamService()
        user_service = UserService()
        story_service = StoryPointService()
        
        # Create team and user
        team = team_service.create_team(**sample_team_data)
        user = user_service.get_or_create_user(**sample_user_data)
        
        # Add user to team
        team_service.add_team_member(team.id, user.telegram_id)
        
        # Add story points
        story_service.add_story_point(user.telegram_id, 5.0, "Task 1")
        story_service.add_story_point(user.telegram_id, 8.0, "Task 2")
        
        stats = team_service.get_team_stats(team.id)
        
        assert stats["total_points"] == 13.0
        assert stats["total_tasks"] == 2
        assert abs(stats["avg_points"] - 6.5) < 0.001
        assert stats["members_count"] == 1

    def test_get_team_stats_no_data(self, db_session, sample_team_data):
        team_service = TeamService()
        
        team = team_service.create_team(**sample_team_data)
        
        stats = team_service.get_team_stats(team.id)
        
        assert stats["total_points"] == 0.0
        assert stats["total_tasks"] == 0
        assert stats["avg_points"] == 0.0
        assert stats["members_count"] == 0