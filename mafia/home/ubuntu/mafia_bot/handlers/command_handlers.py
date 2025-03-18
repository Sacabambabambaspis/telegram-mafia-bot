"""
명령어 핸들러 모듈

이 모듈은 마피아 게임의 텔레그램 명령어 핸들러들을 정의합니다.
"""

import logging
import random
from typing import Dict, List, Optional, Set, Tuple, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from mafia_bot.game.game_manager import GameManager

# 게임 상태 변수
game_managers: Dict[int, GameManager] = {}
DEFAULT_SETTINGS = {
    "day_duration": 60,  # 낮 지속 시간 (초)
    "night_duration": 30,  # 밤 지속 시간 (초)
    "mafia_kill_mode": "team",  # "team" 또는 "individual"
    "sub_role_enabled": True,
    "enabled_roles": {
        "마피아": True,
        "탐정": True,
        "의사": True,
        "기자": True,
        "선동가": True,
        "시민": True,
        "연쇄 살인마": True,
        "숭배자": True,
        "큐피드": True,
        "도둑": True,
    },
    "role_counts": {
        "마피아": 1,
        "탐정": 1,
        "의사": 1,
        "기자": 1,
        "선동가": 1,
        "시민": 2,
        "연쇄 살인마": 0,
        "숭배자": 0,
        "큐피드": 0,
        "도둑": 0,
    }
}


def get_or_create_game_manager(chat_id: int) -> GameManager:
    """
    채팅방 ID에 해당하는 게임 관리자를 가져오거나 생성합니다.
    
    Args:
        chat_id: 채팅방 ID
        
    Returns:
        게임 관리자
    """
    if chat_id not in game_managers:
        game_managers[chat_id] = GameManager(DEFAULT_SETTINGS.copy(), chat_id)
    
    return game_managers[chat_id]


def start(update: Update, context: CallbackContext) -> None:
    """
    /start 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    
    # 개인 채팅인 경우
    if chat_id > 0:
        text = "안녕하세요! 마피아 게임 봇입니다.\n\n"
        text += "그룹 채팅에 저를 초대하고 /menu 명령어로 게임을 시작하세요."
        
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 그룹 채팅인 경우
    text = "안녕하세요! 마피아 게임 봇입니다.\n\n"
    text += "/menu 명령어로 게임 메뉴를 열 수 있습니다."
    
    context.bot.send_message(chat_id=chat_id, text=text)


def help_command(update: Update, context: CallbackContext) -> None:
    """
    /help 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    
    text = "🎮 *마피아 게임 봇 도움말*\n\n"
    text += "이 봇은 텔레그램에서 마피아 게임을 즐길 수 있게 해줍니다.\n\n"
    text += "*기본 명령어:*\n"
    text += "/menu - 게임 메뉴 열기\n"
    text += "/join - 게임 참여하기\n"
    text += "/leave - 게임 나가기\n"
    text += "/open - 새 게임 열기\n"
    text += "/game - 게임 시작하기\n"
    text += "/stop - 게임 중단하기\n"
    text += "/settings - 게임 설정 변경하기 (관리자만 가능)\n\n"
    text += "*게임 규칙:*\n"
    text += "1. 낮에는 토론과 투표를 통해 마피아로 의심되는 사람을 처형합니다.\n"
    text += "2. 밤에는 각자의 역할에 맞는 행동을 수행합니다.\n"
    text += "3. 마피아는 밤에 시민을 죽이고, 시민은 마피아를 모두 찾아내야 합니다.\n"
    text += "4. 중립 역할은 각자의 승리 조건이 있습니다.\n\n"
    text += "자세한 역할 정보는 게임 메뉴에서 확인할 수 있습니다."
    
    context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")


