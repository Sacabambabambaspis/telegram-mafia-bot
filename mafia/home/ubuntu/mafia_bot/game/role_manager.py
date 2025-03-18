"""
역할 관리자 모듈

이 모듈은 마피아 게임의 역할 할당과 관리를 담당하는 RoleManager 클래스를 정의합니다.
"""

import random
from typing import Dict, List, Optional, Set, Tuple, Any

from mafia_bot.roles.base_role import BaseRole
from mafia_bot.roles.mafia_roles import Mafia
from mafia_bot.roles.citizen_roles import Citizen, Detective, Doctor, Reporter, Agitator
from mafia_bot.roles.neutral_roles import SerialKiller, Cultist, Cupid, Thief


class RoleManager:
    """
    역할 관리자 클래스
    
    Attributes:
        settings (Dict[str, Any]): 게임 설정
        available_roles (Dict[str, type]): 사용 가능한 역할 클래스 목록
    """
    
    def __init__(self, settings: Dict[str, Any]):
        """
        RoleManager 클래스 초기화
        
        Args:
            settings: 게임 설정
        """
        self.settings = settings
        
        # 사용 가능한 역할 클래스 목록
        self.available_roles = {
            "마피아": Mafia,
            "탐정": Detective,
            "의사": Doctor,
            "기자": Reporter,
            "선동가": Agitator,
            "시민": Citizen,
            "연쇄 살인마": SerialKiller,
            "숭배자": Cultist,
            "큐피드": Cupid,
            "도둑": Thief
        }
    
    def assign_roles(self, player_ids: List[int]) -> Dict[int, BaseRole]:
        """
        플레이어들에게 역할을 할당합니다.
        
        Args:
            player_ids: 플레이어 ID 목록
            
        Returns:
            플레이어 ID를 키로, 할당된 역할을 값으로 하는 딕셔너리
        """
        # 플레이어 수에 맞게 역할 조정
        roles_to_assign = self._adjust_roles(len(player_ids))
        
        # 역할 할당
        assigned_roles: Dict[int, BaseRole] = {}
        random.shuffle(player_ids)
        
        for role_name, count in roles_to_assign.items():
            if count <= 0 or not player_ids:
                continue
                
            role_class = self.available_roles.get(role_name)
            if not role_class:
                continue
                
            for _ in range(min(count, len(player_ids))):
                if not player_ids:
                    break
                    
                player_id = player_ids.pop(0)
                assigned_roles[player_id] = role_class(player_id)
        
        # 남은 플레이어에게는 시민 역할 할당
        for player_id in player_ids:
            assigned_roles[player_id] = Citizen(player_id)
        
        # 정신병자 처리
        if self.settings.get("sub_role_enabled", True):
            self._assign_psycho(assigned_roles)
        
        return assigned_roles
    
    def _adjust_roles(self, player_count: int) -> Dict[str, int]:
        """
        플레이어 수에 맞게 역할 수를 조정합니다.
        
        Args:
            player_count: 플레이어 수
            
        Returns:
            역할 이름을 키로, 할당할 수를 값으로 하는 딕셔너리
        """
        # 기본 역할 수 복사
        role_counts = self.settings.get("role_counts", {}).copy()
        enabled_roles = self.settings.get("enabled_roles", {})
        
        # 비활성화된 역할 제거
        for role_name in list(role_counts.keys()):
            if not enabled_roles.get(role_name, True):
                role_counts[role_name] = 0
        
        # 플레이어 수에 따른 역할 조정
        total_special_roles = sum(role_counts.values())
        
        # 특수 역할이 플레이어 수보다 많으면 조정
        if total_special_roles > player_count:
            # 우선순위에 따라 역할 제거
            priority_order = [
                "시민", "마피아", "탐정", "의사", "기자", "선동가",
                "연쇄 살인마", "숭배자", "큐피드", "도둑"
            ]
            
            # 우선순위 역순으로 제거
            for role_name in reversed(priority_order):
                if role_name in role_counts and role_counts[role_name] > 0:
                    while (total_special_roles > player_count and 
                           role_counts[role_name] > 0):
                        role_counts[role_name] -= 1
                        total_special_roles -= 1
        
        # 마피아 수 조정 (플레이어 수의 1/4 ~ 1/3)
        min_mafia = max(1, player_count // 5)
        max_mafia = max(1, player_count // 3)
        
        if role_counts.get("마피아", 0) < min_mafia:
            role_counts["마피아"] = min_mafia
        elif role_counts.get("마피아", 0) > max_mafia:
            role_counts["마피아"] = max_mafia
        
        return role_counts
    
    def _assign_psycho(self, assigned_roles: Dict[int, BaseRole]) -> None:
        """
        정신병자 역할을 할당합니다.
        
        Args:
            assigned_roles: 할당된 역할 딕셔너리
        """
        # 시민팀 역할을 가진 플레이어 목록
        citizen_team_players = []
        
        for player_id, role in assigned_roles.items():
            if role.team == "시민팀":
                citizen_team_players.append(player_id)
        
        # 정신병자 수 계산 (시민팀의 약 20%)
        psycho_count = max(1, len(citizen_team_players) // 5)
        
        # 정신병자 할당
        if citizen_team_players:
            psycho_players = random.sample(citizen_team_players, 
                                          min(psycho_count, len(citizen_team_players)))
            
            for player_id in psycho_players:
                assigned_roles[player_id].set_psycho(True)
    
    def get_team_players(self, assigned_roles: Dict[int, BaseRole], team: str) -> List[int]:
        """
        특정 팀에 속한 플레이어 ID 목록을 반환합니다.
        
        Args:
            assigned_roles: 할당된 역할 딕셔너리
            team: 팀 이름 ("마피아팀", "시민팀", "중립팀")
            
        Returns:
            해당 팀에 속한 플레이어 ID 목록
        """
        team_players = []
        
        for player_id, role in assigned_roles.items():
            if role.team == team:
                team_players.append(player_id)
        
        return team_players
    
    def get_role_description(self, role_name: str) -> str:
        """
        역할 설명을 반환합니다.
        
        Args:
            role_name: 역할 이름
            
        Returns:
            역할 설명
        """
        role_class = self.available_roles.get(role_name)
        if role_class:
            role = role_class()
            return role.description
        
        return f"알 수 없는 역할: {role_name}"