# Grididdy Simulator with Prioritized Backtracking
import random
import time
import heapq
from collections import deque

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
        self.steps_taken = 0
        self.explored_tiles = set()
        self.dangerous_moves = 0
        self.previous_pos = None
        self.map = [[UNKNOWN for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.danger_belief = [[0.0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.wall_tiles = self.place_random_set(6)
        self.danger_tiles = self.place_random_set(6, self.wall_tiles)
        self.goal_pos = self.place_unique(self.wall_tiles.union(self.danger_tiles))
        self.robot_pos = self.place_unique(self.wall_tiles.union(self.danger_tiles, {self.goal_pos}))
        self.visit_count = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]

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

    def bfs_all_frontiers(self):
        start = self.robot_pos
        visited = set()
        queue = deque([(start, [])])
        paths_to_unknown = []
        paths_safe = []
        paths_risky = []

        while queue:
            (x, y), path = queue.popleft()
            if (x, y) in visited:
                continue
            visited.add((x, y))

            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                    if self.map[ny][nx] in [WALL, CONFIRMED_DANGER] or (nx, ny) in visited:
                        continue
                    new_path = path + [(nx, ny)]

                    leads_to_unknown = False
                    for px, py in new_path:
                        for dx2, dy2 in DIRS:
                            ax, ay = px + dx2, py + dy2
                            if 0 <= ax < WIDTH and 0 <= ay < HEIGHT and self.map[ay][ax] == UNKNOWN:
                                leads_to_unknown = True
                                break
                        if leads_to_unknown:
                            break

                    danger_penalty = self.danger_belief[ny][nx]
                    revisit_penalty = self.visit_count[ny][nx] * 1.0
                    cost = danger_penalty + revisit_penalty

                    if leads_to_unknown:
                        paths_to_unknown.append((cost + sum(self.visit_count[py][px] for px, py in new_path), new_path))
                    elif danger_penalty == 0.0:
                        paths_safe.append((cost + sum(self.visit_count[py][px] for px, py in new_path), new_path))
                    else:
                        paths_risky.append((cost + sum(self.visit_count[py][px] for px, py in new_path), new_path))

                    queue.append(((nx, ny), new_path))

        if paths_to_unknown:
            paths_to_unknown.sort(key=lambda item: (item[0], len(item[1])))
            return paths_to_unknown[0][1], (paths_to_unknown[0][0], len(paths_to_unknown[0][1]))
        elif paths_safe:
            paths_safe.sort(key=lambda item: (item[0], len(item[1])))
            return paths_safe[0][1], (paths_safe[0][0], len(paths_safe[0][1]))
        elif paths_risky:
            paths_risky.sort(key=lambda item: (item[0], len(item[1])))
            return paths_risky[0][1], (paths_risky[0][0], len(paths_risky[0][1]))
        return [], None

    def move(self):
        path, reason = self.bfs_all_frontiers()
        if not path:
            print("\n💥 Robot is completely trapped.")
            return False
        nx, ny = path[0]
        print(f"\n👉 Moving to ({nx},{ny}) - Danger: {self.danger_belief[ny][nx]:.2f}, Distance to Goal: {abs(nx - self.goal_pos[0]) + abs(ny - self.goal_pos[1])}")
        self.previous_pos = self.robot_pos
        self.robot_pos = (nx, ny)
        if (nx, ny) == self.goal_pos:
            self.map[ny][nx] = GOAL
        else:
            self.map[ny][nx] = SAFE
        self.visit_count[ny][nx] += 1
        self.steps_taken += 1
        self.explored_tiles.add((nx, ny))
        if self.danger_belief[ny][nx] >= 0.3:
            self.dangerous_moves += 1
        return True

    def render(self):
        display = [[self.map[y][x] for x in range(WIDTH)] for y in range(HEIGHT)]
        rx, ry = self.robot_pos
        display[ry][rx] = ROBOT
        print("\n" + "=" * (2 * WIDTH))
        for row in display:
            print(" ".join(row))
        print("=" * (2 * WIDTH))

    def run(self):
        print("\n📌 Legend: R=Robot, X=Confirmed Danger, D=Suspected Danger, .=Safe, ?=Unknown, W=Wall, G=Goal")
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
        print(f"\n🧠 STATS:\n- Steps Taken: {self.steps_taken}\n- Tiles Explored: {len(self.explored_tiles)}\n- Dangerous Moves: {self.dangerous_moves}")

if __name__ == "__main__":
    game = Grididdy()
    game.run()