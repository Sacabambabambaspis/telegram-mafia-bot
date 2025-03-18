"""
마피아 게임 봇 메인 애플리케이션

이 파일은 텔레그램 마피아 게임 봇의 메인 애플리케이션을 정의합니다.
"""

import logging
import os
from typing import Dict, Any

from telegram import Update, ParseMode
from telegram.ext import (
    Updater, CommandHandler, CallbackContext, CallbackQueryHandler,
    MessageHandler, Filters, PicklePersistence
)

from mafia_bot.handlers.command_handlers import (
    start, help_command, menu, join, leave, open_game, 
    start_game_from_countdown, stop_game, settings_command,
    set_mafia_chat, set_lovers_chat, add_bots
)
from mafia_bot.handlers.callback_handlers import (
    help_callback, settings_callback, team_callback, night_action_callback
)
from mafia_bot.handlers.game_handlers import (
    vote_callback, night_action, lastwill_callback
)
from mafia_bot.utils.settings import SettingsManager
from mafia_bot.utils.state_utils import StateManager


# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def error_handler(update: Update, context: CallbackContext) -> None:
    """
    텔레그램 봇 오류 핸들러
    """
    logger.error(f"Update {update} caused error: {context.error}")


def main() -> None:
    """
    메인 함수
    """
    # 환경 변수에서 토큰 가져오기
    token = os.environ.get("TELEGRAM_TOKEN")
    TOKEN = "7399829204:AAHRA7KiB6srIAeK0az6ykKWplAoQnt9cww"
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    
    if not token:
        logger.error("TELEGRAM_TOKEN 환경 변수가 설정되지 않았습니다.")
        return
    
    # 설정 및 상태 관리자 초기화
    settings_manager = SettingsManager()
    state_manager = StateManager()
    
    # 영구 데이터 저장소 설정
    persistence = PicklePersistence(filename='mafia_bot_data')
    
    # 업데이터 초기화
    updater = Updater(token, persistence=persistence)
    dispatcher = updater.dispatcher
    
    # 명령어 핸들러 등록
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("menu", menu))
    dispatcher.add_handler(CommandHandler("join", join))
    dispatcher.add_handler(CommandHandler("leave", leave))
    dispatcher.add_handler(CommandHandler("open", open_game))
    dispatcher.add_handler(CommandHandler("game", start_game_from_countdown))
    dispatcher.add_handler(CommandHandler("stop", stop_game))
    dispatcher.add_handler(CommandHandler("settings", settings_command))
    dispatcher.add_handler(CommandHandler("setmafiachat", set_mafia_chat))
    dispatcher.add_handler(CommandHandler("setloverschat", set_lovers_chat))
    dispatcher.add_handler(CommandHandler("addbots", add_bots))
    dispatcher.add_handler(CommandHandler("night", night_action))
    dispatcher.add_handler(CommandHandler("lastwill", lastwill_callback))
    
    # 콜백 쿼리 핸들러 등록
    dispatcher.add_handler(CallbackQueryHandler(help_callback, pattern="^menu_"))
    dispatcher.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_"))
    dispatcher.add_handler(CallbackQueryHandler(team_callback, pattern="^team_"))
    dispatcher.add_handler(CallbackQueryHandler(night_action_callback, pattern="^night_action$"))
    dispatcher.add_handler(CallbackQueryHandler(vote_callback, pattern="^vote$"))
    dispatcher.add_handler(CallbackQueryHandler(night_action, pattern="^action_"))
    dispatcher.add_handler(CallbackQueryHandler(lastwill_callback, pattern="^lastwill$"))
    
    # 오류 핸들러 등록
    dispatcher.add_error_handler(error_handler)
    
    # 봇 시작
    updater.start_polling()
    logger.info("마피아 게임 봇이 시작되었습니다.")
    
    # 봇이 종료될 때까지 실행
    updater.idle()


if __name__ == '__main__':
    main()
