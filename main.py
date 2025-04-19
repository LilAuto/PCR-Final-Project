# Grididdy Simulator with Balanced Danger Avoidance
import random
import time
import heapq

WIDTH, HEIGHT = 8, 8

UNKNOWN = "?"
SAFE = "."
WALL = "W"
SUSPECTED_DANGER = "D"
CONFIRMED_DANGER = "X"
GOAL = "G"
ROBOT = "R"

DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]

class Grididdy:
    def __init__(self):
        self.map = [[UNKNOWN for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.danger_belief = [[0.0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.wall_tiles = self.place_random_set(6)
        self.danger_tiles = self.place_random_set(6, self.wall_tiles)
        self.goal_pos = self.place_unique(self.wall_tiles.union(self.danger_tiles))
        self.robot_pos = self.place_unique(self.wall_tiles.union(self.danger_tiles, {self.goal_pos}))

    def place_unique(self, exclude=set()):
        while True:
            x, y = random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)
            if (x, y) not in exclude:
                return (x, y)

    def place_random_set(self, count, exclude=set()):
        placed = set()
        while len(placed) < count:
            x, y = random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)
            if (x, y) not in placed and (x, y) not in exclude:
                placed.add((x, y))
        return placed

    def camera_scan(self):
        x, y = self.robot_pos
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                if (nx, ny) in self.wall_tiles:
                    self.map[ny][nx] = WALL

    def magic_sensor(self):
        x, y = self.robot_pos
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if (nx, ny) in self.danger_tiles:
                return True
        return False

    def update_beliefs(self):
        x, y = self.robot_pos
        if self.magic_sensor():
            unknowns = []
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and self.map[ny][nx] == UNKNOWN:
                    unknowns.append((nx, ny))
            if len(unknowns) == 1:
                ux, uy = unknowns[0]
                self.map[uy][ux] = CONFIRMED_DANGER
                self.danger_belief[uy][ux] = 1.0
            else:
                for nx, ny in unknowns:
                    self.danger_belief[ny][nx] = min(self.danger_belief[ny][nx] + 0.3, 1.0)
                    self.map[ny][nx] = SUSPECTED_DANGER
        else:
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and self.map[ny][nx] == SUSPECTED_DANGER:
                    self.map[ny][nx] = SAFE
                    self.danger_belief[ny][nx] = 0.0

    def a_star_search(self, target):
        start = self.robot_pos
        queue = [(0, start)]
        came_from = {start: None}
        cost_so_far = {start: 0}
        details = {}

        while queue:
            _, current = heapq.heappop(queue)
            if current == target:
                break
            x, y = current
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                    tile_type = self.map[ny][nx]
                    if tile_type not in [WALL, CONFIRMED_DANGER]:
                        danger = self.danger_belief[ny][nx]
                        if danger >= 0.95:
                            continue
                        next_tile = (nx, ny)
                        cost = cost_so_far[current] + 1 + danger * 50
                        if next_tile not in cost_so_far or cost < cost_so_far[next_tile]:
                            cost_so_far[next_tile] = cost
                            priority = cost + self.distance_to_goal(next_tile)
                            heapq.heappush(queue, (priority, next_tile))
                            came_from[next_tile] = current
                            details[next_tile] = (danger, self.distance_to_goal(next_tile))

        path = []
        current = target
        while current != start:
            if current not in came_from:
                return [], None
            path.append(current)
            current = came_from[current]
        path.reverse()
        explanation = details.get(path[0], None) if path else None
        return path, explanation

    def move(self):
        path, reason = self.a_star_search(self.goal_pos)
        if not path:
            print("\n⚠️  No safe path found. Robot is stuck.")
            return False
        nx, ny = path[0]
        danger_score, dist_score = reason if reason else (0, 0)
        print(f"\n👉 Moving to ({nx},{ny}) - Danger: {danger_score:.2f}, Distance to Goal: {dist_score}")
        self.robot_pos = (nx, ny)
        self.map[ny][nx] = SAFE
        return True

    def distance_to_goal(self, pos):
        gx, gy = self.goal_pos
        x, y = pos
        return abs(gx - x) + abs(gy - y)

    def render(self):
        display = [[self.map[y][x] for x in range(WIDTH)] for y in range(HEIGHT)]
        rx, ry = self.robot_pos
        display[ry][rx] = ROBOT
        print("\n" + "=" * (2 * WIDTH))
        for row in display:
            print(" ".join(row))
        print("=" * (2 * WIDTH))

    def run(self):
        print("\n🤖 Starting Grididdy Simulation!")
        while self.robot_pos != self.goal_pos:
            self.camera_scan()
            self.update_beliefs()
            self.render()
            if not self.move():
                break
            time.sleep(0.4)
        if self.robot_pos == self.goal_pos:
            self.render()
            print("\n🎉 Robot reached the goal! You win.")

if __name__ == "__main__":
    game = Grididdy()
    game.run()
