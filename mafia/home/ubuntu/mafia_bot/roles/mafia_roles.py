"""
마피아 역할 클래스 모듈

이 모듈은 마피아팀에 속하는 역할 클래스들을 정의합니다.
모든 마피아 역할은 BaseRole 클래스를 상속받습니다.
"""

from typing import Dict, List, Optional, Tuple, Any
from mafia_bot.roles.base_role import BaseRole


class Mafia(BaseRole):
    """
    기본 마피아 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (마피아팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Mafia 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "마피아"
        self.description = "😈 **마피아**\n어둠 속에서 작전을 수행합니다."
        self.team = "마피아팀"
        self.night_action = True
        self.priority = 50
    
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            밤 행동 대상이 될 수 있는 플레이어 ID 목록
        """
        # 살아있는 플레이어 중 마피아가 아닌 플레이어만 대상으로 함
        targets = []
        for player_id, player in players.items():
            if (player.get("alive", True) and 
                player.get("role") and 
                player.get("role").team != "마피아팀" and
                player_id != self.player_id):
                targets.append(player_id)
        return targets
    
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                            night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다. 마피아는 대상을 살해합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 마피아 공격 정보 저장
        if "mafia_kill" not in night_actions:
            night_actions["mafia_kill"] = {"target_id": target_id, "killer_id": self.player_id}
        
        return night_actions
    
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
        if "mafia_kill" in night_actions:
            target_id = night_actions["mafia_kill"]["target_id"]
            if target_id in players:
                target_name = players[target_id].get("name", "알 수 없음")
                return f"당신은 {target_name}을(를) 공격했습니다."
        
        return "공격에 실패했습니다."
    
    def check_win_condition(self, players: Dict[int, Dict[str, Any]]) -> bool:
        """
        승리 조건을 확인합니다. 마피아는 마피아 수가 시민 수 이상이면 승리합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            승리 여부
        """
        mafia_count = 0
        citizen_count = 0
        
        for player in players.values():
            if not player.get("alive", True):
                continue
                
            role = player.get("role")
            if role:
                if role.team == "마피아팀":
                    mafia_count += 1
                elif role.team == "시민팀":
                    citizen_count += 1
        
        # 마피아 수가 시민 수 이상이면 승리
        return mafia_count >= citizen_count and mafia_count > 0
