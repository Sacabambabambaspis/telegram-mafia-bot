"""
시민 역할 클래스 모듈

이 모듈은 시민팀에 속하는 역할 클래스들을 정의합니다.
모든 시민 역할은 BaseRole 클래스를 상속받습니다.
"""

from typing import Dict, List, Optional, Tuple, Any
from mafia_bot.roles.base_role import BaseRole


class Citizen(BaseRole):
    """
    기본 시민 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (시민팀)
        night_action (bool): 밤에 행동 가능 여부
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Citizen 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "시민"
        self.description = "👤 **시민**\n토론과 투표에 참여합니다."
        self.team = "시민팀"
        self.night_action = False
    
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        시민은 밤 행동이 없으므로 빈 리스트를 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            빈 리스트
        """
        return []
    
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                            night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다. 시민은 밤 행동이 없습니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        return night_actions
    
    def check_win_condition(self, players: Dict[int, Dict[str, Any]]) -> bool:
        """
        승리 조건을 확인합니다. 시민은 모든 마피아가 제거되면 승리합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            승리 여부
        """
        # 살아있는 마피아가 있는지 확인
        for player in players.values():
            if not player.get("alive", True):
                continue
                
            role = player.get("role")
            if role and role.team == "마피아팀":
                return False
        
        # 살아있는 시민이 있는지 확인
        citizen_alive = False
        for player in players.values():
            if player.get("alive", True):
                role = player.get("role")
                if role and role.team == "시민팀":
                    citizen_alive = True
                    break
        
        # 모든 마피아가 제거되고 시민이 살아있으면 승리
        return citizen_alive


