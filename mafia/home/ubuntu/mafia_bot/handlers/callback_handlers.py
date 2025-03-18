"""
콜백 쿼리 핸들러 모듈

이 모듈은 마피아 게임의 텔레그램 콜백 쿼리 핸들러들을 정의합니다.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from mafia_bot.handlers.command_handlers import (
    get_or_create_game_manager, join, leave, open_game, 
    start_game_from_countdown, stop_game, settings_command, menu
)
from mafia_bot.roles.base_role import BaseRole


def help_callback(update: Update, context: CallbackContext) -> None:
    """
    도움말 메뉴 콜백 핸들러
    """
    query = update.callback_query
    query.answer()
    
    # 콜백 데이터에 따라 다른 함수 호출
    callback_mapping = {
        "menu_join": join,
        "menu_leave": leave,
        "menu_roleinfo": role_info,
        "menu_open": open_game,
        "menu_game": start_game_from_countdown,
        "menu_stop": stop_game,
        "menu_settings": settings_command,
        "menu_back": menu,
        "menu_addbots": add_bots_callback
    }
    
    callback_func = callback_mapping.get(query.data)
    if callback_func:
        callback_func(update, context)
    else:
        # 알 수 없는 콜백 데이터인 경우 메뉴로 돌아감
        menu(update, context)


def settings_callback(update: Update, context: CallbackContext) -> None:
    """
    설정 메뉴 콜백 핸들러
    """
    query = update.callback_query
    query.answer()
    
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # 관리자 권한 확인
    try:
        member = context.bot.get_chat_member(chat_id, user.id)
        if member.status not in ("administrator", "creator"):
            query.edit_message_text("설정 변경은 관리자만 가능합니다.")
            return
    except Exception as e:
        logging.error(f"Failed to check admin status: {e}")
        query.edit_message_text("권한 확인 중 오류가 발생했습니다.")
        return
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임이 이미 시작된 경우
    if game_manager.game_started:
        query.edit_message_text("게임이 이미 시작되었습니다. 설정은 게임 시작 전에만 변경할 수 있습니다.")
        return
    
    # 설정 데이터 처리
    data = query.data
    
    if data == "settings_day":
        # 낮 시간 설정
        text = f"현재 낮 시간: {game_manager.settings.get('day_duration', 60)}초\n"
        text += "변경하려면 /set_day <초> 명령어를 사용하세요."
        query.edit_message_text(text=text)
    
    elif data == "settings_night":
        # 밤 시간 설정
        text = f"현재 밤 시간: {game_manager.settings.get('night_duration', 30)}초\n"
        text += "변경하려면 /set_night <초> 명령어를 사용하세요."
        query.edit_message_text(text=text)
    
    elif data == "settings_mafia":
        # 마피아 공격 방식 설정
        current_mode = game_manager.settings.get("mafia_kill_mode", "team")
        
        keyboard = [
            [InlineKeyboardButton("팀 투표 (현재: " + ("✓" if current_mode == "team" else "✗") + ")",
                                 callback_data="settings_mafia_team")],
            [InlineKeyboardButton("개인 선택 (현재: " + ("✓" if current_mode == "individual" else "✗") + ")",
                                 callback_data="settings_mafia_individual")],
            [InlineKeyboardButton("설정으로 돌아가기", callback_data="menu_settings")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "마피아 공격 방식을 선택하세요:\n\n"
        text += "- 팀 투표: 마피아 팀원들이 투표로 공격 대상을 결정합니다.\n"
        text += "- 개인 선택: 각 마피아가 개별적으로 공격 대상을 선택합니다."
        
        query.edit_message_text(text=text, reply_markup=reply_markup)
    
    elif data == "settings_mafia_team":
        # 마피아 공격 방식을 팀 투표로 설정
        game_manager.settings["mafia_kill_mode"] = "team"
        settings_callback(update, context)  # 설정 메뉴로 돌아가기
    
    elif data == "settings_mafia_individual":
        # 마피아 공격 방식을 개인 선택으로 설정
        game_manager.settings["mafia_kill_mode"] = "individual"
        settings_callback(update, context)  # 설정 메뉴로 돌아가기
    
    elif data == "settings_subrole":
        # 서브직업 사용 설정
        current_enabled = game_manager.settings.get("sub_role_enabled", True)
        
        keyboard = [
            [InlineKeyboardButton("사용 (현재: " + ("✓" if current_enabled else "✗") + ")",
                                 callback_data="settings_subrole_enable")],
            [InlineKeyboardButton("사용 안 함 (현재: " + ("✓" if not current_enabled else "✗") + ")",
                                 callback_data="settings_subrole_disable")],
            [InlineKeyboardButton("설정으로 돌아가기", callback_data="menu_settings")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "서브직업 사용 여부를 선택하세요:\n\n"
        text += "- 사용: 정신병자 등의 서브직업이 게임에 추가됩니다.\n"
        text += "- 사용 안 함: 서브직업 없이 기본 역할만 사용합니다."
        
        query.edit_message_text(text=text, reply_markup=reply_markup)
    
    elif data == "settings_subrole_enable":
        # 서브직업 사용 설정
        game_manager.settings["sub_role_enabled"] = True
        settings_callback(update, context)  # 설정 메뉴로 돌아가기
    
    elif data == "settings_subrole_disable":
        # 서브직업 사용 안 함 설정
        game_manager.settings["sub_role_enabled"] = False
        settings_callback(update, context)  # 설정 메뉴로 돌아가기
    
    elif data == "settings_roles":
        # 역할 활성화/비활성화 설정
        enabled_roles = game_manager.settings.get("enabled_roles", {})
        
        keyboard = []
        for role_name in sorted(enabled_roles.keys()):
            enabled = enabled_roles.get(role_name, True)
            keyboard.append([
                InlineKeyboardButton(
                    f"{role_name} (현재: {'활성화' if enabled else '비활성화'})",
                    callback_data=f"settings_role_{role_name}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("설정으로 돌아가기", callback_data="menu_settings")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "활성화/비활성화할 역할을 선택하세요:"
        
        query.edit_message_text(text=text, reply_markup=reply_markup)
    
    elif data.startswith("settings_role_"):
        # 특정 역할 활성화/비활성화 토글
        role_name = data.replace("settings_role_", "")
        
        if role_name in game_manager.settings.get("enabled_roles", {}):
            current_state = game_manager.settings["enabled_roles"].get(role_name, True)
            game_manager.settings["enabled_roles"][role_name] = not current_state
        
        # 역할 설정 메뉴로 돌아가기
        settings_callback(update, context)
    
    elif data == "settings_rolecount":
        # 역할 수량 설정
        role_counts = game_manager.settings.get("role_counts", {})
        enabled_roles = game_manager.settings.get("enabled_roles", {})
        
        keyboard = []
        for role_name, enabled in sorted(enabled_roles.items()):
            if enabled:
                count = role_counts.get(role_name, 0)
                keyboard.append([
                    InlineKeyboardButton(
                        f"{role_name}: {count}명",
                        callback_data=f"settings_rolecount_{role_name}"
                    )
                ])
        
        keyboard.append([InlineKeyboardButton("설정으로 돌아가기", callback_data="menu_settings")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "수량을 변경할 역할을 선택하세요:"
        
        query.edit_message_text(text=text, reply_markup=reply_markup)
    
    elif data.startswith("settings_rolecount_"):
        # 특정 역할 수량 설정
        role_name = data.replace("settings_rolecount_", "")
        
        if role_name in game_manager.settings.get("role_counts", {}):
            current_count = game_manager.settings["role_counts"].get(role_name, 0)
            
            keyboard = []
            for i in range(6):  # 0~5명
                keyboard.append([
                    InlineKeyboardButton(
                        f"{i}명 (현재: " + ("✓" if current_count == i else "✗") + ")",
                        callback_data=f"settings_setcount_{role_name}_{i}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("역할 수량 설정으로 돌아가기", callback_data="settings_rolecount")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = f"{role_name} 역할의 수량을 선택하세요:"
            
            query.edit_message_text(text=text, reply_markup=reply_markup)
    
    elif data.startswith("settings_setcount_"):
        # 특정 역할 수량 값 설정
        _, role_name, count = data.split("_")[1:]
        count = int(count)
        
        if role_name in game_manager.settings.get("role_counts", {}):
            game_manager.settings["role_counts"][role_name] = count
        
        # 역할 수량 설정 메뉴로 돌아가기
        update.callback_query.data = "settings_rolecount"
        settings_callback(update, context)
    
    elif data == "settings_save":
        # 설정 저장
        text = "설정이 저장되었습니다."
        query.edit_message_text(text=text)
    
    else:
        # 알 수 없는 설정 데이터인 경우 설정 메뉴로 돌아감
        settings_command(update, context)


def team_callback(update: Update, context: CallbackContext) -> None:
    """
    팀 정보 콜백 핸들러
    """
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    # 팀 정보 표시
    if data.startswith("team_"):
        team_name = data.replace("team_", "")
        
        # 팀별 역할 정보
        team_roles = {
            "마피아팀": ["마피아"],
            "시민팀": ["탐정", "의사", "기자", "선동가", "시민"],
            "중립팀": ["연쇄 살인마", "숭배자", "큐피드", "도둑"]
        }
        
        # 역할 설명
        role_descriptions = {
            "마피아": "😈 **마피아**\n어둠 속에서 작전을 수행합니다.",
            "탐정": "🕵️ **탐정**\n한 명의 정체를 조사합니다.",
            "의사": "👩‍⚕️ **의사**\n한 명을 치료해 공격을 막습니다.",
            "기자": "📰 **기자**\n밤 방문 기록을 수집합니다.",
            "선동가": "📢 **선동가**\n투표에서 미리 2표를 확보합니다.",
            "시민": "👤 **시민**\n토론과 투표에 참여합니다.",
            "연쇄 살인마": "🔪 **연쇄 살인마**\n독자적으로 암살합니다.",
            "숭배자": "🙏 **숭배자**\n다른 플레이어를 숭배자로 전환합니다.",
            "큐피드": "💘 **큐피드**\n두 명을 연인으로 묶습니다.",
            "도둑": "🦹 **도둑**\n타겟의 역할을 대신합니다."
        }
        
        if team_name in team_roles:
            text = f"**{team_name} 역할 목록**\n\n"
            
            for role in team_roles[team_name]:
                if role in role_descriptions:
                    text += f"{role_descriptions[role]}\n\n"
            
            query.edit_message_text(text=text, parse_mode="Markdown")
        else:
            query.edit_message_text(text="존재하지 않는 팀입니다.")


def role_info(update: Update, context: CallbackContext) -> None:
    """
    역할 정보 명령어 핸들러
    """
    chat_id = update.effective_chat.id
    
    # 팀별 버튼 생성
    keyboard = [
        [InlineKeyboardButton("마피아팀 보기", callback_data="team_마피아팀")],
        [InlineKeyboardButton("시민팀 보기", callback_data="team_시민팀")],
        [InlineKeyboardButton("중립팀 보기", callback_data="team_중립팀")],
        [InlineKeyboardButton("메뉴로 돌아가기", callback_data="menu_back")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "팀별 역할 정보를 확인하세요:"
    
    if update.callback_query:
        update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )


def night_action_callback(update: Update, context: CallbackContext) -> None:
    """
    밤 행동 콜백 핸들러
    """
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    
    # 게임 관리자 찾기
    game_manager = None
    for chat_id, manager in get_or_create_game_manager(0).__class__.__dict__.get("game_managers", {}).items():
        if user_id in manager.players:
            game_manager = manager
            break
    
    if not game_manager:
        query.edit_message_text("게임을 찾을 수 없습니다.")
        return
    
    # 게임이 시작되지 않았거나 밤 단계가 아닌 경우
    if not game_manager.game_started or game_manager.phase_manager.current_phase != "night":
        query.edit_message_text("현재 밤 행동을 수행할 수 없습니다.")
        return
    
    # 플레이어가 살아있지 않은 경우
    if user_id not in game_manager.players or not game_manager.players[user_id].alive:
        query.edit_message_text("당신은 이미 사망했습니다.")
        return
    
    # 플레이어 역할이 밤 행동이 없는 경우
    player = game_manager.players[user_id]
    if not player.role or not player.role.night_action:
        query.edit_message_text("당신의 역할은 밤 행동이 없습니다.")
        return
    
    # 밤 행동 대상 목록 가져오기
    targets = game_manager.get_night_action_targets(user_id)
    
    if not targets:
        query.edit_message_text("현재 선택할 수 있는 대상이 없습니다.")
        return
    
    # 대상 선택 버튼 생성
    keyboard = []
    for target_id in targets:
        target_name = game_manager.get_player_name(target_id)
        keyboard.append([
            InlineKeyboardButton(
                target_name,
                callback_data=f"action_{target_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"당신의 역할: {player.role.name}\n\n"
    text += "밤 행동 대상을 선택하세요:"
    
    query.edit_message_text(text=text, reply_markup=reply_markup)


def add_bots_callback(update: Update, context: CallbackContext) -> None:
    """
    테스트용 봇 추가 콜백 핸들러
    """
    query = update.callback_query
    query.answer()
    
    chat_id = update.effective_chat.id
    
    # 개인 채팅인 경우
    if chat_id > 0:
        query.edit_message_text("이 기능은 그룹 채팅에서만 사용할 수 있습니다.")
        return
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임이 이미 시작된 경우
    if game_manager.game_started:
        query.edit_message_text("게임이 이미 시작되었습니다. 봇은 게임 시작 전에만 추가할 수 있습니다.")
        return
    
    # 테스트용 봇 추가 (5명)
    bot_names = ["봇1", "봇2", "봇3", "봇4", "봇5"]
    added_count = 0
    
    for i, name in enumerate(bot_names):
        bot_id = -100 - i  # 음수 ID 사용 (실제 사용자와 겹치지 않도록)
        if game_manager.add_player(bot_id, name, chat_id):
            added_count += 1
    
    text = f"테스트용 봇 {added_count}명이 추가되었습니다.\n\n"
    text += "현재 참가자 목록:\n" + game_manager.get_player_list_text()
    
    query.edit_message_text(text=text)
