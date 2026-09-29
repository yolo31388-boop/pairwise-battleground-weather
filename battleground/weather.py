"""战场天气与地形系统"""
import random
from collections import deque


class WeatherSystem:
    # 主天气状态：晴/雨/雪/雾/风
    WEATHERS = ["sunny", "rain", "snow", "fog", "wind"]

    # 天气转换概率（持续时间到期后按概率切换）
    TRANSITION_PROBS = {
        "sunny": {"sunny": 0.45, "rain": 0.15, "snow": 0.05, "fog": 0.10, "wind": 0.25},
        "rain":  {"sunny": 0.30, "rain": 0.40, "snow": 0.10, "fog": 0.10, "wind": 0.10},
        "snow":  {"sunny": 0.20, "rain": 0.10, "snow": 0.40, "fog": 0.20, "wind": 0.10},
        "fog":   {"sunny": 0.40, "rain": 0.20, "snow": 0.10, "fog": 0.20, "wind": 0.10},
        "wind":  {"sunny": 0.40, "rain": 0.20, "snow": 0.10, "fog": 0.10, "wind": 0.20},
    }

    # 过渡阶段图（阴天→小雨→大雨→暴风雪 等），用于渐变转换
    _STAGE_GRAPH = {
        "sunny": ["cloudy", "wind"],
        "cloudy": ["sunny", "light_rain", "fog", "wind", "snow"],
        "wind": ["sunny", "cloudy"],
        "fog": ["cloudy"],
        "light_rain": ["cloudy", "rain"],
        "rain": ["light_rain", "heavy_rain"],
        "heavy_rain": ["rain", "storm"],
        "storm": ["heavy_rain", "snow"],
        "snow": ["cloudy", "storm"],
    }

    TERRAIN_TYPES = ["plain", "mountain", "forest", "swamp", "water", "ruins", "highland"]

    _MOVEMENT = {
        "plain": 1.0, "mountain": 0.7, "forest": 0.8, "swamp": 0.5,
        "water": 0.3, "ruins": 0.9, "highland": 0.85, "obstacle": 0.0,
    }

    _VISION = {"sunny": 1.0, "rain": 0.8, "snow": 0.7, "fog": 0.5, "wind": 0.9}

    # 地形 -> 属性 -> 修正系数
    _TERRAIN_STATS = {
        "highland": {"atk": 1.1, "def": 1.1},
        "mountain": {"def": 1.1},
        "forest": {"def": 1.1},
        "water": {"melee": 0.8, "atk": 0.9},
        "swamp": {"def": 0.9},
        "ruins": {"def": 1.05},
    }

    # 天气 -> 技能类型 -> 修正系数
    _WEATHER_SKILLS = {
        "sunny": {"fire": 1.1},
        "rain": {"fire": 0.7, "thunder": 1.2, "water": 1.1},
        "snow": {"move": 0.8, "ice": 1.2, "fire": 0.9},
        "wind": {"fire": 1.1, "ranged": 0.9},
        "fog": {},
    }

    _STRONGHOLD_BONUS = {
        "highland": {"atk": 1.1, "def": 1.1, "vision": 1.2},
        "mountain": {"def": 1.15},
        "ruins": {"def": 1.1},
    }

    _RANGED_ACCURACY = {"sunny": 1.0, "rain": 0.85, "snow": 0.8, "fog": 0.7, "wind": 0.9}

    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.current_weather: str = "sunny"
        self.weather_duration: float = 300.0
        self._last_update: float = None
        self.terrain_types: list = list(self.TERRAIN_TYPES)

    def update_weather(self, current_time: float) -> str:
        if self._last_update is None:
            self._last_update = current_time
            return self.current_weather
        if current_time < self._last_update:
            # 时间线回退（新的观测序列），重置计时
            self._last_update = current_time
        if current_time - self._last_update >= self.weather_duration:
            probs = self.TRANSITION_PROBS[self.current_weather]
            self.current_weather = self.rng.choices(
                list(probs.keys()), weights=list(probs.values())
            )[0]
            self._last_update = current_time
        return self.current_weather

    def get_movement_modifier(self, terrain: str) -> float:
        return self._MOVEMENT.get(terrain, 1.0)

    def get_vision_range(self, weather: str, base_vision: float) -> float:
        return base_vision * self._VISION.get(weather, 1.0)

    def get_terrain_stat_modifier(self, terrain: str, stat: str) -> float:
        return self._TERRAIN_STATS.get(terrain, {}).get(stat, 1.0)

    def get_weather_skill_modifier(self, weather: str, skill_type: str) -> float:
        return self._WEATHER_SKILLS.get(weather, {}).get(skill_type, 1.0)

    def get_stronghold_bonus(self, terrain: str) -> dict:
        return dict(self._STRONGHOLD_BONUS.get(terrain, {}))

    def get_weather_transition(self, from_w: str, to_w: str) -> list:
        if from_w == to_w:
            return [to_w]
        # BFS 求最短过渡路径，返回不含起点、含终点的阶段序列
        queue = deque([(from_w, [])])
        visited = {from_w}
        while queue:
            node, path = queue.popleft()
            for nxt in self._STAGE_GRAPH.get(node, []):
                if nxt in visited:
                    continue
                if nxt == to_w:
                    return path + [to_w]
                visited.add(nxt)
                queue.append((nxt, path + [nxt]))
        return [to_w]

    def get_all_terrain_types(self) -> list:
        return list(self.TERRAIN_TYPES)

    def get_ranged_accuracy_modifier(self, weather: str) -> float:
        return self._RANGED_ACCURACY.get(weather, 1.0)

    def get_melee_accuracy_modifier(self, weather: str) -> float:
        # 近战不受天气影响
        return 1.0
