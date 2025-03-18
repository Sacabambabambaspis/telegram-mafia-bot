"""
테스트 스크립트

이 파일은 마피아 게임 봇의 기능을 테스트하기 위한 스크립트입니다.
"""

import logging
import os
import unittest
from unittest.mock import MagicMock, patch

from mafia_bot.roles.base_role import BaseRole
from mafia_bot.roles.mafia_roles import Mafia
from mafia_bot.roles.citizen_roles import Citizen, Detective, Doctor
from mafia_bot.game.player import Player
from mafia_bot.game.role_manager import RoleManager
from mafia_bot.game.phase_manager import PhaseManager
from mafia_bot.game.game_manager import GameManager


class TestRoles(unittest.TestCase):
    """역할 관련 테스트 클래스"""
    
    def test_base_role(self):
        """기본 역할 클래스 테스트"""
        # BaseRole은 추상 클래스이므로 직접 인스턴스화할 수 없음
        # 대신 구체적인 역할 클래스로 테스트
        role = Mafia(1)
        self.assertEqual(role.player_id, 1)
        self.assertEqual(role.name, "마피아")
        self.assertEqual(role.team, "마피아팀")
        self.assertTrue(role.night_action)
        self.assertFalse(role.is_psycho)
    
    def test_mafia_role(self):
        """마피아 역할 클래스 테스트"""
        role = Mafia(1)
        self.assertEqual(role.player_id, 1)
        self.assertEqual(role.name, "마피아")
        self.assertEqual(role.team, "마피아팀")
        self.assertTrue(role.night_action)
        self.assertFalse(role.is_psycho)
    
    def test_citizen_role(self):
        """시민 역할 클래스 테스트"""
        role = Citizen(1)
        self.assertEqual(role.player_id, 1)
        self.assertEqual(role.name, "시민")
        self.assertEqual(role.team, "시민팀")
        self.assertFalse(role.night_action)
        self.assertFalse(role.is_psycho)
    
    def test_detective_role(self):
        """탐정 역할 클래스 테스트"""
        role = Detective(1)
        self.assertEqual(role.player_id, 1)
        self.assertEqual(role.name, "탐정")
        self.assertEqual(role.team, "시민팀")
        self.assertTrue(role.night_action)
        self.assertFalse(role.is_psycho)
    
    def test_doctor_role(self):
        """의사 역할 클래스 테스트"""
        role = Doctor(1)
        self.assertEqual(role.player_id, 1)
        self.assertEqual(role.name, "의사")
        self.assertEqual(role.team, "시민팀")
        self.assertTrue(role.night_action)
        self.assertFalse(role.is_psycho)
    
    def test_psycho_role(self):
        """정신병자 역할 테스트"""
        role = Citizen(1)
        role.set_psycho(True)
        self.assertTrue(role.is_psycho)


