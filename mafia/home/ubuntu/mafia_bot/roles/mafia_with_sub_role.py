"""
마피아 역할 클래스 모듈 - 서브 직업 시스템

이 모듈은 마피아팀에 속하는 역할 클래스들을 정의합니다.
모든 마피아 역할은 BaseRole 클래스를 상속받습니다.
"""

from typing import Dict, List, Optional, Tuple, Any
from mafia_bot.roles.base_role import BaseRole
import random


class MafiaWithSubRole(BaseRole):
    """
    서브 직업을 가진 마피아 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (마피아팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
        sub_role (str): 서브 직업 이름
        sub_role_used (bool): 서브 직업 능력 사용 여부
        action_type (str): 현재 선택한 행동 유형 ("kill" 또는 "sub_role")
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        MafiaWithSubRole 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "마피아"
        self.description = "🔪 **마피아**\n밤에 한 명을 죽이거나 서브 직업 능력을 사용할 수 있습니다."
        self.team = "마피아팀"
        self.night_action = True
        self.priority = 50
        
        # 서브 직업 설정
        self.sub_roles = ["기자", "선동가", "시민"]
        self.sub_role = None
        self.sub_role_used = False
        self.action_type = "kill"  # 기본 행동은 살해
    
    def set_sub_role(self, sub_role: str) -> None:
        """
        서브 직업을 설정합니다.
        
        Args:
            sub_role: 서브 직업 이름
        """
        if sub_role in self.sub_roles:
            self.sub_role = sub_role
            
            # 서브 직업에 따라 설명 업데이트
            if sub_role == "기자":
                self.description += "\n📰 **서브 직업: 기자**\n한 명의 역할을 알아낼 수 있습니다."
            elif sub_role == "선동가":
                self.description += "\n📢 **서브 직업: 선동가**\n한 명의 투표 가중치를 2배로 만듭니다."
            elif sub_role == "시민":
                self.description += "\n👤 **서브 직업: 시민**\n특별한 능력이 없습니다."
    
    def set_action_type(self, action_type: str) -> None:
        """
        행동 유형을 설정합니다.
        
        Args:
            action_type: 행동 유형 ("kill" 또는 "sub_role")
        """
        if action_type in ["kill", "sub_role"]:
            self.action_type = action_type
    
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            밤 행동 대상이 될 수 있는 플레이어 ID 목록
        """
        # 살아있는 플레이어 중 자신과 다른 마피아를 제외한 모든 플레이어가 대상
        targets = []
        for player_id, player in players.items():
            if not player.get("alive", True):
                continue
                
            if player_id == self.player_id:
                continue
                
            role = player.get("role")
            if role and role.team == "마피아팀":
                continue
                
            targets.append(player_id)
        
        return targets
    
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                           night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다. 마피아는 대상을 죽이거나 서브 직업 능력을 사용합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        if self.action_type == "kill":
            # 마피아 살해 정보 저장
            if "mafia_kill" not in night_actions:
                night_actions["mafia_kill"] = {
                    "killer_id": self.player_id,
                    "target_id": target_id
                }
        elif self.action_type == "sub_role" and not self.sub_role_used:
            # 서브 직업 능력 사용
            if self.sub_role == "기자":
                if "mafia_reporter" not in night_actions:
                    night_actions["mafia_reporter"] = {
                        "reporter_id": self.player_id,
                        "target_id": target_id
                    }
                    self.sub_role_used = True
            elif self.sub_role == "선동가":
                if "mafia_agitator" not in night_actions:
                    night_actions["mafia_agitator"] = {
                        "agitator_id": self.player_id,
                        "target_id": target_id
                    }
                    self.sub_role_used = True
        
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
        if self.action_type == "kill" and "mafia_kill" in night_actions:
            kill = night_actions["mafia_kill"]
            if kill["killer_id"] == self.player_id:
                target_id = kill["target_id"]
                
                if target_id in players:
                    target_name = players[target_id].get("name", "알 수 없음")
                    return f"당신은 {target_name}을(를) 공격했습니다."
        
        elif self.action_type == "sub_role":
            if self.sub_role == "기자" and "mafia_reporter" in night_actions:
                report = night_actions["mafia_reporter"]
                if report["reporter_id"] == self.player_id:
                    target_id = report["target_id"]
                    
                    if target_id in players and "role" in players[target_id]:
                        target_name = players[target_id].get("name", "알 수 없음")
                        target_role = players[target_id]["role"].name
                        return f"취재 결과: {target_name}은(는) {target_role}입니다."
            
            elif self.sub_role == "선동가" and "mafia_agitator" in night_actions:
                agitate = night_actions["mafia_agitator"]
                if agitate["agitator_id"] == self.player_id:
                    target_id = agitate["target_id"]
                    
                    if target_id in players:
                        target_name = players[target_id].get("name", "알 수 없음")
                        return f"당신은 {target_name}의 투표 가중치를 2배로 만들었습니다."
        
        return "행동에 실패했습니다."
    
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
