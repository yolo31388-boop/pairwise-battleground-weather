"""战场天气与地形系统"""
import random
from collections import deque


class WeatherSystem:
    # 天气类型: 晴/阴/雨(小/大)/雪/雾/风/暴风雪
    WEATHER_TYPES = [
        "sunny", "cloudy", "light_rain", "rain", "heavy_rain",
        "snow", "fog", "wind", "storm",
    ]

    # 地形类型: 平原/山地/森林/沼泽/水域/废墟/高地/障碍
    TERRAIN_TYPES = [
        "plain", "mountain", "forest", "swamp",
        "water", "ruins", "highland", "obstacle",
    ]

    # 天气转换图(过渡阶段): 晴天不会瞬间变暴风雪
    TRANSITION_GRAPH = {
        "sunny": ["cloudy", "wind", "fog"],
        "cloudy": ["sunny", "light_rain", "wind", "fog"],
        "light_rain": ["cloudy", "rain"],
        "rain": ["light_rain", "heavy_rain", "cloudy"],
        "heavy_rain": ["rain", "storm"],
        "storm": ["heavy_rain", "snow"],
        "snow": ["cloudy", "storm", "fog"],
        "fog": ["sunny", "cloudy", "snow"],
        "wind": ["sunny", "cloudy", "storm"],
    }

    # 地形移动修正: 山地-30%、沼泽-50%、水域需游泳
    MOVEMENT_MODIFIERS = {
        "plain": 1.0,
        "mountain": 0.7,
        "forest": 0.8,
        "swamp": 0.5,
        "water": 0.3,      # 游泳
        "ruins": 0.9,
        "highland": 0.85,
        "obstacle": 0.0,   # 不可通行
    }

    # 天气视野修正: 雾天-50%
    VISION_MODIFIERS = {
        "sunny": 1.0,
        "cloudy": 0.9,
        "light_rain": 0.85,
        "rain": 0.8,
        "heavy_rain": 0.7,
        "snow": 0.7,
        "fog": 0.5,
        "wind": 0.9,
        "storm": 0.6,
    }

    # 地形属性修正: 高地+10%攻击、水域-20%近战
    TERRAIN_STAT_MODIFIERS = {
        "highland": {"atk": 1.1, "ranged": 1.1, "def": 1.05},
        "water": {"melee": 0.8, "def": 0.9},
        "forest": {"def": 1.1, "ranged": 0.9},
        "swamp": {"def": 0.9, "melee": 0.9},
        "ruins": {"def": 1.1},
        "mountain": {"def": 1.05},
    }

    # 天气-技能联动: 雨天火系-30%、雷系+20%; 雪天移动-20%
    WEATHER_SKILL_MODIFIERS = {
        "rain": {"fire": 0.7, "thunder": 1.2},
        "light_rain": {"fire": 0.85, "thunder": 1.1},
        "heavy_rain": {"fire": 0.6, "thunder": 1.3},
        "storm": {"fire": 0.5, "thunder": 1.4, "movement": 0.8},
        "snow": {"movement": 0.8, "fire": 0.9, "ice": 1.2},
        "fog": {"ranged": 0.7},
        "wind": {"ranged": 0.9, "fire": 1.1},
        "sunny": {"fire": 1.1},
    }

    # 占领加成: 高地/据点有攻防加成
    STRONGHOLD_BONUSES = {
        "highland": {"atk": 1.1, "def": 1.1, "vision": 1.2},
        "ruins": {"def": 1.15},
        "mountain": {"def": 1.1, "vision": 1.1},
        "forest": {"def": 1.05, "stealth": 1.2},
    }

    # 天气对远程命中修正: 雾天远程-30%, 近战不受影响
    RANGED_ACCURACY_MODIFIERS = {
        "sunny": 1.0,
        "cloudy": 0.95,
        "light_rain": 0.9,
        "rain": 0.85,
        "heavy_rain": 0.75,
        "snow": 0.8,
        "fog": 0.7,
        "wind": 0.85,
        "storm": 0.6,
    }

    # 天气转换概率(每次持续时间到期时)
    CHANGE_PROBABILITY = 0.4

    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.current_weather: str = "sunny"
        self.terrain_types: list = list(self.TERRAIN_TYPES)
        self.weather_duration: float = 300.0
        self._last_update_time: float = 0.0

    def update_weather(self, current_time: float) -> str:
        """按时间推进天气: 持续时间到期后按概率转换到相邻天气(有过渡)。"""
        if current_time < self._last_update_time:
            self._last_update_time = current_time
        if current_time - self._last_update_time >= self.weather_duration:
            self._last_update_time = current_time
            if self.rng.random() < self.CHANGE_PROBABILITY:
                neighbors = self.TRANSITION_GRAPH.get(self.current_weather, [])
                if neighbors:
                    self.current_weather = self.rng.choice(neighbors)
        return self.current_weather

    def get_movement_modifier(self, terrain: str) -> float:
        return self.MOVEMENT_MODIFIERS.get(terrain, 1.0)

    def get_vision_range(self, weather: str, base_vision: float) -> float:
        return base_vision * self.VISION_MODIFIERS.get(weather, 1.0)

    def get_terrain_stat_modifier(self, terrain: str, stat: str) -> float:
        return self.TERRAIN_STAT_MODIFIERS.get(terrain, {}).get(stat, 1.0)

    def get_weather_skill_modifier(self, weather: str, skill_type: str) -> float:
        return self.WEATHER_SKILL_MODIFIERS.get(weather, {}).get(skill_type, 1.0)

    def get_stronghold_bonus(self, terrain: str) -> dict:
        return dict(self.STRONGHOLD_BONUSES.get(terrain, {}))

    def get_weather_transition(self, from_w: str, to_w: str) -> list:
        """返回从 from_w 到 to_w 的过渡阶段序列(含终点), BFS 最短路径。"""
        if from_w == to_w:
            return [to_w]
        queue = deque([(from_w, [from_w])])
        visited = {from_w}
        while queue:
            node, path = queue.popleft()
            for nxt in self.TRANSITION_GRAPH.get(node, []):
                if nxt in visited:
                    continue
                new_path = path + [nxt]
                if nxt == to_w:
                    return new_path[1:]
                visited.add(nxt)
                queue.append((nxt, new_path))
        return [to_w]

    def get_all_terrain_types(self) -> list:
        return list(self.TERRAIN_TYPES)

    def get_ranged_accuracy_modifier(self, weather: str) -> float:
        return self.RANGED_ACCURACY_MODIFIERS.get(weather, 1.0)