class TestPlayer(unittest.TestCase):
    """플레이어 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.player = Player(1, "테스트 플레이어", 1001)
    
    def test_player_init(self):
        """플레이어 초기화 테스트"""
        self.assertEqual(self.player.user_id, 1)
        self.assertEqual(self.player.name, "테스트 플레이어")
        self.assertEqual(self.player.chat_id, 1001)
        self.assertTrue(self.player.alive)
        self.assertIsNone(self.player.role)
    
    def test_assign_role(self):
        """역할 할당 테스트"""
        role = Mafia(1)
        self.player.assign_role(role)
        self.assertEqual(self.player.role, role)
    
    def test_kill_player(self):
        """플레이어 사망 테스트"""
        self.player.kill(2, {})
        self.assertFalse(self.player.alive)
    
    def test_protect_player(self):
        """플레이어 보호 테스트"""
        self.player.protect()
        self.assertTrue(self.player.protected)
        
        # 보호된 플레이어는 죽지 않음
        self.player.reset_status()  # 테스트를 위해 보호 상태 초기화
        self.player.protect()  # 다시 보호 상태로 설정
        self.player.kill(2, {})
        self.assertTrue(self.player.alive)  # 보호되었으므로 살아있어야 함
    
    def test_vote_for(self):
        """투표 테스트"""
        self.player.vote_for(2)
        self.assertEqual(self.player.voted_for, 2)
    
    def test_add_vote(self):
        """투표 추가 테스트"""
        weight = self.player.add_vote(2, {})
        self.assertEqual(weight, 1)
        self.assertEqual(self.player.vote_count, 1)
    
    def test_reset_vote(self):
        """투표 초기화 테스트"""
        self.player.vote_for(2)
        self.player.add_vote(2, {})
        self.player.reset_vote()
        self.assertIsNone(self.player.voted_for)
        self.assertEqual(self.player.vote_count, 0)
    
    def test_set_last_will(self):
        """유언 설정 테스트"""
        self.player.set_last_will("이것은 유언입니다.")
        self.assertEqual(self.player.last_will, "이것은 유언입니다.")


class TestRoleManager(unittest.TestCase):
    """역할 관리자 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.settings = {
            "role_counts": {
                "마피아": 1,
                "탐정": 1,
                "의사": 1,
                "시민": 2
            },
            "enabled_roles": {
                "마피아": True,
                "탐정": True,
                "의사": True,
                "시민": True
            },
            "sub_role_enabled": True
        }
        self.role_manager = RoleManager(self.settings)
    
    def test_assign_roles(self):
        """역할 할당 테스트"""
        player_ids = [1, 2, 3, 4, 5]
        assigned_roles = self.role_manager.assign_roles(player_ids)
        
        self.assertEqual(len(assigned_roles), 5)
        
        # 각 역할 수 확인
        role_counts = {}
        for player_id, role in assigned_roles.items():
            if role.name not in role_counts:
                role_counts[role.name] = 0
            role_counts[role.name] += 1
        
        self.assertEqual(role_counts.get("마피아", 0), 1)
        self.assertEqual(role_counts.get("탐정", 0), 1)
        self.assertEqual(role_counts.get("의사", 0), 1)
        
        # 모든 플레이어가 역할을 가지고 있는지 확인
        for player_id in player_ids:
            self.assertIn(player_id, assigned_roles)
    
    def test_get_team_players(self):
        """팀별 플레이어 가져오기 테스트"""
        player_ids = [1, 2, 3, 4, 5]
        assigned_roles = self.role_manager.assign_roles(player_ids)
        
        mafia_team = self.role_manager.get_team_players(assigned_roles, "마피아팀")
        citizen_team = self.role_manager.get_team_players(assigned_roles, "시민팀")
        
        self.assertEqual(len(mafia_team), 1)
        self.assertGreaterEqual(len(citizen_team), 4)