def menu(update: Update, context: CallbackContext) -> None:
    """
    /menu 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    
    # 개인 채팅인 경우
    if chat_id > 0:
        text = "이 명령어는 그룹 채팅에서만 사용할 수 있습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    game_status = game_manager.get_game_status()
    
    # 게임 상태에 따른 메뉴 버튼 생성
    keyboard = []
    
    if not game_status["game_started"]:
        keyboard.extend([
            [InlineKeyboardButton("게임 참여", callback_data="menu_join"),
             InlineKeyboardButton("게임 나가기", callback_data="menu_leave")],
            [InlineKeyboardButton("역할 정보", callback_data="menu_roleinfo"),
             InlineKeyboardButton("게임 열기", callback_data="menu_open")],
            [InlineKeyboardButton("게임 시작", callback_data="menu_game"),
             InlineKeyboardButton("설정", callback_data="menu_settings")]
        ])
    else:
        keyboard.extend([
            [InlineKeyboardButton("게임 상태", callback_data="menu_status"),
             InlineKeyboardButton("게임 중단", callback_data="menu_stop")],
            [InlineKeyboardButton("마피아 채팅 설정", callback_data="menu_mafiamsg"),
             InlineKeyboardButton("연인 채팅 설정", callback_data="menu_loversmsg")]
        ])
    
    # 테스트용 봇 추가 버튼
    keyboard.append([InlineKeyboardButton("테스트 봇 추가", callback_data="menu_addbots")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "🎮 *마피아 게임 메뉴*\n\n"
    
    if not game_status["game_started"]:
        text += "게임이 아직 시작되지 않았습니다.\n"
        text += f"현재 참가자: {game_status['player_count']}명\n\n"
        text += "게임에 참여하려면 '게임 참여' 버튼을 누르세요."
    else:
        text += f"게임 진행 중: {game_status['day_count']}일차 {game_status['phase']}\n"
        text += f"남은 시간: {game_status['remaining_time']}초\n"
        text += f"생존자: {game_status['alive_count']}명\n\n"
        text += "게임을 중단하려면 '게임 중단' 버튼을 누르세요."
    
    context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


def join(update: Update, context: CallbackContext) -> None:
    """
    /join 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # 개인 채팅인 경우
    if chat_id > 0:
        text = "이 명령어는 그룹 채팅에서만 사용할 수 있습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임이 이미 시작된 경우
    if game_manager.game_started:
        text = "게임이 이미 시작되었습니다. 다음 게임을 기다려주세요."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 플레이어 추가
    success = game_manager.add_player(user.id, user.first_name, user.id)
    
    if success:
        text = f"{user.first_name}님이 게임에 참여했습니다!"
        
        # 개인 메시지 보내기
        try:
            private_text = f"안녕하세요, {user.first_name}님! 마피아 게임에 참여하셨습니다.\n\n"
            private_text += "게임이 시작되면 역할이 배정되고 개인 메시지로 알림을 받게 됩니다.\n"
            private_text += "게임 진행 상황을 확인하려면 그룹 채팅을 참고하세요."
            
            context.bot.send_message(chat_id=user.id, text=private_text)
        except Exception as e:
            text += f"\n\n⚠️ {user.first_name}님에게 개인 메시지를 보낼 수 없습니다. "
            text += "봇과의 개인 채팅을 시작해주세요."
    else:
        text = f"{user.first_name}님은 이미 게임에 참여 중입니다."
    
    # 플레이어 목록 업데이트
    text += f"\n\n현재 참가자: {len(game_manager.players)}명"
    text += "\n" + game_manager.get_player_list_text()
    
    context.bot.send_message(chat_id=chat_id, text=text)


