"""
게임 단계 관리자 모듈 업데이트

이 모듈은 마피아 게임의 단계(낮/밤) 관리를 담당하는 PhaseManager 클래스를 정의합니다.
추가 역할들과 마피아 서브 직업 시스템을 지원하도록 업데이트되었습니다.
"""

import threading
import time
from typing import Dict, List, Optional, Callable, Any, Tuple


class PhaseManager:
    """
    게임 단계 관리자 클래스
    
    Attributes:
        current_phase (str): 현재 게임 단계
        phase_duration (Dict[str, int]): 각 단계별 지속 시간 (초)
        on_phase_change (Optional[Callable]): 단계 변경 시 호출될 콜백 함수
        on_phase_end (Optional[Callable]): 단계 종료 시 호출될 콜백 함수
        night_actions (Dict[str, Any]): 밤에 수행된 행동 정보
        phase_timer (Optional[threading.Timer]): 단계 타이머
    """
    
    def __init__(self, settings: Dict[str, Any]):
        """
        PhaseManager 클래스 초기화
        
        Args:
            settings: 게임 설정
        """
        self.current_phase = "open"  # 초기 단계: open
        
        # 각 단계별 지속 시간 (초)
        self.phase_duration = {
            "open": 60,  # 게임 시작 대기 시간
            "night": settings.get("night_duration", 60),  # 밤 지속 시간
            "day": settings.get("day_duration", 120),  # 낮 지속 시간
            "vote": settings.get("vote_duration", 30),  # 투표 지속 시간
            "end": 0  # 게임 종료 (지속 시간 없음)
        }
        
        # 콜백 함수
        self.on_phase_change: Optional[Callable] = None
        self.on_phase_end: Optional[Callable] = None
        
        # 밤 행동 정보
        self.night_actions: Dict[str, Any] = {}
        
        # 단계 타이머
        self.phase_timer: Optional[threading.Timer] = None
        
        # 저주 상태 플레이어 목록
        self.cursed_players: List[int] = []
    
    def set_callbacks(self, on_phase_change: Optional[Callable] = None, 
                     on_phase_end: Optional[Callable] = None) -> None:
        """
        콜백 함수를 설정합니다.
        
        Args:
            on_phase_change: 단계 변경 시 호출될 콜백 함수
            on_phase_end: 단계 종료 시 호출될 콜백 함수
        """
        self.on_phase_change = on_phase_change
        self.on_phase_end = on_phase_end
    
    def start_game(self) -> None:
        """
        게임을 시작합니다.
        """
        self._change_phase("night")
    
    def _change_phase(self, new_phase: str) -> None:
        """
        게임 단계를 변경합니다.
        
        Args:
            new_phase: 새 단계 이름
        """
        old_phase = self.current_phase
        self.current_phase = new_phase
        
        # 단계 변경 콜백 호출
        if self.on_phase_change:
            self.on_phase_change(old_phase, new_phase)
        
        # 새 단계 타이머 설정
        self._set_phase_timer()
    
    def _set_phase_timer(self) -> None:
        """
        현재 단계에 대한 타이머를 설정합니다.
        """
        # 이전 타이머 취소
        self._cancel_timers()
        
        # 현재 단계의 지속 시간
        duration = self.phase_duration.get(self.current_phase, 0)
        
        # 지속 시간이 있는 경우에만 타이머 설정
        if duration > 0:
            self.phase_timer = threading.Timer(duration, self._on_phase_timer_end)
            self.phase_timer.daemon = True
            self.phase_timer.start()
    
    def _cancel_timers(self) -> None:
        """
        모든 타이머를 취소합니다.
        """
        if self.phase_timer:
            self.phase_timer.cancel()
            self.phase_timer = None
    
    def _on_phase_timer_end(self) -> None:
        """
        단계 타이머가 종료되었을 때 호출되는 메서드입니다.
        """
        # 단계 종료 콜백 호출
        if self.on_phase_end:
            self.on_phase_end(self.current_phase)
        
        # 다음 단계로 전환
        if self.current_phase == "night":
            self._change_phase("day")
        elif self.current_phase == "day":
            self._change_phase("vote")
        elif self.current_phase == "vote":
            self._change_phase("night")
    
    def force_next_phase(self) -> None:
        """
        강제로 다음 단계로 전환합니다.
        """
        self._on_phase_timer_end()
    
    def record_night_action(self, action_type: str, action_data: Dict[str, Any]) -> None:
        """
        밤 행동을 기록합니다.
        
        Args:
            action_type: 행동 유형
            action_data: 행동 데이터
        """
        self.night_actions[action_type] = action_data
    
    def get_night_actions(self) -> Dict[str, Any]:
        """
        밤 행동 정보를 반환합니다.
        
        Returns:
            밤 행동 정보
        """
        return self.night_actions
    
    def clear_night_actions(self) -> None:
        """
        밤 행동 정보를 초기화합니다.
        """
        self.night_actions.clear()
        
        # 저주 상태 플레이어 목록 초기화 (하루에 한 번)
        self.cursed_players.clear()
    
    def end_game(self) -> None:
        """
        게임을 종료합니다.
        """
        self._cancel_timers()
        old_phase = self.current_phase
        self.current_phase = "end"
        
        # 단계 변경 콜백 호출 (무한 재귀 방지를 위해 end 상태에서는 콜백 호출 안함)
        if self.on_phase_change and old_phase != "end":
            self.on_phase_change(old_phase, "end")
    
    def get_phase_info(self) -> Dict[str, Any]:
        """
        현재 단계 정보를 반환합니다.
        
        Returns:
            현재 단계 정보
        """
        remaining_time = 0
        
        if self.phase_timer:
            # 타이머의 남은 시간 계산
            for thread in threading.enumerate():
                if thread is self.phase_timer:
                    remaining_time = max(0, self.phase_duration.get(self.current_phase, 0) - 
                                       (time.time() - thread._start))
                    break
        
        return {
            "phase": self.current_phase,
            "duration": self.phase_duration.get(self.current_phase, 0),
            "remaining": int(remaining_time)
        }
    
    def add_cursed_player(self, player_id: int) -> None:
        """
        저주 상태 플레이어를 추가합니다.
        
        Args:
            player_id: 플레이어 ID
        """
        if player_id not in self.cursed_players:
            self.cursed_players.append(player_id)
    
    def is_player_cursed(self, player_id: int) -> bool:
        """
        플레이어가 저주 상태인지 확인합니다.
        
        Args:
            player_id: 플레이어 ID
            
        Returns:
            저주 상태 여부
        """
        return player_id in self.cursed_players
    
    def process_night_actions(self, players: Dict[int, Dict[str, Any]]) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
        """
        밤 행동을 처리합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            업데이트된 플레이어 정보와 메시지 목록
        """
        messages = []
        
        # 마녀 저주 처리
        if "witch_curse" in self.night_actions:
            curse = self.night_actions["witch_curse"]
            target_id = curse.get("target_id")
            
            if target_id and target_id in players:
                self.add_cursed_player(target_id)
                target_name = players[target_id].get("name", "알 수 없음")
                messages.append(f"{target_name}이(가) 마녀의 저주에 걸렸습니다. 하루 동안 행동불능 상태가 됩니다.")
        
        # 버스기사 행동 처리
        if "bus_driver_swap" in self.night_actions:
            swap = self.night_actions["bus_driver_swap"]
            if swap.get("target2_id") is not None:
                target1_id = swap.get("target1_id")
                target2_id = swap.get("target2_id")
                
                if target1_id in players and target2_id in players:
                    target1_name = players[target1_id].get("name", "알 수 없음")
                    target2_name = players[target2_id].get("name", "알 수 없음")
                    messages.append(f"버스기사가 {target1_name}와(과) {target2_name}의 결과를 바꿨습니다.")
        
        # 마피아 살해 처리
        if "mafia_kill" in self.night_actions:
            kill = self.night_actions["mafia_kill"]
            killer_id = kill.get("killer_id")
            target_id = kill.get("target_id")
            
            if killer_id and target_id and target_id in players:
                target = players[target_id]
                
                # 의사 보호 확인
                protected = False
                if "doctor_heal" in self.night_actions:
                    heal = self.night_actions["doctor_heal"]
                    if heal.get("target_id") == target_id:
                        protected = True
                        healer_id = heal.get("doctor_id")
                        if healer_id in players:
                            healer_name = players[healer_id].get("name", "알 수 없음")
                            messages.append(f"{healer_name}이(가) {target.get('name', '알 수 없음')}을(를) 치료했습니다.")
                
                if not protected:
                    # 플레이어 사망 처리
                    if target.get("alive", True):
                        target["alive"] = False
                        messages.append(f"{target.get('name', '알 수 없음')}이(가) 마피아에게 살해당했습니다.")
                        
                        # 폭탄 효과 확인
                        role = target.get("role")
                        if role and role.name == "폭탄":
                            if killer_id in players:
                                killer = players[killer_id]
                                killer["alive"] = False
                                messages.append(f"폭탄이 폭발했습니다! {killer.get('name', '알 수 없음')}이(가) 함께 사망했습니다.")
                else:
                    messages.append(f"{target.get('name', '알 수 없음')}이(가) 공격을 받았지만 의사의 치료로 살아남았습니다.")
        
        # 연쇄 살인마 살해 처리
        if "serial_killer_kill" in self.night_actions:
            kill = self.night_actions["serial_killer_kill"]
            killer_id = kill.get("killer_id")
            target_id = kill.get("target_id")
            
            if killer_id and target_id and target_id in players:
                target = players[target_id]
                
                # 의사 보호 확인
                protected = False
                if "doctor_heal" in self.night_actions:
                    heal = self.night_actions["doctor_heal"]
                    if heal.get("target_id") == target_id:
                        protected = True
                
                if not protected:
                    # 플레이어 사망 처리
                    if target.get("alive", True):
                        target["alive"] = False
                        messages.append(f"{target.get('name', '알 수 없음')}이(가) 연쇄 살인마에게 살해당했습니다.")
                        
                        # 폭탄 효과 확인
                        role = target.get("role")
                        if role and role.name == "폭탄":
                            if killer_id in players:
                                killer = players[killer_id]
                                killer["alive"] = False
                                messages.append(f"폭탄이 폭발했습니다! {killer.get('name', '알 수 없음')}이(가) 함께 사망했습니다.")
                else:
                    messages.append(f"{target.get('name', '알 수 없음')}이(가) 공격을 받았지만 의사의 치료로 살아남았습니다.")
        
        # 설계자 예측 처리
        if "architect_result" in self.night_actions:
            result = self.night_actions["architect_result"]
            architect_id = result.get("architect_id")
            target_id = result.get("target_id")
            success = result.get("success", False)
            
            if architect_id in players:
                architect = players[architect_id]
                
                if success and target_id in players:
                    target = players[target_id]
                    target["alive"] = False
                    messages.append(f"설계자의 예측이 성공했습니다! {target.get('name', '알 수 없음')}이(가) 게임에서 제거되었습니다.")
                else:
                    architect["alive"] = False
                    messages.append(f"설계자의 예측이 실패했습니다! {architect.get('name', '알 수 없음')}이(가) 게임에서 제거되었습니다.")
        
        return players, messages
