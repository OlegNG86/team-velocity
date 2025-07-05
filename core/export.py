import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import pandas as pd
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from core.models import User, StoryPoint, Team, TeamMember
from db.database import get_session


class ExportService:
    def __init__(self):
        pass

    async def export_user_data_csv(
        self, 
        telegram_id: str, 
        days: int = 30
    ) -> io.StringIO:
        """Export user's story points to CSV format"""
        async with get_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                raise ValueError(f"User with telegram_id {telegram_id} not found")
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            story_points = session.query(StoryPoint).filter(
                StoryPoint.user_id == user.id,
                StoryPoint.date_completed >= start_date
            ).order_by(desc(StoryPoint.date_completed)).all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Дата',
                'Story Points',
                'Описание',
                'Дата создания'
            ])
            
            # Write data
            for sp in story_points:
                writer.writerow([
                    sp.date_completed.strftime('%Y-%m-%d %H:%M:%S'),
                    sp.points,
                    sp.description or '',
                    sp.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            output.seek(0)
            return output

    async def export_team_data_csv(
        self, 
        team_id: int, 
        days: int = 30
    ) -> io.StringIO:
        """Export team's story points to CSV format"""
        async with get_session() as session:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise ValueError(f"Team with id {team_id} not found")
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get team members
            team_members = session.query(TeamMember).filter(
                TeamMember.team_id == team_id
            ).all()
            
            user_ids = [member.user_id for member in team_members]
            
            # Get story points for all team members
            story_points = session.query(
                StoryPoint, User
            ).join(
                User, StoryPoint.user_id == User.id
            ).filter(
                StoryPoint.user_id.in_(user_ids),
                StoryPoint.date_completed >= start_date
            ).order_by(desc(StoryPoint.date_completed)).all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Команда',
                'Пользователь',
                'Дата',
                'Story Points',
                'Описание'
            ])
            
            # Write data
            for sp, user in story_points:
                user_name = user.first_name or user.username or "Неизвестный"
                if user.last_name:
                    user_name += f" {user.last_name}"
                
                writer.writerow([
                    team.name,
                    user_name,
                    sp.date_completed.strftime('%Y-%m-%d %H:%M:%S'),
                    sp.points,
                    sp.description or ''
                ])
            
            output.seek(0)
            return output

    async def export_leaderboard_csv(
        self, 
        days: int = 30, 
        limit: int = 50
    ) -> io.StringIO:
        """Export leaderboard to CSV format"""
        async with get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            results = session.query(
                User.first_name,
                User.last_name,
                User.username,
                func.sum(StoryPoint.points).label('total_points'),
                func.count(StoryPoint.id).label('total_tasks'),
                func.avg(StoryPoint.points).label('avg_points')
            ).join(
                StoryPoint, User.id == StoryPoint.user_id
            ).filter(
                StoryPoint.date_completed >= start_date
            ).group_by(
                User.id, User.first_name, User.last_name, User.username
            ).order_by(
                desc('total_points')
            ).limit(limit).all()
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Позиция',
                'Пользователь',
                'Всего Story Points',
                'Всего задач',
                'Среднее за задачу'
            ])
            
            # Write data
            for i, result in enumerate(results, 1):
                user_name = result.first_name or result.username or "Неизвестный"
                if result.last_name:
                    user_name += f" {result.last_name}"
                
                writer.writerow([
                    i,
                    user_name,
                    float(result.total_points),
                    result.total_tasks,
                    round(float(result.avg_points), 2)
                ])
            
            output.seek(0)
            return output

    async def export_user_data_excel(
        self, 
        telegram_id: str, 
        days: int = 30
    ) -> io.BytesIO:
        """Export user's story points to Excel format"""
        async with get_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                raise ValueError(f"User with telegram_id {telegram_id} not found")
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            story_points = session.query(StoryPoint).filter(
                StoryPoint.user_id == user.id,
                StoryPoint.date_completed >= start_date
            ).order_by(desc(StoryPoint.date_completed)).all()
            
            # Prepare data for DataFrame
            data = []
            for sp in story_points:
                data.append({
                    'Дата': sp.date_completed.strftime('%Y-%m-%d %H:%M:%S'),
                    'Story Points': sp.points,
                    'Описание': sp.description or '',
                    'Дата создания': sp.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            df = pd.DataFrame(data)
            
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Story Points')
                
                # Add summary sheet
                summary_data = {
                    'Метрика': [
                        'Всего Story Points',
                        'Всего задач',
                        'Среднее за задачу',
                        'Период'
                    ],
                    'Значение': [
                        df['Story Points'].sum(),
                        len(df),
                        round(df['Story Points'].mean(), 2) if len(df) > 0 else 0,
                        f"{days} дней"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, index=False, sheet_name='Сводка')
            
            output.seek(0)
            return output

    async def get_velocity_report(
        self, 
        telegram_id: Optional[str] = None,
        team_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate velocity report for user or team"""
        async with get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            if telegram_id:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()
                if not user:
                    raise ValueError(f"User with telegram_id {telegram_id} not found")
                
                # Daily breakdown
                daily_stats = session.query(
                    func.date(StoryPoint.date_completed).label('date'),
                    func.sum(StoryPoint.points).label('points'),
                    func.count(StoryPoint.id).label('tasks')
                ).filter(
                    StoryPoint.user_id == user.id,
                    StoryPoint.date_completed >= start_date
                ).group_by(
                    func.date(StoryPoint.date_completed)
                ).order_by('date').all()
                
                report = {
                    'type': 'user',
                    'name': user.first_name or user.username or "Неизвестный",
                    'period_days': days,
                    'daily_breakdown': [
                        {
                            'date': stat.date.strftime('%Y-%m-%d'),
                            'points': float(stat.points),
                            'tasks': stat.tasks
                        }
                        for stat in daily_stats
                    ]
                }
                
            elif team_id:
                team = session.query(Team).filter(Team.id == team_id).first()
                if not team:
                    raise ValueError(f"Team with id {team_id} not found")
                
                team_members = session.query(TeamMember).filter(
                    TeamMember.team_id == team_id
                ).all()
                
                user_ids = [member.user_id for member in team_members]
                
                # Daily breakdown for team
                daily_stats = session.query(
                    func.date(StoryPoint.date_completed).label('date'),
                    func.sum(StoryPoint.points).label('points'),
                    func.count(StoryPoint.id).label('tasks')
                ).filter(
                    StoryPoint.user_id.in_(user_ids),
                    StoryPoint.date_completed >= start_date
                ).group_by(
                    func.date(StoryPoint.date_completed)
                ).order_by('date').all()
                
                report = {
                    'type': 'team',
                    'name': team.name,
                    'period_days': days,
                    'members_count': len(team_members),
                    'daily_breakdown': [
                        {
                            'date': stat.date.strftime('%Y-%m-%d'),
                            'points': float(stat.points),
                            'tasks': stat.tasks
                        }
                        for stat in daily_stats
                    ]
                }
            else:
                raise ValueError("Either telegram_id or team_id must be provided")
            
            # Calculate velocity metrics
            if report['daily_breakdown']:
                total_points = sum(day['points'] for day in report['daily_breakdown'])
                total_tasks = sum(day['tasks'] for day in report['daily_breakdown'])
                working_days = len(report['daily_breakdown'])
                
                report['summary'] = {
                    'total_points': total_points,
                    'total_tasks': total_tasks,
                    'avg_points_per_day': round(total_points / working_days, 2) if working_days > 0 else 0,
                    'avg_tasks_per_day': round(total_tasks / working_days, 2) if working_days > 0 else 0,
                    'avg_points_per_task': round(total_points / total_tasks, 2) if total_tasks > 0 else 0
                }
            else:
                report['summary'] = {
                    'total_points': 0,
                    'total_tasks': 0,
                    'avg_points_per_day': 0,
                    'avg_tasks_per_day': 0,
                    'avg_points_per_task': 0
                }
            
            return report