class Detective(BaseRole):
    """
    탐정 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (시민팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Detective 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "탐정"
        self.description = "🕵️ **탐정**\n한 명의 정체를 조사합니다."
        self.team = "시민팀"
        self.night_action = True
        self.priority = 30
    
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
        밤 행동을 수행합니다. 탐정은 대상의 역할을 조사합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 탐정 조사 정보 저장
        if "detective_investigate" not in night_actions:
            target_role = None
            target_team = None
            
            if target_id in players and players[target_id].get("role"):
                target_role = players[target_id]["role"].name
                target_team = players[target_id]["role"].team
            
            night_actions["detective_investigate"] = {
                "detective_id": self.player_id,
                "target_id": target_id,
                "target_role": target_role,
                "target_team": target_team
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
        if "detective_investigate" in night_actions:
            investigation = night_actions["detective_investigate"]
            if investigation["detective_id"] == self.player_id:
                target_id = investigation["target_id"]
                target_team = investigation["target_team"]
                
                if target_id in players:
                    target_name = players[target_id].get("name", "알 수 없음")
                    
                    if target_team == "마피아팀":
                        return f"조사 결과: {target_name}은(는) 마피아팀입니다!"
                    elif target_team == "시민팀":
                        return f"조사 결과: {target_name}은(는) 시민팀입니다."
                    elif target_team == "중립팀":
                        return f"조사 결과: {target_name}은(는) 중립팀입니다."
        
        return "조사에 실패했습니다."


class Doctor(BaseRole):
    """
    의사 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (시민팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
        self_heal_count (int): 자기 자신을 치료할 수 있는 횟수
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Doctor 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "의사"
        self.description = "👩‍⚕️ **의사**\n한 명을 치료해 공격을 막습니다."
        self.team = "시민팀"
        self.night_action = True
        self.priority = 60  # 마피아 공격(50) 이후에 실행
        self.self_heal_count = 1  # 자기 자신을 치료할 수 있는 횟수
    
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            밤 행동 대상이 될 수 있는 플레이어 ID 목록
        """
        # 살아있는 모든 플레이어가 대상
        targets = []
        for player_id, player in players.items():
            if player.get("alive", True):
                # 자기 자신은 self_heal_count가 0이면 대상에서 제외
                if player_id == self.player_id and self.self_heal_count <= 0:
                    continue
                targets.append(player_id)
        return targets
    
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                            night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다. 의사는 대상을 치료합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 의사 치료 정보 저장
        if "doctor_heal" not in night_actions:
            night_actions["doctor_heal"] = {"doctor_id": self.player_id, "target_id": target_id}
            
            # 자기 자신을 치료한 경우 self_heal_count 감소
            if target_id == self.player_id:
                self.self_heal_count -= 1
        
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
        if "doctor_heal" in night_actions:
            heal = night_actions["doctor_heal"]
            if heal["doctor_id"] == self.player_id:
                target_id = heal["target_id"]
                
                if target_id in players:
                    target_name = players[target_id].get("name", "알 수 없음")
                    
                    if target_id == self.player_id:
                        return f"당신은 자신을 치료했습니다. (남은 자가 치료 횟수: {self.self_heal_count})"
                    else:
                        return f"당신은 {target_name}을(를) 치료했습니다."
        
        return "치료에 실패했습니다."
    
    def on_day_start(self, players: Dict[int, Dict[str, Any]], 
                    night_actions: Dict[str, Any]) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
        """
        낮이 시작될 때 호출되는 메서드입니다. 의사는 마피아 공격을 막을 수 있습니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 players와 공지 메시지 목록
        """
        messages = []
        
        # 의사가 치료한 대상이 마피아 공격 대상인 경우, 공격을 막음
        if "doctor_heal" in night_actions and "mafia_kill" in night_actions:
            heal_target = night_actions["doctor_heal"]["target_id"]
            kill_target = night_actions["mafia_kill"]["target_id"]
            
            if heal_target == kill_target:
                # 마피아 공격을 막았음을 표시
                night_actions["mafia_kill"]["blocked"] = True
                
                # 공격 대상 이름 가져오기
                target_name = "알 수 없음"
                if heal_target in players:
                    target_name = players[heal_target].get("name", "알 수 없음")
                
                messages.append(f"의사가 {target_name}을(를) 치료하여 마피아의 공격을 막았습니다!")
        
        return players, messages


class Reporter(BaseRole):
    """
    기자 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (시민팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Reporter 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "기자"
        self.description = "📰 **기자**\n밤 방문 기록을 수집합니다."
        self.team = "시민팀"
        self.night_action = True
        self.priority = 90  # 대부분의 행동이 끝난 후 실행
    
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
        밤 행동을 수행합니다. 기자는 대상의 방문 기록을 조사합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 기자 조사 정보 저장
        if "reporter_investigate" not in night_actions:
            # 대상을 방문한 플레이어 목록 수집
            visitors = []
            for action_type, action_data in night_actions.items():
                if isinstance(action_data, dict) and "target_id" in action_data:
                    if action_data["target_id"] == target_id:
                        actor_id = None
                        for key in ["killer_id", "detective_id", "doctor_id"]:
                            if key in action_data:
                                actor_id = action_data[key]
                                break
                        
                        if actor_id is not None and actor_id != self.player_id:
                            visitors.append(actor_id)
            
            night_actions["reporter_investigate"] = {
                "reporter_id": self.player_id,
                "target_id": target_id,
                "visitors": visitors
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
        if "reporter_investigate" in night_actions:
            investigation = night_actions["reporter_investigate"]
            if investigation["reporter_id"] == self.player_id:
                target_id = investigation["target_id"]
                visitors = investigation["visitors"]
                
                if target_id in players:
                    target_name = players[target_id].get("name", "알 수 없음")
                    
                    if not visitors:
                        return f"{target_name}을(를) 방문한 사람이 없습니다."
                    else:
                        visitor_names = []
                        for visitor_id in visitors:
                            if visitor_id in players:
                                visitor_names.append(players[visitor_id].get("name", "알 수 없음"))
                        
                        return f"{target_name}을(를) 방문한 사람: {', '.join(visitor_names)}"
        
        return "조사에 실패했습니다."


class Agitator(BaseRole):
    """
    선동가 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (시민팀)
        night_action (bool): 밤에 행동 가능 여부
        extra_votes (int): 추가 투표 수
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Agitator 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "선동가"
        self.description = "📢 **선동가**\n투표에서 미리 2표를 확보합니다."
        self.team = "시민팀"
        self.night_action = False
        self.extra_votes = 2  # 추가 투표 수
    
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        선동가는 밤 행동이 없으므로 빈 리스트를 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            빈 리스트
        """
        return []
    
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                            night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다. 선동가는 밤 행동이 없습니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        return night_actions
    
    def on_voted(self, voter_id: int, players: Dict[int, Dict[str, Any]]) -> int:
        """
        투표를 받았을 때 호출되는 메서드입니다.
        
        Args:
            voter_id: 투표한 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            실제 적용될 투표 수 (기본값: 1)
        """
        # 선동가는 투표 시 추가 투표 수를 가짐
        return 1 + self.extra_votes