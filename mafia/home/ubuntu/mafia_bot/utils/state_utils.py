"""
게임 상태 관리 모듈

이 모듈은 마피아 게임의 상태를 관리하는 기능을 제공합니다.
"""

import json
import os
import pickle
from typing import Dict, Any, Optional, List


class StateManager:
    """
    상태 관리자 클래스
    
    Attributes:
        state_file (str): 상태 파일 경로
        state (Dict[str, Any]): 현재 상태
    """
    
    def __init__(self, state_file: str = "game_state.json"):
        """
        StateManager 클래스 초기화
        
        Args:
            state_file: 상태 파일 경로
        """
        self.state_file = state_file
        self.state = self.load_state()
    
    def load_state(self) -> Dict[str, Any]:
        """
        상태 파일에서 상태를 로드합니다.
        
        Returns:
            상태 딕셔너리
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                return state
            except Exception as e:
                print(f"상태 로드 중 오류 발생: {e}")
        
        return {"games": {}}
    
    def save_state(self) -> bool:
        """
        상태를 파일에 저장합니다.
        
        Returns:
            저장 성공 여부
        """
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"상태 저장 중 오류 발생: {e}")
            return False
    
    def get_game_state(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """
        특정 채팅방의 게임 상태를 반환합니다.
        
        Args:
            chat_id: 채팅방 ID
            
        Returns:
            게임 상태
        """
        return self.state.get("games", {}).get(str(chat_id))
    
    def set_game_state(self, chat_id: int, game_state: Dict[str, Any]) -> bool:
        """
        특정 채팅방의 게임 상태를 설정합니다.
        
        Args:
            chat_id: 채팅방 ID
            game_state: 게임 상태
            
        Returns:
            설정 성공 여부
        """
        if "games" not in self.state:
            self.state["games"] = {}
        
        self.state["games"][str(chat_id)] = game_state
        return self.save_state()
    
    def remove_game_state(self, chat_id: int) -> bool:
        """
        특정 채팅방의 게임 상태를 제거합니다.
        
        Args:
            chat_id: 채팅방 ID
            
        Returns:
            제거 성공 여부
        """
        if "games" in self.state and str(chat_id) in self.state["games"]:
            del self.state["games"][str(chat_id)]
            return self.save_state()
        
        return True
    
    def get_active_games(self) -> List[int]:
        """
        활성화된 게임 채팅방 ID 목록을 반환합니다.
        
        Returns:
            활성화된 게임 채팅방 ID 목록
        """
        active_games = []
        
        for chat_id_str, game_state in self.state.get("games", {}).items():
            if game_state.get("active", False):
                try:
                    active_games.append(int(chat_id_str))
                except ValueError:
                    pass
        
        return active_games
    
    def save_game_manager(self, chat_id: int, game_manager: Any) -> bool:
        """
        게임 관리자 객체를 저장합니다.
        
        Args:
            chat_id: 채팅방 ID
            game_manager: 게임 관리자 객체
            
        Returns:
            저장 성공 여부
        """
        try:
            # 게임 관리자 객체를 바이너리 파일로 저장
            file_path = f"game_manager_{chat_id}.pkl"
            with open(file_path, "wb") as f:
                pickle.dump(game_manager, f)
            
            # 게임 상태 업데이트
            game_state = {
                "active": game_manager.game_started,
                "manager_file": file_path,
                "player_count": len(game_manager.players),
                "phase": game_manager.phase_manager.current_phase,
                "day_count": game_manager.phase_manager.day_count
            }
            
            return self.set_game_state(chat_id, game_state)
        except Exception as e:
            print(f"게임 관리자 저장 중 오류 발생: {e}")
            return False
    
    def load_game_manager(self, chat_id: int) -> Optional[Any]:
        """
        게임 관리자 객체를 로드합니다.
        
        Args:
            chat_id: 채팅방 ID
            
        Returns:
            게임 관리자 객체
        """
        game_state = self.get_game_state(chat_id)
        
        if not game_state or "manager_file" not in game_state:
            return None
        
        try:
            file_path = game_state["manager_file"]
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, "rb") as f:
                game_manager = pickle.load(f)
            
            return game_manager
        except Exception as e:
            print(f"게임 관리자 로드 중 오류 발생: {e}")
            return None
