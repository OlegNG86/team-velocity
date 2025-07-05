import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from bot.main import StoryBot
from core.models import User, StoryPoint


class TestStoryBot:
    @pytest.fixture
    def bot(self):
        return StoryBot("test_token")

    @pytest.fixture
    def mock_update(self):
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.username = "testuser"
        update.effective_user.first_name = "Test"
        update.effective_user.last_name = "User"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        context = Mock()
        context.user_data = {}
        return context

    @pytest.fixture
    def mock_callback_query(self):
        query = Mock()
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.from_user = Mock()
        query.from_user.id = 123456789
        query.from_user.username = "testuser"
        query.from_user.first_name = "Test"
        query.from_user.last_name = "User"
        return query

    @pytest.mark.asyncio
    async def test_start_command_new_user(self, bot, mock_update, mock_context):
        with patch.object(bot.user_service, 'get_or_create_user') as mock_get_or_create:
            mock_user = Mock()
            mock_get_or_create.return_value = mock_user
            
            await bot.start(mock_update, mock_context)
            
            mock_get_or_create.assert_called_once_with(
                telegram_id="123456789",
                username="testuser",
                first_name="Test",
                last_name="User"
            )
            mock_update.message.reply_text.assert_called_once()
            
            # Check that the welcome message contains the user's name
            call_args = mock_update.message.reply_text.call_args
            assert "Test" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_start_command_no_user(self, bot, mock_context):
        update = Mock()
        update.effective_user = None
        
        await bot.start(update, mock_context)
        
        # Should return early without calling any services

    @pytest.mark.asyncio
    async def test_button_callback_add_points(self, bot, mock_context):
        query = Mock()
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.data = "add_points"
        
        update = Mock()
        update.callback_query = query
        
        await bot.button_callback(update, mock_context)
        
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        assert mock_context.user_data['waiting_for_points'] == True

    @pytest.mark.asyncio
    async def test_button_callback_my_stats(self, bot, mock_context):
        query = Mock()
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.data = "my_stats"
        query.from_user = Mock()
        query.from_user.id = 123456789
        
        update = Mock()
        update.callback_query = query
        
        with patch.object(bot.story_service, 'get_user_stats') as mock_get_stats:
            mock_get_stats.return_value = {
                'total_points': 15.0,
                'total_tasks': 3,
                'avg_points': 5.0
            }
            
            await bot.button_callback(update, mock_context)
            
            query.answer.assert_called_once()
            query.edit_message_text.assert_called_once()
            
            # Check that stats are displayed
            call_args = query.edit_message_text.call_args
            assert "15" in call_args[0][0]
            assert "3" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_button_callback_leaderboard(self, bot, mock_context):
        query = Mock()
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.data = "leaderboard"
        
        update = Mock()
        update.callback_query = query
        
        with patch.object(bot.story_service, 'get_leaderboard') as mock_get_leaderboard:
            mock_get_leaderboard.return_value = [
                {"name": "User1", "points": 20.0},
                {"name": "User2", "points": 15.0}
            ]
            
            await bot.button_callback(update, mock_context)
            
            query.answer.assert_called_once()
            query.edit_message_text.assert_called_once()
            
            # Check that leaderboard is displayed
            call_args = query.edit_message_text.call_args
            assert "User1" in call_args[0][0]
            assert "20" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_button_callback_help(self, bot, mock_context):
        query = Mock()
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.data = "help"
        
        update = Mock()
        update.callback_query = query
        
        await bot.button_callback(update, mock_context)
        
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        
        # Check that help text is displayed
        call_args = query.edit_message_text.call_args
        assert "Справка" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_handle_message_waiting_for_points(self, bot, mock_update, mock_context):
        mock_context.user_data['waiting_for_points'] = True
        
        with patch.object(bot, 'process_story_points') as mock_process:
            mock_process.return_value = None
            
            await bot.handle_message(mock_update, mock_context)
            
            mock_process.assert_called_once_with(mock_update, mock_context)
            assert mock_context.user_data['waiting_for_points'] == False

    @pytest.mark.asyncio
    async def test_handle_message_not_waiting(self, bot, mock_update, mock_context):
        with patch.object(bot, 'process_story_points') as mock_process:
            await bot.handle_message(mock_update, mock_context)
            
            mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_story_points_success(self, bot, mock_update, mock_context):
        mock_update.message.text = "5 Test implementation"
        mock_update.effective_user.id = 123456789
        
        with patch.object(bot.story_service, 'add_story_point') as mock_add:
            mock_add.return_value = Mock()
            
            await bot.process_story_points(mock_update, mock_context)
            
            mock_add.assert_called_once_with(
                telegram_id="123456789",
                points=5.0,
                description="Test implementation"
            )
            mock_update.message.reply_text.assert_called_once()
            
            # Check success message
            call_args = mock_update.message.reply_text.call_args
            assert "✅" in call_args[0][0]
            assert "5" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_process_story_points_invalid_format(self, bot, mock_update, mock_context):
        mock_update.message.text = "5"  # Missing description
        
        await bot.process_story_points(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        
        # Check error message
        call_args = mock_update.message.reply_text.call_args
        assert "❌" in call_args[0][0]
        assert "Неверный формат" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_process_story_points_invalid_number(self, bot, mock_update, mock_context):
        mock_update.message.text = "invalid Test implementation"
        
        await bot.process_story_points(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        
        # Check error message
        call_args = mock_update.message.reply_text.call_args
        assert "❌" in call_args[0][0]
        assert "Неверный формат числа" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_process_story_points_negative_points(self, bot, mock_update, mock_context):
        mock_update.message.text = "-5 Test implementation"
        
        await bot.process_story_points(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        
        # Check error message
        call_args = mock_update.message.reply_text.call_args
        assert "❌" in call_args[0][0]
        assert "положительным" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_process_story_points_zero_points(self, bot, mock_update, mock_context):
        mock_update.message.text = "0 Test implementation"
        
        await bot.process_story_points(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        
        # Check error message
        call_args = mock_update.message.reply_text.call_args
        assert "❌" in call_args[0][0]
        assert "положительным" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_process_story_points_no_user(self, bot, mock_context):
        update = Mock()
        update.effective_user = None
        
        await bot.process_story_points(update, mock_context)
        
        # Should return early without processing

    @pytest.mark.asyncio
    async def test_show_user_stats_no_data(self, bot, mock_callback_query, mock_context):
        with patch.object(bot.story_service, 'get_user_stats') as mock_get_stats:
            mock_get_stats.return_value = None
            
            await bot.show_user_stats(mock_callback_query, mock_context)
            
            mock_callback_query.edit_message_text.assert_called_once()
            
            # Check no data message
            call_args = mock_callback_query.edit_message_text.call_args
            assert "нет записей" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_show_leaderboard_no_data(self, bot, mock_callback_query, mock_context):
        with patch.object(bot.story_service, 'get_leaderboard') as mock_get_leaderboard:
            mock_get_leaderboard.return_value = []
            
            await bot.show_leaderboard(mock_callback_query, mock_context)
            
            mock_callback_query.edit_message_text.assert_called_once()
            
            # Check empty leaderboard message
            call_args = mock_callback_query.edit_message_text.call_args
            assert "пуст" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_show_leaderboard_with_data(self, bot, mock_callback_query, mock_context):
        leaderboard_data = [
            {"name": "Winner", "points": 25.0},
            {"name": "Runner-up", "points": 20.0},
            {"name": "Third", "points": 15.0}
        ]
        
        with patch.object(bot.story_service, 'get_leaderboard') as mock_get_leaderboard:
            mock_get_leaderboard.return_value = leaderboard_data
            
            await bot.show_leaderboard(mock_callback_query, mock_context)
            
            mock_callback_query.edit_message_text.assert_called_once()
            
            # Check leaderboard display
            call_args = mock_callback_query.edit_message_text.call_args
            message = call_args[0][0]
            assert "🥇" in message  # Gold medal for first place
            assert "🥈" in message  # Silver medal for second place
            assert "🥉" in message  # Bronze medal for third place
            assert "Winner" in message
            assert "25" in message