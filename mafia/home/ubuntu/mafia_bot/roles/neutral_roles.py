"""
중립 역할 클래스 모듈

이 모듈은 중립팀에 속하는 역할 클래스들을 정의합니다.
모든 중립 역할은 BaseRole 클래스를 상속받습니다.
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from mafia_bot.roles.base_role import BaseRole


class SerialKiller(BaseRole):
    """
    연쇄 살인마 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (중립팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        SerialKiller 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "연쇄 살인마"
        self.description = "🔪 **연쇄 살인마**\n독자적으로 암살합니다."
        self.team = "중립팀"
        self.night_action = True
        self.priority = 40  # 마피아(50)보다 먼저 실행
    
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
        밤 행동을 수행합니다. 연쇄 살인마는 대상을 살해합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 연쇄 살인마 공격 정보 저장
        if "serial_killer_kill" not in night_actions:
            night_actions["serial_killer_kill"] = {"target_id": target_id, "killer_id": self.player_id}
        
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
        if "serial_killer_kill" in night_actions:
            target_id = night_actions["serial_killer_kill"]["target_id"]
            if target_id in players:
                target_name = players[target_id].get("name", "알 수 없음")
                return f"당신은 {target_name}을(를) 공격했습니다."
        
        return "공격에 실패했습니다."
    
    def check_win_condition(self, players: Dict[int, Dict[str, Any]]) -> bool:
        """
        승리 조건을 확인합니다. 연쇄 살인마는 자신을 제외한 모든 플레이어가 제거되면 승리합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            승리 여부
        """
        # 살아있는 플레이어 수 확인
        alive_count = 0
        for player_id, player in players.items():
            if player.get("alive", True):
                alive_count += 1
                
                # 자신이 아닌 살아있는 플레이어가 있으면 승리 조건 미달성
                if player_id != self.player_id:
                    return False
        
        # 자신만 살아있으면 승리
        return alive_count == 1 and players.get(self.player_id, {}).get("alive", False)


class Cultist(BaseRole):
    """
    숭배자 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (중립팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
        cultists (Set[int]): 숭배자 그룹에 속한 플레이어 ID 집합
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Cultist 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "숭배자"
        self.description = "🙏 **숭배자**\n다른 플레이어를 숭배자로 전환합니다."
        self.team = "중립팀"
        self.night_action = True
        self.priority = 20
        self.cultists: Set[int] = set()
        if player_id is not None:
            self.cultists.add(player_id)
    
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            밤 행동 대상이 될 수 있는 플레이어 ID 목록
        """
        # 살아있는 플레이어 중 숭배자 그룹에 속하지 않은 플레이어만 대상
        targets = []
        for player_id, player in players.items():
            if (player.get("alive", True) and 
                player_id not in self.cultists):
                targets.append(player_id)
        return targets
    
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                            night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다. 숭배자는 대상을 숭배자로 전환합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 숭배자 전환 정보 저장
        if "cultist_convert" not in night_actions:
            night_actions["cultist_convert"] = {
                "cultist_id": self.player_id,
                "target_id": target_id,
                "success": True  # 기본적으로 성공으로 설정
            }
            
            # 마피아는 전환 실패
            if target_id in players and players[target_id].get("role"):
                target_role = players[target_id]["role"]
                if target_role.team == "마피아팀":
                    night_actions["cultist_convert"]["success"] = False
        
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
        if "cultist_convert" in night_actions:
            convert = night_actions["cultist_convert"]
            if convert["cultist_id"] == self.player_id:
                target_id = convert["target_id"]
                success = convert["success"]
                
                if target_id in players:
                    target_name = players[target_id].get("name", "알 수 없음")
                    
                    if success:
                        # 전환 성공 시 숭배자 그룹에 추가
                        self.cultists.add(target_id)
                        return f"{target_name}을(를) 숭배자로 전환했습니다! 현재 숭배자: {len(self.cultists)}명"
                    else:
                        return f"{target_name}을(를) 전환하는데 실패했습니다."
        
        return "전환에 실패했습니다."
    
    def on_day_start(self, players: Dict[int, Dict[str, Any]], 
                    night_actions: Dict[str, Any]) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
        """
        낮이 시작될 때 호출되는 메서드입니다. 숭배자는 전환된 플레이어의 역할을 변경합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 players와 공지 메시지 목록
        """
        messages = []
        
        if "cultist_convert" in night_actions:
            convert = night_actions["cultist_convert"]
            if convert["success"]:
                target_id = convert["target_id"]
                
                if target_id in players and players[target_id].get("alive", True):
                    # 대상 플레이어의 역할을 숭배자로 변경
                    players[target_id]["role"] = Cultist(target_id)
                    players[target_id]["role"].cultists = self.cultists.copy()
                    
                    # 공개 메시지는 없음 (비밀 전환)
        
        return players, messages
    
    def check_win_condition(self, players: Dict[int, Dict[str, Any]]) -> bool:
        """
        승리 조건을 확인합니다. 숭배자는 살아있는 플레이어의 절반 이상이 숭배자면 승리합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            승리 여부
        """
        # 살아있는 플레이어 수와 살아있는 숭배자 수 확인
        alive_count = 0
        alive_cultist_count = 0
        
        for player_id, player in players.items():
            if player.get("alive", True):
                alive_count += 1
                
                if player_id in self.cultists:
                    alive_cultist_count += 1
        
        # 살아있는 플레이어의 절반 이상이 숭배자면 승리
        return alive_cultist_count >= (alive_count / 2) and alive_cultist_count > 0


class Cupid(BaseRole):
    """
    큐피드 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (중립팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
        used_ability (bool): 능력 사용 여부
        lovers (Set[int]): 연인으로 지정된 플레이어 ID 집합
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Cupid 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "큐피드"
        self.description = "💘 **큐피드**\n두 명을 연인으로 묶습니다."
        self.team = "중립팀"
        self.night_action = True
        self.priority = 10  # 게임 시작 시 가장 먼저 실행
        self.used_ability = False
        self.lovers: Set[int] = set()
    
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            밤 행동 대상이 될 수 있는 플레이어 ID 목록
        """
        # 이미 능력을 사용했거나 연인이 2명 이상이면 대상 없음
        if self.used_ability or len(self.lovers) >= 2:
            return []
        
        # 살아있는 모든 플레이어가 대상
        targets = []
        for player_id, player in players.items():
            if player.get("alive", True):
                targets.append(player_id)
        return targets
    
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                            night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다. 큐피드는 대상을 연인으로 지정합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 큐피드 연인 지정 정보 저장
        if "cupid_match" not in night_actions:
            night_actions["cupid_match"] = {
                "cupid_id": self.player_id,
                "lovers": []
            }
        
        # 연인 목록에 추가 (최대 2명)
        if len(night_actions["cupid_match"]["lovers"]) < 2:
            night_actions["cupid_match"]["lovers"].append(target_id)
            self.lovers.add(target_id)
        
        # 2명을 지정했으면 능력 사용 완료
        if len(night_actions["cupid_match"]["lovers"]) >= 2:
            self.used_ability = True
        
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
        if "cupid_match" in night_actions:
            match = night_actions["cupid_match"]
            if match["cupid_id"] == self.player_id:
                lovers = match["lovers"]
                
                if len(lovers) == 2:
                    lover1_name = players[lovers[0]].get("name", "알 수 없음") if lovers[0] in players else "알 수 없음"
                    lover2_name = players[lovers[1]].get("name", "알 수 없음") if lovers[1] in players else "알 수 없음"
                    
                    return f"{lover1_name}와(과) {lover2_name}을(를) 연인으로 지정했습니다."
                elif len(lovers) == 1:
                    lover_name = players[lovers[0]].get("name", "알 수 없음") if lovers[0] in players else "알 수 없음"
                    
                    return f"{lover_name}을(를) 첫 번째 연인으로 지정했습니다. 두 번째 연인을 선택하세요."
        
        return "연인 지정에 실패했습니다."
    
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
        승리 조건을 확인합니다. 큐피드는 연인 둘만 살아남으면 승리합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            승리 여부
        """
        # 연인이 2명 미만이면 승리 불가
        if len(self.lovers) < 2:
            return False
        
        # 살아있는 플레이어 수 확인
        alive_count = 0
        alive_lovers = []
        
        for player_id, player in players.items():
            if player.get("alive", True):
                alive_count += 1
                
                if player_id in self.lovers:
                    alive_lovers.append(player_id)
        
        # 살아있는 플레이어가 연인 둘뿐이면 승리
        return alive_count == 2 and len(alive_lovers) == 2


class Thief(BaseRole):
    """
    도둑 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (중립팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
        used_ability (bool): 능력 사용 여부
        stolen_role (Optional[BaseRole]): 훔친 역할
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Thief 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "도둑"
        self.description = "🦹 **도둑**\n타겟의 역할을 대신합니다."
        self.team = "중립팀"
        self.night_action = True
        self.priority = 15
        self.used_ability = False
        self.stolen_role: Optional[BaseRole] = None
    
    def get_night_action_targets(self, players: Dict[int, Dict[str, Any]]) -> List[int]:
        """
        밤 행동 대상 플레이어 목록을 반환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            밤 행동 대상이 될 수 있는 플레이어 ID 목록
        """
        # 이미 능력을 사용했으면 대상 없음
        if self.used_ability:
            return []
        
        # 살아있는 플레이어 중 자신을 제외한 모든 플레이어가 대상
        targets = []
        for player_id, player in players.items():
            if player.get("alive", True) and player_id != self.player_id:
                targets.append(player_id)
        return targets
    
    def perform_night_action(self, target_id: int, players: Dict[int, Dict[str, Any]], 
                            night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤 행동을 수행합니다. 도둑은 대상의 역할을 훔칩니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 도둑 역할 훔치기 정보 저장
        if "thief_steal" not in night_actions and not self.used_ability:
            target_role = None
            
            if target_id in players and players[target_id].get("role"):
                # 대상의 역할 정보 복사
                target_role = type(players[target_id]["role"])(self.player_id)
            
            night_actions["thief_steal"] = {
                "thief_id": self.player_id,
                "target_id": target_id,
                "target_role": target_role
            }
            
   <response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>