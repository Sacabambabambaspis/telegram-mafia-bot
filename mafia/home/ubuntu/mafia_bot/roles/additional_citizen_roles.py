"""
시민 역할 클래스 모듈 - 추가 역할

이 모듈은 시민팀에 속하는 추가 역할 클래스들을 정의합니다.
모든 시민 역할은 BaseRole 클래스를 상속받습니다.
"""

from typing import Dict, List, Optional, Tuple, Any
from mafia_bot.roles.base_role import BaseRole
import random


class BusDriver(BaseRole):
    """
    버스기사 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (시민팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        BusDriver 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "버스기사"
        self.description = "🚌 **버스기사**\n두 사람을 지목해 받는 결과를 바꿉니다."
        self.team = "시민팀"
        self.night_action = True
        self.priority = 70  # 의사(60)보다 높은 우선순위
        self.target_count = 2  # 두 명의 대상 필요
    
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            밤 행동 대상이 될 수 있는 플레이어 ID 목록
        """
        # 살아있는 플레이어 중 자신을 제외한 모든 플레이어가 대상
        targets = []
        for player_id, player in players.items():
            if player.get("alive", True) and player_id != self.player_id:
                targets.append(player_id)
        return targets
    
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                           night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다. 버스기사는 두 플레이어의 결과를 바꿉니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 버스기사 행동 정보 저장
        if "bus_driver_swap" not in night_actions:
            night_actions["bus_driver_swap"] = {
                "driver_id": self.player_id,
                "target1_id": target_id,
                "target2_id": None
            }
        elif night_actions["bus_driver_swap"]["driver_id"] == self.player_id:
            night_actions["bus_driver_swap"]["target2_id"] = target_id
        
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
        if "bus_driver_swap" in night_actions:
            swap = night_actions["bus_driver_swap"]
            if swap["driver_id"] == self.player_id and swap["target2_id"] is not None:
                target1_id = swap["target1_id"]
                target2_id = swap["target2_id"]
                
                if target1_id in players and target2_id in players:
                    target1_name = players[target1_id].get("name", "알 수 없음")
                    target2_name = players[target2_id].get("name", "알 수 없음")
                    
                    return f"당신은 {target1_name}와(과) {target2_name}의 결과를 바꿨습니다."
        
        return "행동에 실패했습니다."
    
    def on_night_end(self, players: Dict[int, Dict[str, Any]], 
                   night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤이 끝날 때 호출되는 메서드입니다. 버스기사는 두 플레이어의 결과를 바꿉니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        if "bus_driver_swap" in night_actions:
            swap = night_actions["bus_driver_swap"]
            if swap["target2_id"] is not None:
                target1_id = swap["target1_id"]
                target2_id = swap["target2_id"]
                
                # 두 플레이어에 대한 모든 행동 결과 교환
                for action_key, action_data in night_actions.items():
                    if action_key == "bus_driver_swap":
                        continue
                        
                    # 대상 ID가 있는 경우 교환
                    if isinstance(action_data, dict):
                        for key, value in action_data.items():
                            if key.endswith("_id") and key != "driver_id":
                                if value == target1_id:
                                    action_data[key] = target2_id
                                elif value == target2_id:
                                    action_data[key] = target1_id
        
        return night_actions


class Psycho(BaseRole):
    """
    정신병자 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (시민팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
        fake_role (str): 가짜로 사용하는 역할 이름
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Psycho 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "정신병자"
        self.description = "🤪 **정신병자**\n시민팀 직업의 능력을 사용하지만 결과는 랜덤입니다."
        self.team = "시민팀"
        self.night_action = True
        self.priority = 35  # 중간 우선순위
        
        # 랜덤하게 시민팀 역할 중 하나를 선택 (시민 제외)
        self.fake_roles = ["탐정", "의사", "기자"]
        self.fake_role = random.choice(self.fake_roles)
    
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            밤 행동 대상이 될 수 있는 플레이어 ID 목록
        """
        # 살아있는 플레이어 중 자신을 제외한 모든 플레이어가 대상
        targets = []
        for player_id, player in players.items():
            if player.get("alive", True) and player_id != self.player_id:
                targets.append(player_id)
        return targets
    
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                           night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다. 정신병자는 가짜 역할의 행동을 수행합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 정신병자 행동 정보 저장
        if "psycho_action" not in night_actions:
            night_actions["psycho_action"] = {
                "psycho_id": self.player_id,
                "target_id": target_id,
                "fake_role": self.fake_role
            }
        
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
        if "psycho_action" in night_actions:
            action = night_actions["psycho_action"]
            if action["psycho_id"] == self.player_id:
                target_id = action["target_id"]
                fake_role = action["fake_role"]
                
                if target_id in players:
                    target_name = players[target_id].get("name", "알 수 없음")
                    
                    # 랜덤한 결과 생성
                    if fake_role == "탐정":
                        teams = ["마피아팀", "시민팀", "중립팀"]
                        random_team = random.choice(teams)
                        return f"조사 결과: {target_name}은(는) {random_team}입니다."
                    
                    elif fake_role == "의사":
                        return f"당신은 {target_name}을(를) 치료했습니다."
                    
                    elif fake_role == "기자":
                        roles = ["마피아", "시민", "탐정", "의사", "선동가", "연쇄 살인마", "숭배자"]
                        random_role = random.choice(roles)
                        return f"취재 결과: {target_name}은(는) {random_role}입니다."
        
        return "행동에 실패했습니다."


class Bomber(BaseRole):
    """
    폭탄 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (시민팀)
        night_action (bool): 밤에 행동 가능 여부
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Bomber 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "폭탄"
        self.description = "💣 **폭탄**\n밤에 사망 시 공격자도 함께 죽입니다."
        self.team = "시민팀"
        self.night_action = False
    
    def on_death(self, player_data: Dict[str, Any], killer_id: Optional[int]) -> Tuple[Dict[str, Any], List[str]]:
        """
        사망 시 호출되는 메서드입니다. 폭탄은 공격자도 함께 죽입니다.
        
        Args:
            player_data: 플레이어 정보
            killer_id: 죽인 플레이어 ID (없을 수도 있음)
            
        Returns:
            업데이트된 플레이어 정보와 메시지 목록
        """
        messages = []
        
        # 밤에 사망했고 공격자가 있는 경우
        if killer_id is not None:
            messages.append(f"폭탄이 폭발했습니다! 공격자도 함께 사망합니다.")
            
            # 폭탄 폭발 정보 추가
            player_data["bomber_explosion"] = {
                "bomber_id": self.player_id,
                "killer_id": killer_id
            }
        
        return player_data, messages


class Witch(BaseRole):
    """
    마녀 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (시민팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Witch 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "마녀"
        self.description = "🧙‍♀️ **마녀**\n한 명에게 저주를 걸어 행동불능 상태로 만듭니다."
        self.team = "시민팀"
        self.night_action = True
        self.priority = 40  # 마피아 공격(50)보다 낮은 우선순위
    
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            밤 행동 대상이 될 수 있는 플레이어 ID 목록
        """
        # 살아있는 플레이어 중 자신을 제외한 모든 플레이어가 대상
        targets = []
        for player_id, player in players.items():
            if player.get("alive", True) and player_id != self.player_id:
                targets.append(player_id)
        return targets
    
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                           night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다. 마녀는 대상에게 저주를 겁니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 마녀 저주 정보 저장
        if "witch_curse" not in night_actions:
            night_actions["witch_curse"] = {
                "witch_id": self.player_id,
                "target_id": target_id
            }
        
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
        if "witch_curse" in night_actions:
            curse = night_actions["witch_curse"]
            if curse["witch_id"] == self.player_id:
                target_id = curse["target_id"]
                
                if target_id in players:
                    target_name = players[target_id].get("name", "알 수 없음")
                    return f"당신은 {target_name}에게 저주를 걸었습니다. 하루 동안 행동불능 상태가 됩니다."
        
        return "저주에 실패했습니다."
