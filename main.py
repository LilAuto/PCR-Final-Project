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

        while True:
            self.wall_tiles = self.place_random_set(6)
            self.danger_tiles = self.place_random_set(6, self.wall_tiles)
            self.goal_pos = self.place_unique(self.wall_tiles.union(self.danger_tiles))
            self.robot_pos = self.place_unique(self.wall_tiles.union(self.danger_tiles, {self.goal_pos}))
            if not self.is_surrounded(self.robot_pos):
                break

        self.visit_count = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.frontier_memory = set()
        self.map[self.robot_pos[1]][self.robot_pos[0]] = SAFE

        if self.is_surrounded(self.robot_pos):
            self.force_move_out_of_surrounding()

    def is_surrounded(self, pos):
        x, y = pos
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                if (nx, ny) not in self.wall_tiles and (nx, ny) not in self.danger_tiles:
                    return False
        return True

    def force_move_out_of_surrounding(self):
        x, y = self.robot_pos
        valid_dangers = []
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and (nx, ny) in self.danger_tiles:
                valid_dangers.append((nx, ny))
        if valid_dangers:
            choice = random.choice(valid_dangers)
            self.robot_pos = choice
            self.map[choice[1]][choice[0]] = SAFE
            self.steps_taken += 1
            self.dangerous_moves += 1
            self.explored_tiles.add(choice)
            self.visit_count[choice[1]][choice[0]] += 1

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

    def update_frontier_memory(self):
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if self.map[y][x] == SAFE:
                    for dx, dy in DIRS:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and self.map[ny][nx] == UNKNOWN:
                            self.frontier_memory.add((x, y))

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
        best_path = None
        best_cost = float('inf')

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
                    if self.map[ny][nx] == UNKNOWN:
                        return new_path, None
                    queue.append(((nx, ny), new_path))

        return [], None

    def move(self):
        self.update_frontier_memory()
        path, _ = self.bfs_all_frontiers()
        if not path:
            print("\n\U0001F4A5 Robot is completely trapped.")
            return False
        nx, ny = path[0]
        print(f"\n\U0001F449 Moving to ({nx},{ny}) - Danger: {self.danger_belief[ny][nx]:.2f}, Distance to Goal: {abs(nx - self.goal_pos[0]) + abs(ny - self.goal_pos[1])}")
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
        print("\n\U0001F4CC Legend: R=Robot, X=Confirmed Danger, D=Suspected Danger, .=Safe, ?=Unknown, W=Wall")
        print("\n\U0001F916 Starting Grididdy Simulation!")
        while self.robot_pos != self.goal_pos:
            self.camera_scan()
            self.update_beliefs()
            self.render()
            if not self.move():
                break
            time.sleep(0.4)
        if self.robot_pos == self.goal_pos:
            self.render()
            print("\n\U0001F389 Robot reached the goal! You win.")
        print(f"\n\U0001F9E0 STATS:\n- Steps Taken: {self.steps_taken}\n- Tiles Explored: {len(self.explored_tiles)}\n- Dangerous Moves: {self.dangerous_moves}")

if __name__ == "__main__":
    game = Grididdy()
    game.run()
