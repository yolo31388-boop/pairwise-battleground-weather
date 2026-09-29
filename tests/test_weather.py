"""战场天气与地形系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from battleground.weather import WeatherSystem

class TestWeatherChange:
    def test_weather_changes_over_time(self):
        ws = WeatherSystem(seed=42)
        w1 = ws.update_weather(0)
        w2 = ws.update_weather(10000)
        # 应该有概率变化
        assert hasattr(ws, "weather_duration")
        ws.weather_duration = 100
        results = set()
        for t in range(0, 10000, 100):
            results.add(ws.update_weather(t))
        assert len(results) > 1

class TestMovementModifier:
    def test_mountain_slows_movement(self):
        ws = WeatherSystem()
        m1 = ws.get_movement_modifier("plain")
        m2 = ws.get_movement_modifier("mountain")
        assert m2 < m1

class TestVisionRange:
    def test_fog_reduces_vision(self):
        ws = WeatherSystem()
        v1 = ws.get_vision_range("sunny", 100)
        v2 = ws.get_vision_range("fog", 100)
        assert v2 < v1

class TestTerrainStatModifier:
    def test_highland_boosts_attack(self):
        ws = WeatherSystem()
        m1 = ws.get_terrain_stat_modifier("plain", "atk")
        m2 = ws.get_terrain_stat_modifier("highland", "atk")
        assert m2 > m1

class TestWeatherSkillLink:
    def test_rain_reduces_fire_damage(self):
        ws = WeatherSystem()
        m1 = ws.get_weather_skill_modifier("sunny", "fire")
        m2 = ws.get_weather_skill_modifier("rain", "fire")
        assert m2 < m1

class TestStrongholdBonus:
    def test_occupying_highland_gives_bonus(self):
        ws = WeatherSystem()
        bonus = ws.get_stronghold_bonus("highland")
        assert bonus != {}

class TestWeatherTransition:
    def test_sunny_to_storm_has_transition(self):
        ws = WeatherSystem()
        transition = ws.get_weather_transition("sunny", "storm")
        assert len(transition) > 1

class TestTerrainTypes:
    def test_more_than_two_terrain_types(self):
        ws = WeatherSystem()
        types = ws.get_all_terrain_types()
        assert len(types) > 2

class TestRangedAccuracy:
    def test_fog_reduces_ranged_accuracy(self):
        ws = WeatherSystem()
        m1 = ws.get_ranged_accuracy_modifier("sunny")
        m2 = ws.get_ranged_accuracy_modifier("fog")
        assert m2 < m1
