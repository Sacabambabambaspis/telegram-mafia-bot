"""
게임 단계 관리자 모듈

이 모듈은 마피아 게임의 단계(낮/밤)를 관리하는 PhaseManager 클래스를 정의합니다.
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext


class PhaseManager:
    """
    게임 단계 관리자 클래스
    
    Attributes:
        settings (Dict[str, Any]): 게임 설정
        current_phase (str): 현재 게임 단계 ("open", "day", "night", "end")
        day_count (int): 현재 날짜 (1일차부터 시작)
        phase_timers (Dict[str, threading.Timer]): 단계별 타이머
        night_actions (Dict[str, Any]): 밤 행동 정보
        on_phase_change (Optional[Callable]): 단계 변경 시 호출할 콜백 함수
    """
    
    def __init__(self, settings: Dict[str, Any]):
        """
        PhaseManager 클래스 초기화
        
        Args:
            settings: 게임 설정
        """
        self.settings = settings
        self.current_phase = "open"  # "open", "day", "night", "end"
        self.day_count = 0
        self.phase_timers: Dict[str, threading.Timer] = {}
        self.night_actions: Dict[str, Any] = {}
        self.on_phase_change: Optional[Callable] = None
    
    def set_phase_change_callback(self, callback: Callable) -> None:
        """
        단계 변경 시 호출할 콜백 함수를 설정합니다.
        
        Args:
            callback: 단계 변경 시 호출할 콜백 함수
        """
        self.on_phase_change = callback
    
    def start_game(self) -> None:
        """
        게임을 시작합니다. 첫 번째 밤으로 진행합니다.
        """
        self.day_count = 1
        self.change_phase("night")
    
    def change_phase(self, new_phase: str) -> None:
        """
        게임 단계를 변경합니다.
        
        Args:
            new_phase: 새 게임 단계 ("day", "night", "end")
        """
        old_phase = self.current_phase
        self.current_phase = new_phase
        
        # 이전 타이머 취소
        self._cancel_timers()
        
        # 단계 변경 콜백 호출
        if self.on_phase_change:
            self.on_phase_change(old_phase, new_phase)
        
        # 새 단계에 따른 타이머 설정
        if new_phase == "day":
            self._set_day_timer()
        elif new_phase == "night":
            self._set_night_timer()
    
    def _set_day_timer(self) -> None:
        """
        낮 단계 타이머를 설정합니다.
        """
        day_duration = self.settings.get("day_duration", 60)  # 기본값 60초
        
        if day_duration > 0:
            timer = threading.Timer(day_duration, self._day_timeout)
            timer.daemon = True
            timer.start()
            self.phase_timers["day"] = timer
    
    def _set_night_timer(self) -> None:
        """
        밤 단계 타이머를 설정합니다.
        """
        night_duration = self.settings.get("night_duration", 30)  # 기본값 30초
        
        if night_duration > 0:
            timer = threading.Timer(night_duration, self._night_timeout)
            timer.daemon = True
            timer.start()
            self.phase_timers["night"] = timer
    
    def _day_timeout(self) -> None:
        """
        낮 타이머가 종료되었을 때 호출됩니다.
        """
        # 밤으로 변경
        self.change_phase("night")
    
    def _night_timeout(self) -> None:
        """
        밤 타이머가 종료되었을 때 호출됩니다.
        """
        # 다음 날로 변경
        self.day_count += 1
        self.change_phase("day")
    
    def _cancel_timers(self) -> None:
        """
        모든 타이머를 취소합니다.
        """
        for phase, timer in self.phase_timers.items():
            if timer and timer.is_alive():
                timer.cancel()
        
        self.phase_timers.clear()
    
    def get_remaining_time(self) -> int:
        """
        현재 단계의 남은 시간(초)을 반환합니다.
        
        Returns:
            남은 시간(초)
        """
        if self.current_phase == "day" and "day" in self.phase_timers:
            timer = self.phase_timers["day"]
            if hasattr(timer, "_target_time"):
                return max(0, int(timer._target_time - time.time()))
        elif self.current_phase == "night" and "night" in self.phase_timers:
            timer = self.phase_timers["night"]
            if hasattr(timer, "_target_time"):
                return max(0, int(timer._target_time - time.time()))
        
        return 0
    
    def get_phase_keyboard(self) -> InlineKeyboardMarkup:
        """
        현재 단계에 맞는 인라인 키보드를 반환합니다.
        
        Returns:
            인라인 키보드 마크업
        """
        keyboard = []
        
        if self.current_phase == "day":
            keyboard = [
                [InlineKeyboardButton("투표하기", callback_data="vote")],
                [InlineKeyboardButton("유언 작성", callback_data="lastwill")]
            ]
        elif self.current_phase == "night":
            keyboard = [
                [InlineKeyboardButton("밤 행동", callback_data="night_action")],
                [InlineKeyboardButton("유언 작성", callback_data="lastwill")]
            ]
        
        return InlineKeyboardMarkup(keyboard)
    
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
        기록된 밤 행동 정보를 반환합니다.
        
        Returns:
            밤 행동 정보
        """
        return self.night_actions
    
    def clear_night_actions(self) -> None:
        """
        밤 행동 정보를 초기화합니다.
        """
        self.night_actions.clear()
    
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
            단계 정보를 담은 딕셔너리
        """
        return {
            "phase": self.current_phase,
            "day_count": self.day_count,
            "remaining_time": self.get_remaining_time()
        }
