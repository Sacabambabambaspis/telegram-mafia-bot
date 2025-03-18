"""
게임 진행 핸들러 모듈

이 모듈은 마피아 게임의 텔레그램 게임 진행 관련 핸들러들을 정의합니다.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from mafia_bot.handlers.command_handlers import get_or_create_game_manager


def vote_callback(update: Update, context: CallbackContext) -> None:
    """
    투표 콜백 핸들러
    """
    query = update.callback_query
    query.answer()
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임이 시작되지 않았거나 낮 단계가 아닌 경우
    if not game_manager.game_started or game_manager.phase_manager.current_phase != "day":
        query.edit_message_text("현재 투표를 진행할 수 없습니다.")
        return
    
    # 플레이어가 살아있지 않은 경우
    if user_id not in game_manager.players or not game_manager.players[user_id].alive:
        query.edit_message_text("당신은 이미 사망했습니다.")
        return
    
    # 투표 대상 목록 (살아있는 다른 플레이어)
    targets = []
    for player_id, player in game_manager.players.items():
        if player.alive and player_id != user_id:
            targets.append(player_id)
    
    if not targets:
        query.edit_message_text("투표할 대상이 없습니다.")
        return
    
    # 대상 선택 버튼 생성
    keyboard = []
    for target_id in targets:
        target_name = game_manager.get_player_name(target_id)
        keyboard.append([
            InlineKeyboardButton(
                target_name,
                callback_data=f"vote_{target_id}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "투표할 대상을 선택하세요:"
    
    query.edit_message_text(text=text, reply_markup=reply_markup)


def night_action(update: Update, context: CallbackContext) -> None:
    """
    밤 행동 핸들러
    """
    query = update.callback_query
    
    if query:
        query.answer()
        user_id = update.effective_user.id
        data = query.data
        
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
        
        # 행동 대상 선택 처리
        if data.startswith("action_"):
            target_id = int(data.replace("action_", ""))
            
            # 밤 행동 수행
            success = game_manager.perform_night_action(user_id, target_id)
            
            if success:
                # 행동 결과 메시지
                result = game_manager.get_night_action_result(user_id)
                query.edit_message_text(f"행동 완료: {result}")
            else:
                query.edit_message_text("행동 수행에 실패했습니다.")
        else:
            # 밤 행동 대상 목록 표시
            from mafia_bot.handlers.callback_handlers import night_action_callback
            night_action_callback(update, context)
    else:
        # 일반 명령어로 호출된 경우
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # 개인 채팅이 아닌 경우
        if chat_id < 0:
            context.bot.send_message(
                chat_id=chat_id,
                text="이 명령어는 개인 채팅에서만 사용할 수 있습니다."
            )
            return
        
        # 게임 관리자 찾기
        game_manager = None
        for chat_id, manager in get_or_create_game_manager(0).__class__.__dict__.get("game_managers", {}).items():
            if user_id in manager.players:
                game_manager = manager
                break
        
        if not game_manager:
            context.bot.send_message(
                chat_id=chat_id,
                text="게임을 찾을 수 없습니다."
            )
            return
        
        # 게임이 시작되지 않았거나 밤 단계가 아닌 경우
        if not game_manager.game_started or game_manager.phase_manager.current_phase != "night":
            context.bot.send_message(
                chat_id=chat_id,
                text="현재 밤 행동을 수행할 수 없습니다."
            )
            return
        
        # 플레이어가 살아있지 않은 경우
        if user_id not in game_manager.players or not game_manager.players[user_id].alive:
            context.bot.send_message(
                chat_id=chat_id,
                text="당신은 이미 사망했습니다."
            )
            return
        
        # 플레이어 역할이 밤 행동이 없는 경우
        player = game_manager.players[user_id]
        if not player.role or not player.role.night_action:
            context.bot.send_message(
                chat_id=chat_id,
                text="당신의 역할은 밤 행동이 없습니다."
            )
            return
        
        # 밤 행동 대상 목록 가져오기
        targets = game_manager.get_night_action_targets(user_id)
        
        if not targets:
            context.bot.send_message(
                chat_id=chat_id,
                text="현재 선택할 수 있는 대상이 없습니다."
            )
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
        
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )


def lastwill_callback(update: Update, context: CallbackContext) -> None:
    """
    유언 작성 콜백 핸들러
    """
    query = update.callback_query
    
    if query:
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
        
        # 게임이 시작되지 않은 경우
        if not game_manager.game_started:
            query.edit_message_text("게임이 시작되지 않았습니다.")
            return
        
        # 플레이어가 게임에 참여하지 않은 경우
        if user_id not in game_manager.players:
            query.edit_message_text("당신은 게임에 참여하지 않았습니다.")
            return
        
        # 유언 작성 안내 메시지
        text = "유언을 작성하려면 '/lastwill <내용>' 형식으로 메시지를 보내세요.\n"
        text += "예: /lastwill 나는 시민이었습니다. 3번 플레이어가 마피아입니다."
        
        query.edit_message_text(text=text)
    else:
        # 일반 명령어로 호출된 경우
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # 개인 채팅이 아닌 경우
        if chat_id < 0:
            context.bot.send_message(
                chat_id=chat_id,
                text="이 명령어는 개인 채팅에서만 사용할 수 있습니다."
            )
            return
        
        # 게임 관리자 찾기
        game_manager = None
        for chat_id, manager in get_or_create_game_manager(0).__class__.__dict__.get("game_managers", {}).items():
            if user_id in manager.players:
                game_manager = manager
                break
        
        if not game_manager:
            context.bot.send_message(
                chat_id=chat_id,
                text="게임을 찾을 수 없습니다."
            )
            return
        
        # 게임이 시작되지 않은 경우
        if not game_manager.game_started:
            context.bot.send_message(
                chat_id=chat_id,
                text="게임이 시작되지 않았습니다."
            )
            return
        
        # 플레이어가 게임에 참여하지 않은 경우
        if user_id not in game_manager.players:
            context.bot.send_message(
                chat_id=chat_id,
                text="당신은 게임에 참여하지 않았습니다."
            )
            return
        
        # 명령어 인자 확인
        args = context.args
        if not args:
            # 유언 작성 안내 메시지
            text = "유언을 작성하려면 '/lastwill <내용>' 형식으로 메시지를 보내세요.\n"
            text += "예: /lastwill 나는 시민이었습니다. 3번 플레이어가 마피아입니다."
            
            context.bot.send_message(
                chat_id=chat_id,
                text=text
            )
            return
        
        # 유언 내용 저장
        last_will = " ".join(args)
        game_manager.players[user_id].set_last_will(last_will)
        
        context.bot.send_message(
            chat_id=chat_id,
            text="유언이 저장되었습니다."
        )


def add_bots(update: Update, context: CallbackContext) -> None:
    """
    테스트용 봇 추가 핸들러
    """
    chat_id = update.effective_chat.id
    
    # 개인 채팅인 경우
    if chat_id > 0:
        context.bot.send_message(
            chat_id=chat_id,
            text="이 명령어는 그룹 채팅에서만 사용할 수 있습니다."
        )
        return
    
    # 게임 관리자 가져오기
    game_manager = get_or_create_game_manager(chat_id)
    
    # 게임이 이미 시작된 경우
    if game_manager.game_started:
        context.bot.send_message(
            chat_id=chat_id,
            text="게임이 이미 시작되었습니다. 봇은 게임 시작 전에만 추가할 수 있습니다."
        )
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
    
    context.bot.send_message(
        chat_id=chat_id,
        text=text
    )
