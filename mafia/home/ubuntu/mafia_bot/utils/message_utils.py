"""
메시지 유틸리티 모듈

이 모듈은 마피아 게임의 텔레그램 메시지 관련 유틸리티 함수들을 제공합니다.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext


def send_message(context: CallbackContext, chat_id: int, text: str, 
                reply_markup: Optional[InlineKeyboardMarkup] = None,
                parse_mode: Optional[str] = None) -> bool:
    """
    메시지를 전송합니다.
    
    Args:
        context: 콜백 컨텍스트
        chat_id: 채팅방 ID
        text: 메시지 내용
        reply_markup: 인라인 키보드 마크업
        parse_mode: 파싱 모드
        
    Returns:
        전송 성공 여부
    """
    try:
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        logging.error(f"메시지 전송 중 오류 발생: {e}")
        return False


def send_game_status(context: CallbackContext, chat_id: int, game_manager: Any) -> bool:
    """
    게임 상태 메시지를 전송합니다.
    
    Args:
        context: 콜백 컨텍스트
        chat_id: 채팅방 ID
        game_manager: 게임 관리자
        
    Returns:
        전송 성공 여부
    """
    try:
        game_status = game_manager.get_game_status()
        
        text = "🎮 *마피아 게임 상태*\n\n"
        
        if not game_status["game_started"]:
            text += "게임이 아직 시작되지 않았습니다.\n"
            text += f"현재 참가자: {game_status['player_count']}명\n\n"
            text += game_manager.get_player_list_text()
        else:
            text += f"게임 진행 중: {game_status['day_count']}일차 {game_status['phase']}\n"
            text += f"남은 시간: {game_status['remaining_time']}초\n"
            text += f"생존자: {game_status['alive_count']}명\n"
            text += f"마피아: {game_status['mafia_count']}명 / "
            text += f"시민: {game_status['citizen_count']}명 / "
            text += f"중립: {game_status['neutral_count']}명\n\n"
            text += game_manager.get_player_list_text()
        
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown"
        )
        return True
    except Exception as e:
        logging.error(f"게임 상태 메시지 전송 중 오류 발생: {e}")
        return False


def send_role_info(context: CallbackContext, chat_id: int, player: Any) -> bool:
    """
    역할 정보 메시지를 전송합니다.
    
    Args:
        context: 콜백 컨텍스트
        chat_id: 채팅방 ID
        player: 플레이어 객체
        
    Returns:
        전송 성공 여부
    """
    try:
        if not player.role:
            return False
        
        role_info = player.get_role_info()
        
        text = f"🎭 당신의 역할: {player.role.name}\n\n"
        text += role_info
        
        # 밤 행동이 있는 역할인 경우 행동 버튼 추가
        if player.role.night_action:
            keyboard = [[InlineKeyboardButton("밤 행동 수행", callback_data="night_action")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown"
            )
        return True
    except Exception as e:
        logging.error(f"역할 정보 메시지 전송 중 오류 발생: {e}")
        return False


def send_phase_change_message(context: CallbackContext, chat_id: int, 
                             old_phase: str, new_phase: str, day_count: int) -> bool:
    """
    단계 변경 메시지를 전송합니다.
    
    Args:
        context: 콜백 컨텍스트
        chat_id: 채팅방 ID
        old_phase: 이전 단계
        new_phase: 새 단계
        day_count: 날짜
        
    Returns:
        전송 성공 여부
    """
    try:
        if new_phase == "day":
            text = f"☀️ {day_count}일차 낮이 되었습니다.\n\n"
            text += "마을 회의를 통해 마피아로 의심되는 사람을 투표로 처형하세요."
            
            keyboard = [[InlineKeyboardButton("투표하기", callback_data="vote")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup
            )
        elif new_phase == "night":
            text = f"🌙 {day_count}일차 밤이 되었습니다.\n\n"
            text += "각자의 역할에 맞는 행동을 수행하세요."
            
            context.bot.send_message(
                chat_id=chat_id,
                text=text
            )
        elif new_phase == "end":
            text = "🏁 게임이 종료되었습니다.\n\n"
            text += "새 게임을 시작하려면 /open 명령어를 사용하세요."
            
            context.bot.send_message(
                chat_id=chat_id,
                text=text
            )
        return True
    except Exception as e:
        logging.error(f"단계 변경 메시지 전송 중 오류 발생: {e}")
        return False


def send_death_message(context: CallbackContext, chat_id: int, 
                      player_name: str, role_name: str, last_will: Optional[str] = None) -> bool:
    """
    사망 메시지를 전송합니다.
    
    Args:
        context: 콜백 컨텍스트
        chat_id: 채팅방 ID
        player_name: 플레이어 이름
        role_name: 역할 이름
        last_will: 유언
        
    Returns:
        전송 성공 여부
    """
    try:
        text = f"💀 *{player_name}*님이 사망했습니다.\n"
        text += f"역할: *{role_name}*\n\n"
        
        if last_will:
            text += f"📜 *유언*\n{last_will}"
        
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown"
        )
        return True
    except Exception as e:
        logging.error(f"사망 메시지 전송 중 오류 발생: {e}")
        return False


def send_vote_result(context: CallbackContext, chat_id: int, 
                    vote_results: Dict[int, int], player_names: Dict[int, str]) -> bool:
    """
    투표 결과 메시지를 전송합니다.
    
    Args:
        context: 콜백 컨텍스트
        chat_id: 채팅방 ID
        vote_results: 투표 결과 (대상 ID: 투표 수)
        player_names: 플레이어 이름 (플레이어 ID: 이름)
        
    Returns:
        전송 성공 여부
    """
    try:
        text = "📊 *투표 결과*\n\n"
        
        if not vote_results:
            text += "아무도 투표하지 않았습니다."
        else:
            # 투표 수 내림차순으로 정렬
            sorted_results = sorted(vote_results.items(), key=lambda x: x[1], reverse=True)
            
            for player_id, votes in sorted_results:
                player_name = player_names.get(player_id, "알 수 없음")
                text += f"{player_name}: {votes}표\n"
            
            # 최다 득표자 확인
            max_votes = sorted_results[0][1]
            max_voted_players = [player_id for player_id, votes in sorted_results if votes == max_votes]
            
            text += "\n"
            
            if len(max_voted_players) > 1:
                text += "동률로 인해 아무도 처형되지 않았습니다."
            elif max_votes == 0:
                text += "아무도 처형되지 않았습니다."
            else:
                executed_id = max_voted_players[0]
                executed_name = player_names.get(executed_id, "알 수 없음")
                text += f"*{executed_name}*님이 처형되었습니다."
        
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown"
        )
        return True
    except Exception as e:
        logging.error(f"투표 결과 메시지 전송 중 오류 발생: {e}")
        return False


def send_game_end_message(context: CallbackContext, chat_id: int, 
                         winning_team: Optional[str] = None, 
                         winning_player_id: Optional[int] = None,
                         player_list: Optional[str] = None) -> bool:
    """
    게임 종료 메시지를 전송합니다.
    
    Args:
        context: 콜백 컨텍스트
        chat_id: 채팅방 ID
        winning_team: 승리한 팀
        winning_player_id: 승리한 중립 플레이어 ID
        player_list: 플레이어 목록 텍스트
        
    Returns:
        전송 성공 여부
    """
    try:
        text = "🏁 *게임이 종료되었습니다!*\n\n"
        
        if winning_team:
            text += f"*{winning_team}* 승리!\n\n"
        
        if player_list:
            text += "📋 *최종 플레이어 목록*\n"
            text += player_list
        
        text += "\n새 게임을 시작하려면 /open 명령어를 사용하세요."
        
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown"
        )
        return True
    except Exception as e:
        logging.error(f"게임 종료 메시지 전송 중 오류 발생: {e}")
        return False


def send_error_message(context: CallbackContext, chat_id: int, error_message: str) -> bool:
    """
    오류 메시지를 전송합니다.
    
    Args:
        context: 콜백 컨텍스트
        chat_id: 채팅방 ID
        error_message: 오류 메시지
        
    Returns:
        전송 성공 여부
    """
    try:
        text = f"⚠️ *오류*\n\n{error_message}"
        
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown"
        )
        return True
    except Exception as e:
        logging.error(f"오류 메시지 전송 중 오류 발생: {e}")
        return False
