"""
기본 역할 클래스 모듈

이 모듈은 모든 역할의 기본이 되는 BaseRole 클래스를 정의합니다.
모든 역할 클래스는 이 BaseRole 클래스를 상속받아 구현됩니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple, Any


class BaseRole(ABC):
    """
    모든 역할의 기본 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (마피아팀, 시민팀, 중립팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
        player_id (Optional[int]): 이 역할을 가진 플레이어 ID
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        BaseRole 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        self.name: str = self.__class__.__name__
        self.description: str = "기본 역할 설명"
        self.team: str = "시민팀"  # 기본값은 시민팀
        self.night_action: bool = False
        self.priority: int = 100  # 기본 우선순위
        self.player_id: Optional[int] = player_id
        self.is_psycho: bool = False  # 정신병자 여부
    
    def get_role_info(self) -> Dict[str, Any]:
        """
        역할 정보를 반환합니다.
        
        Returns:
            역할 정보를 담은 딕셔너리
        """
        return {
            "name": self.name,
            "description": self.description,
            "team": self.team,
            "night_action": self.night_action,
            "priority": self.priority,
            "player_id": self.player_id,
            "is_psycho": self.is_psycho
        }
    
    def set_player(self, player_id: int) -> None:
        """
        이 역할을 가진 플레이어를 설정합니다.
        
        Args:
            player_id: 플레이어 ID
        """
        self.player_id = player_id
    
    def set_psycho(self, is_psycho: bool = True) -> None:
        """
        정신병자 여부를 설정합니다.
        
        Args:
            is_psycho: 정신병자 여부
        """
        self.is_psycho = is_psycho
    
    @abstractmethod
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            밤 행동 대상이 될 수 있는 플레이어 ID 목록
        """
        pass
    
    @abstractmethod
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                            night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        pass
    
    def get_night_action_result(self, players: Dict[int, Dict[str, Any]], 
                               night_actions: Dict[str, Any]) -> str:
        """
        밤 행동 결과 메시지를 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            밤 행동 결과 메시지
        """
        return "아무 일도 일어나지 않았습니다."
    
    def on_day_start(self, players: Dict[int, Dict[str, Any]], 
                    night_actions: Dict[str, Any]) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
        """
        낮이 시작될 때 호출되는 메서드입니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 players와 공지 메시지 목록
        """
        return players, []
    
    def on_voted(self, voter_id: int, players: Dict[int, Dict[str, Any]]) -> int:
        """
        투표를 받았을 때 호출되는 메서드입니다.
        
        Args:
            voter_id: 투표한 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            실제 적용될 투표 수 (기본값: 1)
        """
        return 1
    
    def on_death(self, players: Dict[int, Dict[str, Any]], 
                killer_id: Optional[int] = None) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
        """
        사망했을 때 호출되는 메서드입니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            killer_id: 죽인 플레이어 ID (없을 수도 있음)
            
        Returns:
            업데이트된 players와 공지 메시지 목록
        """
        return players, []
    
    def check_win_condition(self, players: Dict[int, Dict[str, Any]]) -> bool:
        """
        승리 조건을 확인합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            승리 여부
        """
        return False