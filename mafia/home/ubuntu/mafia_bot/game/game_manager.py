"""
게임 관리자 모듈

이 모듈은 마피아 게임의 전체 게임 흐름을 관리하는 GameManager 클래스를 정의합니다.
"""

import random
import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Callable

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from mafia_bot.game.player import Player
from mafia_bot.game.role_manager import RoleManager
from mafia_bot.game.phase_manager import PhaseManager


class GameManager:
    """
    게임 관리자 클래스
    
    Attributes:
        settings (Dict[str, Any]): 게임 설정
        players (Dict[int, Player]): 플레이어 정보
        role_manager (RoleManager): 역할 관리자
        phase_manager (PhaseManager): 단계 관리자
        game_started (bool): 게임 시작 여부
        game_chat_id (int): 게임 채팅방 ID
        mafia_chat_id (Optional[int]): 마피아 채팅방 ID
        lovers_chat_id (Optional[int]): 연인 채팅방 ID
        vote_results (Dict[int, int]): 투표 결과 (대상 ID: 투표 수)
        on_game_end (Optional[Callable]): 게임 종료 시 호출할 콜백 함수
    """
    
    def __init__(self, settings: Dict[str, Any], game_chat_id: int):
        """
        GameManager 클래스 초기화
        
        Args:
            settings: 게임 설정
            game_chat_id: 게임 채팅방 ID
        """
        self.settings = settings
        self.players: Dict[int, Player] = {}
        self.role_manager = RoleManager(settings)
        self.phase_manager = PhaseManager(settings)
        self.game_started = False
        self.game_chat_id = game_chat_id
        self.mafia_chat_id: Optional[int] = None
        self.lovers_chat_id: Optional[int] = None
        self.vote_results: Dict[int, int] = {}
        self.on_game_end: Optional[Callable] = None
        
        # 단계 변경 콜백 설정
        self.phase_manager.set_phase_change_callback(self._on_phase_change)
    
    def set_game_end_callback(self, callback: Callable) -> None:
        """
        게임 종료 시 호출할 콜백 함수를 설정합니다.
        
        Args:
            callback: 게임 종료 시 호출할 콜백 함수
        """
        self.on_game_end = callback
    
    def add_player(self, user_id: int, name: str, chat_id: int) -> bool:
        """
        게임에 플레이어를 추가합니다.
        
        Args:
            user_id: 텔레그램 사용자 ID
            name: 플레이어 이름
            chat_id: 플레이어의 개인 채팅 ID
            
        Returns:
            추가 성공 여부
        """
        if self.game_started:
            return False
        
        if user_id not in self.players:
            self.players[user_id] = Player(user_id, name, chat_id)
            return True
        
        return False
    
    def remove_player(self, user_id: int) -> bool:
        """
        게임에서 플레이어를 제거합니다.
        
        Args:
            user_id: 텔레그램 사용자 ID
            
        Returns:
            제거 성공 여부
        """
        if self.game_started:
            return False
        
        if user_id in self.players:
            del self.players[user_id]
            return True
        
        return False
    
    def start_game(self) -> Tuple[bool, str]:
        """
        게임을 시작합니다.
        
        Returns:
            (성공 여부, 메시지)
        """
        if self.game_started:
            return False, "게임이 이미 시작되었습니다."
        
        if len(self.players) < 4:
            return False, "게임을 시작하려면 최소 4명의 플레이어가 필요합니다."
        
        # 역할 할당
        roles = self.role_manager.assign_roles(list(self.players.keys()))
        
        for player_id, role in roles.items():
            if player_id in self.players:
                self.players[player_id].assign_role(role)
        
        # 게임 시작
        self.game_started = True
        self.phase_manager.start_game()
        
        return True, "게임이 시작되었습니다!"
    
    def stop_game(self) -> None:
        """
        게임을 중지합니다.
        """
        if not self.game_started:
            return
        
        self.game_started = False
        self.phase_manager.end_game()
        self._reset_game()
    
    def _reset_game(self) -> None:
        """
        게임 상태를 초기화합니다.
        """
        self.players.clear()
        self.vote_results.clear()
        self.mafia_chat_id = None
        self.lovers_chat_id = None
    
    def _on_phase_change(self, old_phase: str, new_phase: str) -> None:
        """
        단계 변경 시 호출되는 콜백 함수입니다.
        
        Args:
            old_phase: 이전 단계
            new_phase: 새 단계
        """
        if new_phase == "day":
            self._process_night_actions()
            self._start_day()
        elif new_phase == "night":
            self._process_day_votes()
            self._start_night()
        elif new_phase == "end":
            self._end_game()
    
    def _process_night_actions(self) -> None:
        """
        밤 행동을 처리합니다.
        """
        night_actions = self.phase_manager.get_night_actions()
        
        # 플레이어 상태 초기화
        for player in self.players.values():
            player.reset_status()
        
        # 의사 치료 처리
        if "doctor_heal" in night_actions:
            target_id = night_actions["doctor_heal"]["target_id"]
            if target_id in self.players:
                self.players[target_id].protect()
        
        # 마피아 공격 처리
        if "mafia_kill" in night_actions:
            kill_data = night_actions["mafia_kill"]
            target_id = kill_data["target_id"]
            killer_id = kill_data["killer_id"]
            blocked = kill_data.get("blocked", False)
            
            if not blocked and target_id in self.players:
                target = self.players[target_id]
                if not target.protected:
                    target.kill(killer_id, self.players)
        
        # 연쇄 살인마 공격 처리
        if "serial_killer_kill" in night_actions:
            kill_data = night_actions["serial_killer_kill"]
            target_id = kill_data["target_id"]
            killer_id = kill_data["killer_id"]
            
            if target_id in self.players:
                target = self.players[target_id]
                if not target.protected:
                    target.kill(killer_id, self.players)
        
        # 밤 행동 초기화
        self.phase_manager.clear_night_actions()
    
    def _start_day(self) -> None:
        """
        낮 단계를 시작합니다.
        """
        # 투표 초기화
        self.vote_results.clear()
        for player in self.players.values():
            player.reset_vote()
        
        # 승리 조건 확인
        self._check_win_condition()
    
    def _process_day_votes(self) -> None:
        """
        낮 투표 결과를 처리합니다.
        """
        if not self.vote_results:
            return
        
        # 최다 득표자 찾기
        max_votes = 0
        max_voted_players = []
        
        for player_id, votes in self.vote_results.items():
            if votes > max_votes:
                max_votes = votes
                max_voted_players = [player_id]
            elif votes == max_votes:
                max_voted_players.append(player_id)
        
        # 동률이 아니면 처형
        if len(max_voted_players) == 1 and max_votes > 0:
            executed_id = max_voted_players[0]
            if executed_id in self.players:
                self.players[executed_id].kill(None, self.players)
        
        # 투표 결과 초기화
        self.vote_results.clear()
    
    def _start_night(self) -> None:
        """
        밤 단계를 시작합니다.
        """
        # 승리 조건 확인
        self._check_win_condition()
    
    def vote(self, voter_id: int, target_id: int) -> bool:
        """
        투표를 진행합니다.
        
        Args:
            voter_id: 투표하는 플레이어 ID
            target_id: 투표 대상 플레이어 ID
            
        Returns:
            투표 성공 여부
        """
        if not self.game_started or self.phase_manager.current_phase != "day":
            return False
        
        if voter_id not in self.players or target_id not in self.players:
            return False
        
        voter = self.players[voter_id]
        target = self.players[target_id]
        
        if not voter.alive or not target.alive:
            return False
        
        # 이미 투표한 경우 이전 투표 취소
        if voter.voted_for is not None and voter.voted_for in self.vote_results:
            self.vote_results[voter.voted_for] -= 1
            if self.vote_results[voter.voted_for] <= 0:
                del self.vote_results[voter.voted_for]
        
        # 새 투표 등록
        voter.vote_for(target_id)
        vote_weight = target.add_vote(voter_id, self.players)
        
        if target_id not in self.vote_results:
            self.vote_results[target_id] = 0
        
        self.vote_results[target_id] += vote_weight
        
        return True
    
    def perform_night_action(self, player_id: int, target_id: int) -> bool:
        """
        밤 행동을 수행합니다.
        
        Args:
            player_id: 행동하는 플레이어 ID
            target_id: 대상 플레이어 ID
            
        Returns:
            행동 성공 여부
        """
        if not self.game_started or self.phase_manager.current_phase != "night":
            return False
        
        if player_id not in self.players or target_id not in self.players:
            return False
        
        player = self.players[player_id]
        
        if not player.alive or not player.role or not player.role.night_action:
            return False
        
        # 역할의 밤 행동 수행
        night_actions = self.phase_manager.get_night_actions()
        updated_actions = player.role.perform_night_action(target_id, player.to_dict(self.players), night_actions)
        
        # 업데이트된 밤 행동 저장
        for action_type, action_data in updated_actions.items():
            self.phase_manager.record_night_action(action_type, action_data)
        
        return True
    
    def get_night_action_result(self, player_id: int) -> str:
        """
        플레이어의 밤 행동 결과를 반환합니다.
        
        Args:
            player_id: 플레이어 ID
            
        Returns:
            밤 행동 결과 메시지
        """
        if player_id not in self.players or not self.players[player_id].role:
            return "행동 결과가 없습니다."
        
        night_actions = self.phase_manager.get_night_actions()
        return self.players[player_id].role.get_night_action_result(
            self.players[player_id].to_dict(self.players), night_actions)
    
    def get_night_action_targets(self, player_id: int) -> List[int]:
        """
        플레이어의 밤 행동 대상 목록을 반환합니다.
        
        Args:
            player_id: 플레이어 ID
            
        Returns:
            밤 행동 대상 플레이어 ID 목록
        """
        if player_id not in self.players or not self.players[player_id].role:
            return []
        
        return self.players[player_id].role.get_night_action_targets(
            self.players[player_id].to_dict(self.players))
    
    def set_mafia_chat(self, chat_id: int) -> None:
        """
        마피아 채팅방 ID를 설정합니다.
        
        Args:
            chat_id: 마피아 채팅방 ID
        """
        self.mafia_chat_id = chat_id
    
    def set_lovers_chat(self, chat_id: int) -> None:
        """
        연인 채팅방 ID를 설정합니다.
        
        Args:
            chat_id: 연인 채팅방 ID
        """
        self.lovers_chat_id = chat_id
    
    def get_alive_players(self) -> List[int]:
        """
        살아있는 플레이어 ID 목록을 반환합니다.
        
        Returns:
            살아있는 플레이어 ID 목록
        """
        return [player_id for player_id, player in self.players.items() if player.alive]
    
    def get_player_name(self, player_id: int) -> str:
        """
        플레이어 이름을 반환합니다.
        
        Args:
            player_id: 플레이어 ID
            
        Returns:
            플레이어 이름
        """
        if player_id in self.players:
            return self.players[player_id].name
        return "알 수 없음"
    
    def get_player_role_name(self, player_id: int) -> str:
        """
        플레이어 역할 이름을 반환합니다.
        
        Args:
            player_id: 플레이어 ID
            
        Returns:
            플레이어 역할 이름
        """
        if player_id in self.players and self.players[player_id].role:
            return self.players[player_id].role.name
        return "알 수 없음"
    
    def get_player_team(self, player_id: int) -> str:
        """
        플레이어 팀을 반환합니다.
        
        Args:
            player_id: 플레이어 ID
            
        Returns:
            플레이어 팀
        """
        if player_id in self.players and self.players[player_id].role:
            return self.players[player_id].role.team
        return "알 수 없음"
    
    def get_team_players(self, team: str) -> List[int]:
        """
        특정 팀에 속한 플레이어 ID 목록을 반환합니다.
        
        Args:
            team: 팀 이름 ("마피아팀", "시민팀", "중립팀")
            
        Returns:
            해당 팀에 속한 플레이어 ID 목록
        """
        team_players = []
        
        for player_id, player in self.players.items():
            if player.role and player.role.team == team:
                team_players.append(player_id)
        
        return team_players
    
    def get_alive_team_players(self, team: str) -> List[int]:
        """
        살아있는 특정 팀 플레이어 ID 목록을 반환합니다.
        
        Args:
            team: 팀 이름 ("마피아팀", "시민팀", "중립팀")
            
        Returns:
            살아있는 해당 팀 플레이어 ID 목록
        """
        team_players = []
        
        for player_id, player in self.players.items():
            if player.alive and player.role and player.role.team == team:
                team_players.append(player_id)
        
        return team_players
    
    def _check_win_condition(self) -> bool:
        """
        승리 조건을 확인합니다.
        
        Returns:
            게임 종료 여부
        """
        if not self.game_started:
            return False
        
        # 살아있는 플레이어가 없으면 게임 종료
        alive_players = self.get_alive_players()
        if not alive_players:
            self._end_game()
            return True
        
        # 마피아팀 승리 조건
        mafia_alive = len(self.get_alive_team_players("마피아팀"))
        citizen_alive = len(self.get_alive_team_players("시민팀"))
        
        if mafia_alive >= citizen_alive and mafia_alive > 0:
            self._end_game("마피아팀")
            return True
        
        # 시민팀 승리 조건
        if mafia_alive == 0 and citizen_alive > 0:
            self._end_game("시민팀")
            return True
        
        # 중립 역할 승리 조건 확인
        for player_id, player in self.players.items():
            if player.alive and player.role and player.role.team == "중립팀":
                if player.role.check_win_condition(player.to_dict(self.players)):
                    self._end_game("중립팀", player_id)
                    return True
        
        return False
    
    def _end_game(self, winning_team: Optional[str] = None, winning_player_id: Optional[int] = None) -> None:
        """
        게임을 종료합니다.
        
        Args:
            winning_team: 승리한 팀
            winning_player_id: 승리한 중립 플레이어 ID
        """
        self.game_started = False
        self.phase_manager.end_game()
        
        # 게임 종료 콜백 호출
        if self.on_game_end:
            self.on_game_end(winning_team, winning_player_id)
    
    def get_game_status(self) -> Dict[str, Any]:
        """
        현재 게임 상태 정보를 반환합니다.
        
        Returns:
            게임 상태 정보를 담은 딕셔너리
        """
        alive_players = self.get_alive_players()
        
        return {
            "game_started": self.game_started,
            "phase": self.phase_manager.current_phase,
            "day_count": self.phase_manager.day_count,
            "remaining_time": self.phase_manager.get_remaining_time(),
            "player_count": len(self.players),
            "alive_count": len(alive_players),
            "mafia_count": len(self.get_alive_team_players("마피아팀")),
            "citizen_count": len(self.get_alive_team_players("시민팀")),
            "neutral_count": len(self.get_alive_team_players("중립팀"))
        }
    
    def get_player_list_text(self, show_role: bool = False) -> str:
        """
        플레이어 목록 텍스트를 반환합니다.
        
        Args:
            show_role: 역할 표시 여부
            
        Returns:
            플레이어 목록 텍스트
        """
        if not self.players:
            return "참가자가 없습니다."
    <response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>