def leave(update: Update, context: CallbackContext) -> None:
    """
    /leave 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # 개인 채팅인 경우
    if chat_id > 0:
        text = "이 명령어는 그룹 채팅에서만 사용할 수 있습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임이 이미 시작된 경우
    if game_manager.game_started:
        text = "게임이 이미 시작되었습니다. 중도 퇴장은 불가능합니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 플레이어 제거
    success = game_manager.remove_player(user.id)
    
    if success:
        text = f"{user.first_name}님이 게임에서 나갔습니다."
    else:
        text = f"{user.first_name}님은 게임에 참여하지 않았습니다."
    
    # 플레이어 목록 업데이트
    text += f"\n\n현재 참가자: {len(game_manager.players)}명"
    if game_manager.players:
        text += "\n" + game_manager.get_player_list_text()
    
    context.bot.send_message(chat_id=chat_id, text=text)


def open_game(update: Update, context: CallbackContext) -> None:
    """
    /open 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    
    # 개인 채팅인 경우
    if chat_id > 0:
        text = "이 명령어는 그룹 채팅에서만 사용할 수 있습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임이 이미 시작된 경우
    if game_manager.game_started:
        text = "게임이 이미 시작되었습니다. 새 게임을 열려면 먼저 현재 게임을 중단하세요."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 새 게임 열기 (기존 플레이어 초기화)
    game_managers[chat_id] = GameManager(DEFAULT_SETTINGS.copy(), chat_id)
    
    # 참여 버튼이 있는 메시지 전송
    keyboard = [[InlineKeyboardButton("게임 참여", callback_data="menu_join")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "🎮 새로운 마피아 게임이 열렸습니다!\n\n"
    text += "게임에 참여하려면 아래 버튼을 누르세요.\n"
    text += "충분한 인원이 모이면 '/game' 명령어로 게임을 시작할 수 있습니다."
    
    context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )


def start_game_from_countdown(update: Update, context: CallbackContext) -> None:
    """
    /game 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    
    # 개인 채팅인 경우
    if chat_id > 0:
        text = "이 명령어는 그룹 채팅에서만 사용할 수 있습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임이 이미 시작된 경우
    if game_manager.game_started:
        text = "게임이 이미 시작되었습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 플레이어 수 확인
    if len(game_manager.players) < 4:
        text = "게임을 시작하려면 최소 4명의 플레이어가 필요합니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 카운트다운 메시지
    text = "🎮 게임이 곧 시작됩니다!\n\n"
    text += "참가자 목록:\n" + game_manager.get_player_list_text()
    text += "\n5초 후 게임이 시작됩니다..."
    
    message = context.bot.send_message(chat_id=chat_id, text=text)
    
    # 5초 후 게임 시작
    context.job_queue.run_once(
        start_game_callback,
        5,
        context={'chat_id': chat_id, 'message_id': message.message_id}
    )


def start_game_callback(context: CallbackContext) -> None:
    """
    게임 시작 콜백 함수
    """
    job = context.job
    chat_id = job.context['chat_id']
    message_id = job.context['message_id']
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임 시작
    success, message = game_manager.start_game()
    
    if success:
        # 게임 시작 메시지 업데이트
        text = "🎮 마피아 게임이 시작되었습니다!\n\n"
        text += "각 플레이어에게 역할이 배정되었습니다. 개인 메시지를 확인하세요.\n\n"
        text += "첫 번째 밤이 시작됩니다. 각자의 역할에 맞는 행동을 수행하세요."
        
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text
        )
        
        # 각 플레이어에게 역할 정보 전송
        for player_id, player in game_manager.players.items():
            try:
                role_info = player.get_role_info()
                
                text = f"🎭 당신의 역할: {player.role.name}\n\n"
                text += role_info
                
                # 밤 행동이 있는 역할인 경우 행동 버튼 추가
                if player.role.night_action:
                    keyboard = [[InlineKeyboardButton("밤 행동 수행", callback_data="night_action")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    context.bot.send_message(
                        chat_id=player_id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                else:
                    context.bot.send_message(
                        chat_id=player_id,
                        text=text,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logging.error(f"Failed to send role info to player {player_id}: {e}")
    else:
        # 게임 시작 실패 메시지
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"게임 시작 실패: {message}"
        )


def stop_game(update: Update, context: CallbackContext) -> None:
    """
    /stop 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    
    # 개인 채팅인 경우
    if chat_id > 0:
        text = "이 명령어는 그룹 채팅에서만 사용할 수 있습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임이 시작되지 않은 경우
    if not game_manager.game_started:
        text = "현재 진행 중인 게임이 없습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 게임 중단
    game_manager.stop_game()
    
    text = "게임이 중단되었습니다.\n"
    text += "새 게임을 시작하려면 /open 명령어를 사용하세요."
    
    context.bot.send_message(chat_id=chat_id, text=text)


def settings_command(update: Update, context: CallbackContext) -> None:
    """
    /settings 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # 개인 채팅인 경우
    if chat_id > 0:
        text = "이 명령어는 그룹 채팅에서만 사용할 수 있습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 관리자 권한 확인
    try:
        member = context.bot.get_chat_member(chat_id, user.id)
        if member.status not in ("administrator", "creator"):
            text = "설정 변경은 관리자만 가능합니다."
            context.bot.send_message(chat_id=chat_id, text=text)
            return
    except Exception as e:
        logging.error(f"Failed to check admin status: {e}")
        text = "권한 확인 중 오류가 발생했습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임이 이미 시작된 경우
    if game_manager.game_started:
        text = "게임이 이미 시작되었습니다. 설정은 게임 시작 전에만 변경할 수 있습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 설정 메뉴 표시
    keyboard = [
        [InlineKeyboardButton("낮 시간 설정", callback_data="settings_day"),
         InlineKeyboardButton("밤 시간 설정", callback_data="settings_night")],
        [InlineKeyboardButton("마피아 공격 방식", callback_data="settings_mafia"),
         InlineKeyboardButton("서브직업 사용", callback_data="settings_subrole")],
        [InlineKeyboardButton("역할 설정", callback_data="settings_roles"),
         InlineKeyboardButton("역할 수량 설정", callback_data="settings_rolecount")],
        [InlineKeyboardButton("설정 저장", callback_data="settings_save"),
         InlineKeyboardButton("메뉴로 돌아가기", callback_data="menu_back")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "⚙️ *게임 설정 메뉴*\n\n"
    text += "변경할 설정을 선택하세요.\n"
    text += "설정은 게임 시작 전에만 변경할 수 있습니다."
    
    context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


def set_mafia_chat(update: Update, context: CallbackContext) -> None:
    """
    /setmafiachat 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 마피아 채팅방 설정
    game_manager.set_mafia_chat(chat_id)
    
    text = "이 채팅방이 마피아 채팅방으로 설정되었습니다.\n"
    text += "이제 마피아 팀원들만 이 채팅방에 초대하세요."
    
    context.bot.send_message(chat_id=chat_id, text=text)


def set_lovers_chat(update: Update, context: CallbackContext) -> None:
    """
    /setloverschat 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 연인 채팅방 설정
    game_manager.set_lovers_chat(chat_id)
    
    text = "이 채팅방이 연인 채팅방으로 설정되었습니다.\n"
    text += "이제 연인 관계인 플레이어들만 이 채팅방에 초대하세요."
    
    context.bot.send_message(chat_id=chat_id, text=text)


def add_bots(update: Update, context: CallbackContext) -> None:
    """
    /addbots 명령어 핸들러 (테스트용)
    """
    chat_id = update.effective_chat.id
    
    # 개인 채팅인 경우
    if chat_id > 0:
        text = "이 명령어는 그룹 채팅에서만 사용할 수 있습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임이 이미 시작된 경우
    if game_manager.game_started:
        text = "게임이 이미 시작되었습니다. 봇은 게임 시작 전에만 추가할 수 있습니다."
        context.bot.send_message(chat_id=chat_id, text=text)
        return
    
    # 테스트용 봇 추가 (5명)
    bot_names = ["봇1", "봇2", "봇3", "봇4", "봇5"]
    added_count = 0
    
    for i<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>