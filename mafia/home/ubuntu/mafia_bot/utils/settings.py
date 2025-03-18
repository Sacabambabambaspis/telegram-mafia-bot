"""
설정 관리 모듈

이 모듈은 마피아 게임의 설정을 관리하는 기능을 제공합니다.
"""

import json
import os
from typing import Dict, Any, Optional


class SettingsManager:
    """
    설정 관리자 클래스
    
    Attributes:
        settings_file (str): 설정 파일 경로
        default_settings (Dict[str, Any]): 기본 설정
        settings (Dict[str, Any]): 현재 설정
    """
    
    def __init__(self, settings_file: str = "settings.json"):
        """
        SettingsManager 클래스 초기화
        
        Args:
            settings_file: 설정 파일 경로
        """
        self.settings_file = settings_file
        
        # 기본 설정
        self.default_settings = {
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
        
        # 설정 로드
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """
        설정 파일에서 설정을 로드합니다.
        
        Returns:
            설정 딕셔너리
        """
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                
                # 기본 설정과 병합
                merged_settings = self.default_settings.copy()
                self._deep_update(merged_settings, settings)
                
                return merged_settings
            except Exception as e:
                print(f"설정 로드 중 오류 발생: {e}")
        
        return self.default_settings.copy()
    
    def save_settings(self, settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        설정을 파일에 저장합니다.
        
        Args:
            settings: 저장할 설정 (None인 경우 현재 설정 사용)
            
        Returns:
            저장 성공 여부
        """
        if settings is None:
            settings = self.settings
        
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            return True
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {e}")
            return False
    
    def get_settings(self) -> Dict[str, Any]:
        """
        현재 설정을 반환합니다.
        
        Returns:
            현재 설정
        """
        return self.settings
    
    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """
        설정을 업데이트합니다.
        
        Args:
            new_settings: 새 설정
            
        Returns:
            업데이트 성공 여부
        """
        self._deep_update(self.settings, new_settings)
        return self.save_settings()
    
    def reset_settings(self) -> bool:
        """
        설정을 기본값으로 초기화합니다.
        
        Returns:
            초기화 성공 여부
        """
        self.settings = self.default_settings.copy()
        return self.save_settings()
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        딕셔너리를 깊은 수준까지 업데이트합니다.
        
        Args:
            target: 대상 딕셔너리
            source: 소스 딕셔너리
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def get_chat_settings(self, chat_id: int) -> Dict[str, Any]:
        """
        특정 채팅방의 설정을 반환합니다.
        
        Args:
            chat_id: 채팅방 ID
            
        Returns:
            채팅방 설정
        """
        chat_settings = self.settings.get("chat_settings", {}).get(str(chat_id))
        
        if chat_settings:
            # 기본 설정과 병합
            merged_settings = self.default_settings.copy()
            self._deep_update(merged_settings, chat_settings)
            
            return merged_settings
        
        return self.default_settings.copy()
    
    def update_chat_settings(self, chat_id: int, new_settings: Dict[str, Any]) -> bool:
        """
        특정 채팅방의 설정을 업데이트합니다.
        
        Args:
            chat_id: 채팅방 ID
            new_settings: 새 설정
            
        Returns:
            업데이트 성공 여부
        """
        if "chat_settings" not in self.settings:
            self.settings["chat_settings"] = {}
        
        if str(chat_id) not in self.settings["chat_settings"]:
            self.settings["chat_settings"][str(chat_id)] = {}
        
        self._deep_update(self.settings["chat_settings"][str(chat_id)], new_settings)
        return self.save_settings()
    
    def reset_chat_settings(self, chat_id: int) -> bool:
        """
        특정 채팅방의 설정을 기본값으로 초기화합니다.
        
        Args:
            chat_id: 채팅방 ID
            
        Returns:
            초기화 성공 여부
        """
        if "chat_settings" in self.settings and str(chat_id) in self.settings["chat_settings"]:
            del self.settings["chat_settings"][str(chat_id)]
            return self.save_settings()
        
        return True
