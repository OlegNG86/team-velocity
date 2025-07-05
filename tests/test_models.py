import pytest
from datetime import datetime
from core.models import User, StoryPoint, Team, TeamMember


class TestUser:
    def test_user_creation(self, db_session, sample_user_data):
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.telegram_id == sample_user_data["telegram_id"]
        assert user.username == sample_user_data["username"]
        assert user.first_name == sample_user_data["first_name"]
        assert user.last_name == sample_user_data["last_name"]
        assert user.is_active == 1
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_unique_telegram_id(self, db_session, sample_user_data):
        user1 = User(**sample_user_data)
        user2_data = sample_user_data.copy()
        user2_data["telegram_id"] = sample_user_data["telegram_id"]  # Same telegram_id
        user2 = User(**user2_data)
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        
        with pytest.raises(Exception):
            db_session.commit()

    def test_user_story_points_relationship(self, db_session, sample_user_data):
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        story_point = StoryPoint(
            user_id=user.id,
            points=5.0,
            description="Test task",
            date_completed=datetime.utcnow()
        )
        db_session.add(story_point)
        db_session.commit()
        
        assert len(user.story_points) == 1
        assert user.story_points[0].points == 5.0


class TestStoryPoint:
    def test_story_point_creation(self, db_session, sample_user_data):
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        story_point = StoryPoint(
            user_id=user.id,
            points=8.0,
            description="Complex feature implementation",
            date_completed=datetime.utcnow()
        )
        db_session.add(story_point)
        db_session.commit()
        
        assert story_point.id is not None
        assert story_point.user_id == user.id
        assert story_point.points == 8.0
        assert story_point.description == "Complex feature implementation"
        assert story_point.date_completed is not None
        assert story_point.created_at is not None
        assert story_point.updated_at is not None

    def test_story_point_user_relationship(self, db_session, sample_user_data):
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        story_point = StoryPoint(
            user_id=user.id,
            points=3.0,
            description="Bug fix",
            date_completed=datetime.utcnow()
        )
        db_session.add(story_point)
        db_session.commit()
        
        assert story_point.user.telegram_id == user.telegram_id
        assert story_point.user.first_name == user.first_name

    def test_story_point_required_fields(self, db_session, sample_user_data):
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        story_point = StoryPoint(
            user_id=user.id,
            points=2.0,
            date_completed=datetime.utcnow()
        )
        db_session.add(story_point)
        db_session.commit()
        
        assert story_point.id is not None
        assert story_point.description is None


class TestTeam:
    def test_team_creation(self, db_session, sample_team_data):
        team = Team(**sample_team_data)
        db_session.add(team)
        db_session.commit()
        
        assert team.id is not None
        assert team.name == sample_team_data["name"]
        assert team.description == sample_team_data["description"]
        assert team.created_at is not None
        assert team.updated_at is not None

    def test_team_required_fields(self, db_session):
        team = Team(name="Minimal Team")
        db_session.add(team)
        db_session.commit()
        
        assert team.id is not None
        assert team.name == "Minimal Team"
        assert team.description is None

    def test_team_members_relationship(self, db_session, sample_team_data, sample_user_data):
        team = Team(**sample_team_data)
        user = User(**sample_user_data)
        
        db_session.add(team)
        db_session.add(user)
        db_session.commit()
        
        team_member = TeamMember(
            team_id=team.id,
            user_id=user.id,
            role="developer"
        )
        db_session.add(team_member)
        db_session.commit()
        
        assert len(team.team_members) == 1
        assert team.team_members[0].user.telegram_id == user.telegram_id


class TestTeamMember:
    def test_team_member_creation(self, db_session, sample_team_data, sample_user_data):
        team = Team(**sample_team_data)
        user = User(**sample_user_data)
        
        db_session.add(team)
        db_session.add(user)
        db_session.commit()
        
        team_member = TeamMember(
            team_id=team.id,
            user_id=user.id,
            role="lead"
        )
        db_session.add(team_member)
        db_session.commit()
        
        assert team_member.id is not None
        assert team_member.team_id == team.id
        assert team_member.user_id == user.id
        assert team_member.role == "lead"
        assert team_member.joined_at is not None

    def test_team_member_default_role(self, db_session, sample_team_data, sample_user_data):
        team = Team(**sample_team_data)
        user = User(**sample_user_data)
        
        db_session.add(team)
        db_session.add(user)
        db_session.commit()
        
        team_member = TeamMember(
            team_id=team.id,
            user_id=user.id
        )
        db_session.add(team_member)
        db_session.commit()
        
        assert team_member.role == "member"

    def test_team_member_relationships(self, db_session, sample_team_data, sample_user_data):
        team = Team(**sample_team_data)
        user = User(**sample_user_data)
        
        db_session.add(team)
        db_session.add(user)
        db_session.commit()
        
        team_member = TeamMember(
            team_id=team.id,
            user_id=user.id
        )
        db_session.add(team_member)
        db_session.commit()
        
        assert team_member.team.name == team.name
        assert team_member.user.telegram_id == user.telegram_id