"""
중립 역할 클래스 모듈 - 추가 역할

이 모듈은 중립팀에 속하는 추가 역할 클래스들을 정의합니다.
모든 중립 역할은 BaseRole 클래스를 상속받습니다.
"""

from typing import Dict, List, Optional, Tuple, Any
from mafia_bot.roles.base_role import BaseRole


class Architect(BaseRole):
    """
    설계자 역할 클래스
    
    Attributes:
        name (str): 역할 이름
        description (str): 역할 설명
        team (str): 소속 팀 (중립팀)
        night_action (bool): 밤에 행동 가능 여부
        priority (int): 밤 행동 우선순위 (낮을수록 먼저 실행)
        predicted_roles (Dict[int, str]): 예측한 역할 정보
    """
    
    def __init__(self, player_id: Optional[int] = None):
        """
        Architect 클래스 초기화
        
        Args:
            player_id: 이 역할을 가진 플레이어 ID
        """
        super().__init__(player_id)
        self.name = "설계자"
        self.description = "🏗️ **설계자**\n직업을 예측하여 성공 시 대상을 게임에서 제거합니다."
        self.team = "중립팀"
        self.night_action = True
        self.priority = 45  # 중간 우선순위
        self.predicted_roles = {}  # 플레이어 ID를 키로, 예측한 역할을 값으로 하는 딕셔너리
    
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
        밤 행동을 수행합니다. 설계자는 대상의 역할을 예측합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        # 설계자 예측 정보 저장
        if "architect_predict" not in night_actions:
            # 예측할 역할 목록
            available_roles = [
                "마피아", "탐정", "의사", "기자", "선동가", "시민", 
                "연쇄 살인마", "숭배자", "큐피드", "도둑", 
                "버스기사", "정신병자", "폭탄", "마녀", "설계자"
            ]
            
            # 예측 정보 저장
            night_actions["architect_predict"] = {
                "architect_id": self.player_id,
                "target_id": target_id,
                "available_roles": available_roles,
                "predicted_role": None  # 이 값은 클라이언트에서 선택 후 업데이트됨
            }
        
        return night_actions
    
    def update_prediction(self, target_id: int, predicted_role: str) -> None:
        """
        예측한 역할 정보를 업데이트합니다.
        
        Args:
            target_id: 대상 플레이어 ID
            predicted_role: 예측한 역할
        """
        self.predicted_roles[target_id] = predicted_role
    
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
        if "architect_predict" in night_actions:
            predict = night_actions["architect_predict"]
            if predict["architect_id"] == self.player_id:
                target_id = predict["target_id"]
                predicted_role = predict.get("predicted_role")
                
                if target_id in players and predicted_role:
                    target_name = players[target_id].get("name", "알 수 없음")
                    actual_role = None
                    
                    if "role" in players[target_id]:
                        actual_role = players[target_id]["role"].name
                    
                    if actual_role == predicted_role:
                        return f"예측 성공! {target_name}은(는) {predicted_role}입니다. 대상은 게임에서 제거됩니다."
                    else:
                        return f"예측 실패! {target_name}은(는) {predicted_role}이(가) 아닙니다. 당신은 게임에서 제거됩니다."
        
        return "예측에 실패했습니다."
    
    def on_night_end(self, players: Dict[int, Dict[str, Any]], 
                   night_actions: Dict[str, Any]) -> Dict[str, Any]:
        """
        밤이 끝날 때 호출되는 메서드입니다. 설계자는 예측 결과에 따라 플레이어를 제거합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            night_actions: 이번 밤에 수행된 행동 정보
            
        Returns:
            업데이트된 night_actions
        """
        if "architect_predict" in night_actions:
            predict = night_actions["architect_predict"]
            if predict["architect_id"] == self.player_id:
                target_id = predict["target_id"]
                predicted_role = predict.get("predicted_role")
                
                if target_id in players and predicted_role:
                    actual_role = None
                    
                    if "role" in players[target_id]:
                        actual_role = players[target_id]["role"].name
                    
                    # 예측 결과에 따라 처리
                    if actual_role == predicted_role:
                        # 예측 성공: 대상 제거
                        night_actions["architect_result"] = {
                            "architect_id": self.player_id,
                            "target_id": target_id,
                            "success": True
                        }
                    else:
                        # 예측 실패: 설계자 제거
                        night_actions["architect_result"] = {
                            "architect_id": self.player_id,
                            "target_id": None,
                            "success": False
                        }
        
        return night_actions
    
    def check_win_condition(self, players: Dict[int, Dict[str, Any]]) -> bool:
        """
        승리 조건을 확인합니다. 설계자는 생존하면 승리합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            승리 여부
        """
        # 설계자가 살아있으면 승리
        for player in players.values():
            if player.get("player_id") == self.player_id and player.get("alive", False):
                return True
        
        return False
