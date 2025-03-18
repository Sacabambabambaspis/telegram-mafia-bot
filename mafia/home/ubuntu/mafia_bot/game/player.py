"""
플레이어 클래스 모듈

이 모듈은 마피아 게임의 플레이어를 관리하는 Player 클래스를 정의합니다.
"""

from typing import Dict, Any, Optional, List, Set
from mafia_bot.roles.base_role import BaseRole


class Player:
    """
    게임 플레이어 클래스
    
    Attributes:
        user_id (int): 텔레그램 사용자 ID
        name (str): 플레이어 이름
        chat_id (int): 플레이어의 개인 채팅 ID
        role (Optional[BaseRole]): 플레이어의 역할
        alive (bool): 생존 여부
        vote_count (int): 받은 투표 수
        voted_for (Optional[int]): 투표한 플레이어 ID
        is_psycho (bool): 정신병자 여부
        lovers (Set[int]): 연인 관계인 플레이어 ID 집합
        protected (bool): 보호 여부 (의사 등에 의한 보호)
        silenced (bool): 침묵 여부 (마녀 등에 의한 침묵)
        last_will (str): 유언
    """
    
    def __init__(self, user_id: int, name: str, chat_id: int):
        """
        Player 클래스 초기화
        
        Args:
            user_id: 텔레그램 사용자 ID
            name: 플레이어 이름
            chat_id: 플레이어의 개인 채팅 ID
        """
        self.user_id: int = user_id
        self.name: str = name
        self.chat_id: int = chat_id
        self.role: Optional[BaseRole] = None
        self.alive: bool = True
        self.vote_count: int = 0
        self.voted_for: Optional[int] = None
        self.is_psycho: bool = False
        self.lovers: Set[int] = set()
        self.protected: bool = False
        self.silenced: bool = False
        self.last_will: str = ""
    
    def assign_role(self, role: BaseRole) -> None:
        """
        플레이어에게 역할을 할당합니다.
        
        Args:
            role: 할당할 역할
        """
        self.role = role
        role.set_player(self.user_id)
    
    def set_psycho(self, is_psycho: bool = True) -> None:
        """
        정신병자 여부를 설정합니다.
        
        Args:
            is_psycho: 정신병자 여부
        """
        self.is_psycho = is_psycho
        if self.role:
            self.role.set_psycho(is_psycho)
    
    def add_lover(self, lover_id: int) -> None:
        """
        연인을 추가합니다.
        
        Args:
            lover_id: 연인 플레이어 ID
        """
        self.lovers.add(lover_id)
    
    def reset_vote(self) -> None:
        """
        투표 정보를 초기화합니다.
        """
        self.vote_count = 0
        self.voted_for = None
    
    def add_vote(self, voter_id: int, players: Dict[int, 'Player']) -> int:
        """
        투표를 받습니다.
        
        Args:
            voter_id: 투표한 플레이어 ID
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            실제 적용된 투표 수
        """
        vote_weight = 1
        
        # 역할에 따른 투표 가중치 적용
        if self.role:
            vote_weight = self.role.on_voted(voter_id, self.to_dict(players))
        
        self.vote_count += vote_weight
        return vote_weight
    
    def vote_for(self, target_id: int) -> None:
        """
        다른 플레이어에게 투표합니다.
        
        Args:
            target_id: 투표 대상 플레이어 ID
        """
        self.voted_for = target_id
    
    def kill(self, killer_id: Optional[int], players: Dict[int, 'Player']) -> List[str]:
        """
        플레이어를 사망 처리합니다.
        
        Args:
            killer_id: 죽인 플레이어 ID (없을 수도 있음)
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            사망 처리 결과 메시지 목록
        """
        if not self.alive:
            return []
        
        # 보호 상태인 경우 사망하지 않음
        if self.protected:
            return ["보호되어 사망하지 않았습니다."]
        
        messages = []
        self.alive = False
        
        # 역할의 사망 이벤트 처리
        if self.role:
            _, role_messages = self.role.on_death(self.to_dict(players), killer_id)
            messages.extend(role_messages)
        
        # 연인 관계 처리
        if self.lovers:
            for lover_id in self.lovers:
                if lover_id in players and players[lover_id].alive:
                    lover_messages = players[lover_id].kill(None, players)
                    messages.append(f"{players[lover_id].name}이(가) 연인의 죽음을 따라 사망했습니다.")
                    messages.extend(lover_messages)
        
        return messages
    
    def protect(self) -> None:
        """
        플레이어를 보호 상태로 설정합니다.
        """
        self.protected = True
    
    def silence(self) -> None:
        """
        플레이어를 침묵 상태로 설정합니다.
        """
        self.silenced = True
    
    def reset_status(self) -> None:
        """
        플레이어의 상태를 초기화합니다. (보호, 침묵 등)
        """
        self.protected = False
        self.silenced = False
    
    def set_last_will(self, text: str) -> None:
        """
        유언을 설정합니다.
        
        Args:
            text: 유언 내용
        """
        self.last_will = text
    
    def to_dict(self, players: Dict[int, 'Player']) -> Dict[int, Dict[str, Any]]:
        """
        플레이어 정보를 딕셔너리로 변환합니다.
        
        Args:
            players: 게임에 참여 중인 플레이어 정보
            
        Returns:
            플레이어 정보를 담은 딕셔너리
        """
        players_dict = {}
        
        for player_id, player in players.items():
            players_dict[player_id] = {
                "name": player.name,
                "role": player.role,
                "alive": player.alive,
                "chat_id": player.chat_id,
                "is_psycho": player.is_psycho,
                "lovers": player.lovers,
                "protected": player.protected,
                "silenced": player.silenced,
                "vote_count": player.vote_count,
                "voted_for": player.voted_for
            }
        
        return players_dict
    
    def get_role_info(self) -> str:
        """
        플레이어의 역할 정보를 문자열로 반환합니다.
        
        Returns:
            역할 정보 문자열
        """
        if not self.role:
            return "역할이 아직 할당되지 않았습니다."
        
        role_info = self.role.get_role_info()
        
        info_text = f"{role_info['description']}\n\n"
        info_text += f"팀: {role_info['team']}\n"
        
        if self.is_psycho:
            info_text += "\n⚠️ 당신은 정신병자입니다. 실제 능력은 발동하지 않습니다."
        
        if self.lovers:
            info_text += "\n\n💘 당신은 연인 관계입니다. 연인이 죽으면 함께 죽습니다."
        
        return info_text
