from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from core.models import User, StoryPoint, Team, TeamMember
from db.database import get_session


class UserService:
    def __init__(self, session: Optional[Session] = None):
        self.session = session

    def get_or_create_user(
        self,
        telegram_id: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        session = self.session or get_session()
        close_session = self.session is None
        
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()

            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )
                session.add(user)
                session.commit()
                session.refresh(user)
            else:
                # Update user info if changed
                if (
                    username != user.username
                    or first_name != user.first_name
                    or last_name != user.last_name
                ):
                    user.username = username
                    user.first_name = first_name
                    user.last_name = last_name
                    user.updated_at = datetime.utcnow()
                    session.commit()

            return user
        finally:
            if close_session:
                session.close()

    def get_user_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        session = self.session or get_session()
        close_session = self.session is None
        
        try:
            return session.query(User).filter(User.telegram_id == telegram_id).first()
        finally:
            if close_session:
                session.close()


class StoryPointService:
    def add_story_point(
        self,
        telegram_id: str,
        points: float,
        description: Optional[str] = None,
        date_completed: Optional[datetime] = None,
    ) -> StoryPoint:
        if date_completed is None:
            date_completed = datetime.utcnow()

        session = get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                raise ValueError(f"User with telegram_id {telegram_id} not found")

            story_point = StoryPoint(
                user_id=user.id,
                points=points,
                description=description,
                date_completed=date_completed,
            )
            session.add(story_point)
            session.commit()
            session.refresh(story_point)

            return story_point
        finally:
            session.close()

    def get_user_stats(
        self, telegram_id: str, days: int = 30
    ) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return None

            start_date = datetime.utcnow() - timedelta(days=days)

            stats = (
                session.query(
                    func.sum(StoryPoint.points).label("total_points"),
                    func.count(StoryPoint.id).label("total_tasks"),
                    func.avg(StoryPoint.points).label("avg_points"),
                )
                .filter(
                    StoryPoint.user_id == user.id,
                    StoryPoint.date_completed >= start_date,
                )
                .first()
            )

            return {
                "total_points": float(stats.total_points) if stats.total_points else 0,
                "total_tasks": stats.total_tasks if stats.total_tasks else 0,
                "avg_points": float(stats.avg_points) if stats.avg_points else 0,
            }
        finally:
            session.close()

    def get_leaderboard(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        session = get_session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            results = (
                session.query(
                    User.first_name,
                    User.last_name,
                    User.username,
                    func.sum(StoryPoint.points).label("total_points"),
                )
                .join(StoryPoint, User.id == StoryPoint.user_id)
                .filter(StoryPoint.date_completed >= start_date)
                .group_by(User.id, User.first_name, User.last_name, User.username)
                .order_by(desc("total_points"))
                .limit(limit)
                .all()
            )

            leaderboard = []
            for result in results:
                name = result.first_name or result.username or "Неизвестный"
                if result.last_name:
                    name += f" {result.last_name}"

                leaderboard.append({"name": name, "points": float(result.total_points)})

            return leaderboard
        finally:
            session.close()

    def get_user_story_points(
        self, telegram_id: str, days: int = 30
    ) -> List[StoryPoint]:
        session = get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return []

            start_date = datetime.utcnow() - timedelta(days=days)

            return (
                session.query(StoryPoint)
                .filter(
                    StoryPoint.user_id == user.id,
                    StoryPoint.date_completed >= start_date,
                )
                .order_by(desc(StoryPoint.date_completed))
                .all()
            )
        finally:
            session.close()


class TeamService:
    def create_team(self, name: str, description: Optional[str] = None) -> Team:
        session = get_session()
        try:
            team = Team(name=name, description=description)
            session.add(team)
            session.commit()
            session.refresh(team)
            return team
        finally:
            session.close()

    def add_team_member(
        self, team_id: int, telegram_id: str, role: str = "member"
    ) -> TeamMember:
        session = get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                raise ValueError(f"User with telegram_id {telegram_id} not found")

            team_member = TeamMember(team_id=team_id, user_id=user.id, role=role)
            session.add(team_member)
            session.commit()
            session.refresh(team_member)
            return team_member
        finally:
            session.close()

    def get_team_stats(self, team_id: int, days: int = 30) -> Dict[str, Any]:
        session = get_session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            members = (
                session.query(TeamMember).filter(TeamMember.team_id == team_id).all()
            )

            user_ids = [member.user_id for member in members]

            stats = (
                session.query(
                    func.sum(StoryPoint.points).label("total_points"),
                    func.count(StoryPoint.id).label("total_tasks"),
                    func.avg(StoryPoint.points).label("avg_points"),
                )
                .filter(
                    StoryPoint.user_id.in_(user_ids),
                    StoryPoint.date_completed >= start_date,
                )
                .first()
            )

            return {
                "total_points": float(stats.total_points) if stats.total_points else 0,
                "total_tasks": stats.total_tasks if stats.total_tasks else 0,
                "avg_points": float(stats.avg_points) if stats.avg_points else 0,
                "members_count": len(members),
            }
        finally:
            session.close()