class TestPhaseManager(unittest.TestCase):
    """단계 관리자 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.settings = {
            "day_duration": 5,
            "night_duration": 3
        }
        self.phase_manager = PhaseManager(self.settings)
        self.phase_changes = []
        
        def on_phase_change(old_phase, new_phase):
            self.phase_changes.append((old_phase, new_phase))
        
        self.phase_manager.set_phase_change_callback(on_phase_change)
    
    def test_start_game(self):
        """게임 시작 테스트"""
        self.phase_manager.start_game()
        self.assertEqual(self.phase_manager.current_phase, "night")
        self.assertEqual(self.phase_manager.day_count, 1)
        self.assertEqual(len(self.phase_changes), 1)
        self.assertEqual(self.phase_changes[0], ("open", "night"))
    
    def test_change_phase(self):
        """단계 변경 테스트"""
        self.phase_manager.change_phase("day")
        self.assertEqual(self.phase_manager.current_phase, "day")
        self.assertEqual(len(self.phase_changes), 1)
        self.assertEqual(self.phase_changes[0], ("open", "day"))
        
        self.phase_manager.change_phase("night")
        self.assertEqual(self.phase_manager.current_phase, "night")
        self.assertEqual(len(self.phase_changes), 2)
        self.assertEqual(self.phase_changes[1], ("day", "night"))
    
    def test_end_game(self):
        """게임 종료 테스트"""
        self.phase_manager.end_game()
        self.assertEqual(self.phase_manager.current_phase, "end")
        self.assertEqual(len(self.phase_changes), 1)
        self.assertEqual(self.phase_changes[0], ("open", "end"))
    
    def test_record_night_action(self):
        """밤 행동 기록 테스트"""
        action_data = {"target_id": 2, "killer_id": 1}
        self.phase_manager.record_night_action("mafia_kill", action_data)
        
        night_actions = self.phase_manager.get_night_actions()
        self.assertIn("mafia_kill", night_actions)
        self.assertEqual(night_actions["mafia_kill"], action_data)
        
        self.phase_manager.clear_night_actions()
        self.assertEqual(self.phase_manager.get_night_actions(), {})


class TestGameManager(unittest.TestCase):
    """게임 관리자 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.settings = {
            "day_duration": 5,
            "night_duration": 3,
            "role_counts": {
                "마피아": 1,
                "탐정": 1,
                "의사": 1,
                "시민": 2
            },
            "enabled_roles": {
                "마피아": True,
                "탐정": True,
                "의사": True,
                "시민": True
            },
            "sub_role_enabled": True
        }
        self.game_manager = GameManager(self.settings, 1001)
        
        # 플레이어 추가
        self.game_manager.add_player(1, "플레이어1", 1001)
        self.game_manager.add_player(2, "플레이어2", 1002)
        self.game_manager.add_player(3, "플레이어3", 1003)
        self.game_manager.add_player(4, "플레이어4", 1004)
        self.game_manager.add_player(5, "플레이어5", 1005)
    
    def test_add_player(self):
        """플레이어 추가 테스트"""
        self.assertEqual(len(self.game_manager.players), 5)
        
        # 게임 시작 후에는 플레이어 추가 불가
        self.game_manager.game_started = True
        result = self.game_manager.add_player(6, "플레이어6", 1006)
        self.assertFalse(result)
        self.assertEqual(len(self.game_manager.players), 5)
    
    def test_remove_player(self):
        """플레이어 제거 테스트"""
        result = self.game_manager.remove_player(1)
        self.assertTrue(result)
        self.assertEqual(len(self.game_manager.players), 4)
        
        # 게임 시작 후에는 플레이어 제거 불가
        self.game_manager.game_started = True
        result = self.game_manager.remove_player(2)
        self.assertFalse(result)
        self.assertEqual(len(self.game_manager.players), 4)
    
    def test_start_game(self):
        """게임 시작 테스트"""
        success, message = self.game_manager.start_game()
        self.assertTrue(success)
        self.assertTrue(self.game_manager.game_started)
        
        # 모든 플레이어가 역할을 가지고 있는지 확인
        for player in self.game_manager.players.values():
            self.assertIsNotNone(player.role)
    
    def test_stop_game(self):
        """게임 중지 테스트"""
        self.game_manager.start_game()
        self.game_manager.stop_game()
        self.assertFalse(self.game_manager.game_started)
    
    def test_vote(self):
        """투표 테스트"""
        self.game_manager.start_game()
        self.game_manager.phase_manager.change_phase("day")
        
        # 투표 진행
        result = self.game_manager.vote(1, 2)
        self.assertTrue(result)
        self.assertEqual(self.game_manager.vote_results.get(2, 0), 1)
        
        # 같은 플레이어가 다른 대상에게 투표
        result = self.game_manager.vote(1, 3)
        self.assertTrue(result)
        self.assertEqual(self.game_manager.vote_results.get(2, 0), 0)
        self.assertEqual(self.game_manager.vote_results.get(3, 0), 1)
    
    def test_get_alive_players(self):
        """살아있는 플레이어 가져오기 테스트"""
        self.game_manager.start_game()
        alive_players = self.game_manager.get_alive_players()
        self.assertEqual(len(alive_players), 5)
        
        # 한 플레이어 사망
        self.game_manager.players[1].kill(2, self.game_manager.players)
        alive_players = self.game_manager.get_alive_players()
        self.assertEqual(len(alive_players), 4)
    
    def test_get_player_name(self):
        """플레이어 이름 가져오기 테스트"""
        name = self.game_manager.get_player_name(1)
        self.assertEqual(name, "플레이어1")
        
        name = self.game_manager.get_player_name(999)
        self.assertEqual(name, "알 수 없음")
    
    def test_get_game_status(self):
        """게임 상태 가져오기 테스트"""
        status = self.game_manager.get_game_status()
        self.assertFalse(status["game_started"])
        self.assertEqual(status["player_count"], 5)
        
        self.game_manager.start_game()
        status = self.game_manager.get_game_status()
        self.assertTrue(status["game_started"])
        self.assertEqual(status["alive_count"], 5)


if __name__ == "__main__":
    unittest.main()
