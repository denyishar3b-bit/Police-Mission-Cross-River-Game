import os
import sys
import pygame

pygame.init()

try:
    pygame.mixer.init()
except pygame.error:
    print("Sound system could not start.")

# ============================================================
# POLICE MISSION: ROBBER RIVER CROSSING
# Python + Pygame OOP Puzzle Game
# ============================================================

WIDTH = 1000
HEIGHT = 650
FPS = 60
TIME_LIMIT = 120

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Police Catch Robber River Crossing")
clock = pygame.time.Clock()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "assets", "images")
SOUND_DIR = os.path.join(BASE_DIR, "assets", "sounds")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK = (20, 20, 35)
YELLOW = (255, 220, 80)
RED = (230, 70, 70)
GREEN = (80, 220, 120)
BLUE = (80, 200, 255)
ORANGE = (255, 160, 60)
PURPLE = (170, 100, 255)
GREY = (170, 170, 180)

FONT = pygame.font.SysFont("arial", 24)
SMALL = pygame.font.SysFont("arial", 18)
BIG = pygame.font.SysFont("arial", 46, bold=True)


def draw_text(text, font, colour, x, y, center=False):
    image = font.render(text, True, colour)
    rect = image.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(image, rect)


def load_image(filename, size):
    path = os.path.join(IMAGE_DIR, filename)

    if os.path.exists(path):
        try:
            image = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(image, size)
        except pygame.error:
            return None

    return None


def load_sound(filename):
    path = os.path.join(SOUND_DIR, filename)

    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except pygame.error:
            return None

    return None


def play_music():
    path = os.path.join(SOUND_DIR, "bgm.wav")

    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.25)
            pygame.mixer.music.play(-1)
        except pygame.error:
            print("Background music failed.")
    else:
        print("bgm.wav not found.")


def stop_music():
    try:
        pygame.mixer.music.stop()
    except pygame.error:
        pass


class Entity:
    def __init__(self, name, colour, left_pos, right_pos, image_file):
        self.name = name
        self.colour = colour
        self.left_pos = left_pos
        self.right_pos = right_pos
        self.side = "left"
        self.x, self.y = left_pos
        self.radius = 30
        self.selected = False
        self.image = load_image(image_file, (70, 70))

    def get_target_position(self, boat):
        if self.side == "left":
            return self.left_pos

        if self.side == "right":
            return self.right_pos

        if self.side == "boat":
            if self in boat.passengers:
                index = boat.passengers.index(self)
            else:
                index = 0

            if index == 0:
                return boat.x - 35, boat.y - 15
            else:
                return boat.x + 35, boat.y - 15

        return self.x, self.y

    def update(self, boat):
        target_x, target_y = self.get_target_position(boat)
        self.x += (target_x - self.x) * 0.18
        self.y += (target_y - self.y) * 0.18

    def draw(self):
        if self.image:
            rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.image, rect)
        else:
            pygame.draw.circle(screen, self.colour, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, 3)

        if self.selected:
            pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius + 8, 3)

        draw_text(self.name, SMALL, WHITE, self.x, self.y + 43, center=True)


class Boat:
    def __init__(self):
        self.side = "left"
        self.x = 300
        self.y = 410
        self.target_x = 300
        self.passengers = []
        self.moving = False
        self.image = load_image("boat.png", (170, 90))

    def can_add(self, entity):
        if self.moving:
            return False

        if entity.side != self.side:
            return False

        if len(self.passengers) >= 2:
            return False

        return True

    def toggle_passenger(self, entity):
        if self.moving:
            return False

        if entity in self.passengers:
            self.passengers.remove(entity)
            entity.side = self.side
            return True

        if self.can_add(entity):
            self.passengers.append(entity)
            entity.side = "boat"
            return True

        return False

    def has_police(self):
        return any(entity.name == "Police" for entity in self.passengers)

    def start_move(self):
        if self.moving:
            return False

        if not self.has_police():
            return False

        if self.side == "left":
            self.side = "right"
            self.target_x = 700
        else:
            self.side = "left"
            self.target_x = 300

        self.moving = True
        return True

    def update(self):
        if not self.moving:
            return False

        speed = 6

        if abs(self.x - self.target_x) <= speed:
            self.x = self.target_x
            self.moving = False
            return True

        if self.x < self.target_x:
            self.x += speed
        else:
            self.x -= speed

        return False

    def unload_all(self):
        for passenger in self.passengers:
            passenger.side = self.side

        self.passengers.clear()

    def draw(self):
        if self.image:
            rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.image, rect)
        else:
            rect = pygame.Rect(self.x - 85, self.y - 35, 170, 70)
            pygame.draw.ellipse(screen, ORANGE, rect)
            pygame.draw.ellipse(screen, WHITE, rect, 3)
            draw_text("BOAT", SMALL, BLACK, self.x, self.y, center=True)


class GameManager:
    def __init__(self):
        self.state = "menu"
        self.boat = Boat()
        self.entities = self.create_entities()

        self.start_time = pygame.time.get_ticks()
        self.remaining_time = TIME_LIMIT
        self.message = ""
        self.score = 0
        self.pause_start = 0

        self.instruction_scroll = 0
        self.max_instruction_scroll = -570

        self.lobby_background = load_image("lobby_background.png", (WIDTH, HEIGHT))
        self.game_background = load_image("background.png", (WIDTH, HEIGHT))

        self.move_sound = load_sound("move.wav")
        self.win_sound = load_sound("win.wav")
        self.lose_sound = load_sound("lose.wav")

    def create_entities(self):
        return [
            Entity("Police", BLUE, (140, 190), (860, 190), "police.png"),
            Entity("Robber", RED, (140, 300), (860, 300), "robber.png"),
            Entity("Witness", GREY, (140, 410), (860, 410), "witness.png"),
            Entity("Money", GREEN, (140, 520), (860, 520), "money.png"),
        ]

    def start_game(self):
        self.state = "playing"
        self.boat = Boat()
        self.entities = self.create_entities()
        self.start_time = pygame.time.get_ticks()
        self.remaining_time = TIME_LIMIT
        self.message = ""
        self.score = 0
        play_music()

    def pause_game(self):
        if self.state == "playing":
            self.state = "paused"
            self.pause_start = pygame.time.get_ticks()

            try:
                pygame.mixer.music.pause()
            except pygame.error:
                pass

        elif self.state == "paused":
            pause_duration = pygame.time.get_ticks() - self.pause_start
            self.start_time += pause_duration
            self.state = "playing"

            try:
                pygame.mixer.music.unpause()
            except pygame.error:
                pass

    def scroll_instructions(self, amount):
        self.instruction_scroll += amount

        if self.instruction_scroll > 0:
            self.instruction_scroll = 0

        if self.instruction_scroll < self.max_instruction_scroll:
            self.instruction_scroll = self.max_instruction_scroll

    def get_side_names(self, side):
        return [entity.name for entity in self.entities if entity.side == side]

    def select_entity(self, index):
        if self.state != "playing":
            return

        entity = self.entities[index]
        success = self.boat.toggle_passenger(entity)

        for item in self.entities:
            item.selected = False

        if success:
            entity.selected = True
            self.message = ""
        else:
            self.message = "Cannot select. Same side only. Boat max is 2."

    def move_boat(self):
        if self.state != "playing":
            return

        if self.boat.start_move():
            self.message = ""

            if self.move_sound:
                self.move_sound.play()
        else:
            self.message = "Police must be on the boat to move."

    def update_timer(self):
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        self.remaining_time = TIME_LIMIT - elapsed

        if self.remaining_time <= 0:
            self.remaining_time = 0
            self.lose("Time is over! Mission failed.")

    def check_rules(self):
        for side in ["left", "right"]:
            names = self.get_side_names(side)

            if "Police" not in names:
                if "Robber" in names and "Witness" in names:
                    self.lose("Robber threatened the Witness! Mission failed.")
                    return

                if "Robber" in names and "Money" in names:
                    self.lose("Robber stole the Money! Mission failed.")
                    return

    def check_win(self):
        if all(entity.side == "right" for entity in self.entities):
            self.score = self.remaining_time * 10
            self.state = "win"
            stop_music()

            if self.win_sound:
                self.win_sound.play()

    def lose(self, message):
        self.state = "lose"
        self.message = message
        stop_music()

        if self.lose_sound:
            self.lose_sound.play()

    def update(self):
        if self.state != "playing":
            return

        self.update_timer()
        arrived = self.boat.update()

        if arrived:
            self.boat.unload_all()
            self.check_rules()
            self.check_win()

        for entity in self.entities:
            entity.update(self.boat)    

    def draw_lobby_background(self):
        if self.lobby_background:
            screen.blit(self.lobby_background, (0, 0))
        else:
            screen.fill((18, 24, 50))

    def draw_game_background(self):
        if self.game_background:
            screen.blit(self.game_background, (0, 0))
        else:
            screen.fill((18, 24, 50))
            pygame.draw.rect(screen, (55, 90, 95), (0, 80, 300, HEIGHT - 80))
            pygame.draw.rect(screen, (65, 125, 85), (700, 80, 300, HEIGHT - 80))
            pygame.draw.rect(screen, (35, 110, 190), (300, 80, 400, HEIGHT - 80))

        draw_text("BASE", FONT, WHITE, 150, 105, center=True)
        draw_text("RIVER", FONT, WHITE, 500, 105, center=True)
        draw_text("SAFE ZONE", FONT, WHITE, 850, 105, center=True)

    def draw_hud(self):
        pygame.draw.rect(screen, DARK, (0, 0, WIDTH, 80))
        pygame.draw.line(screen, WHITE, (0, 80), (WIDTH, 80), 2)

        timer_colour = GREEN if self.remaining_time > 30 else RED

        draw_text(f"Time: {self.remaining_time}s", FONT, timer_colour, 20, 20)
        draw_text("1 Police | 2 Robber | 3 Witness | 4 Money", SMALL, WHITE, 260, 18)
        draw_text("SPACE Move | P Pause | R Restart | ESC Quit", SMALL, WHITE, 260, 45)

    def draw_rules(self):
        pygame.draw.rect(screen, DARK, (20, 570, 960, 60))
        pygame.draw.rect(screen, WHITE, (20, 570, 960, 60), 2)

        draw_text(
            "Rule: Boat carries max 2 passengers. Police must be on boat to move.",
            SMALL,
            WHITE,
            35,
            582
        )

        draw_text(
            "Lose: Robber + Witness without Police OR Witness + Money without Police.",
            SMALL,
            YELLOW,
            35,
            605
        )

    def draw_game(self):
        self.draw_game_background()
        self.draw_hud()
        self.boat.draw()

        for entity in self.entities:
            entity.draw()

        self.draw_rules()

        if self.message:
            draw_text(self.message, SMALL, RED, WIDTH // 2, 90, center=True)

    def draw_menu(self):
        self.draw_lobby_background()

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(100)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        draw_text("POLICE MISSION", BIG, BLUE, WIDTH // 2, 155, center=True)
        draw_text("Catch the robber", BIG, YELLOW, WIDTH // 2, 215, center=True)
        draw_text("Press ENTER to Start", FONT, WHITE, WIDTH // 2, 330, center=True)
        draw_text("Press I for Instructions", FONT, WHITE, WIDTH // 2, 375, center=True)
        draw_text("Press ESC to Quit", FONT, WHITE, WIDTH // 2, 420, center=True)
        draw_text("Background music starts after ENTER", SMALL, WHITE, WIDTH // 2, 510, center=True)

    def draw_instructions(self):
        self.draw_lobby_background()

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(165)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        draw_text("INSTRUCTIONS", BIG, YELLOW, WIDTH // 2, 70, center=True)
        draw_text("UP/DOWN or Mouse Wheel = Scroll | BACKSPACE = Menu", SMALL, WHITE, WIDTH // 2, 115, center=True)

        instruction_area = pygame.Rect(120, 145, 760, 420)
        pygame.draw.rect(screen, (15, 15, 30), instruction_area, border_radius=15)
        pygame.draw.rect(screen, WHITE, instruction_area, 2, border_radius=15)

        previous_clip = screen.get_clip()
        screen.set_clip(instruction_area)

        lines = [
            "Mission:",
            "Move all entities from LEFT BASE to SAFE ZONE before the timer ends.",
            "",
            "Controls:",
            "1 = Select Police",
            "2 = Select Robber",
            "3 = Select Witness",
            "4 = Select Money",
            "SPACE = Move boat",
            "P = Pause game",
            "R = Restart game",
            "ESC = Quit game",
            "BACKSPACE = Return to menu from this page",
            "",
            "Game Rules:",
            "- The boat can carry maximum 2 passengers only.",
            "- The Police must be on the boat to move.",
            "- Robber cannot be left with Witness without Police.",
            "- Witness cannot be left with Money without Police.",
            "- If any rule is broken, the mission fails.",
            "",
            "Win Condition:",
            "- Move Police, Robber, Witness and Money to the SAFE ZONE.",
            "- You must complete the mission before the timer becomes zero.",
            "",
            "Lose Condition:",
            "- Timer reaches zero.",
            "- Robber is left with Witness without Police.",
            "- Witness is left with Money without Police.",
            "",
            "Tips:",
            "- Always bring the Police when moving the boat.",
            "- Think carefully before leaving two entities alone.",
            "- Use restart if your move is wrong.",
            "",
            "Technical Details:",
            "This game uses classes and objects for Entity, Boat and GameManager.",
            "It also uses event handling, timer logic, animation and rule validation."
        ]

        y = 165 + self.instruction_scroll

        for line in lines:
            headings = [
                "Mission:",
                "Controls:",
                "Game Rules:",
                "Win Condition:",
                "Lose Condition:",
                "Tips:",
                "Technical Details:"
            ]

            colour = YELLOW if line in headings else WHITE
            draw_text(line, SMALL, colour, 145, y)
            y += 30

        screen.set_clip(previous_clip)

        pygame.draw.rect(screen, WHITE, (895, 145, 8, 420), 1)

        scrollbar_y = 145 + min(360, max(0, int(-self.instruction_scroll * 0.63)))
        pygame.draw.rect(screen, YELLOW, (895, scrollbar_y, 8, 60))

    def draw_overlay(self, title, colour, subtitle):
        self.draw_game()

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        draw_text(title, BIG, colour, WIDTH // 2, HEIGHT // 2 - 80, center=True)
        draw_text(subtitle, FONT, WHITE, WIDTH // 2, HEIGHT // 2 - 10, center=True)
        draw_text("Press R to Restart or ESC to Quit", FONT, WHITE, WIDTH // 2, HEIGHT // 2 + 50, center=True)

    def draw(self):
        if self.state == "menu":
            self.draw_menu()

        elif self.state == "instructions":
            self.draw_instructions()

        elif self.state == "playing":
            self.draw_game()

        elif self.state == "paused":
            self.draw_overlay("PAUSED", YELLOW, "Press P to continue")

        elif self.state == "win":
            self.draw_overlay("MISSION SUCCESS!", GREEN, f"Score: {self.score}")

        elif self.state == "lose":
            self.draw_overlay("MISSION FAILED", RED, self.message)


def main():
    game = GameManager()
    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEWHEEL and game.state == "instructions":
                game.scroll_instructions(event.y * 30)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if game.state == "menu":
                    if event.key == pygame.K_RETURN:
                        game.start_game()

                    elif event.key == pygame.K_i:
                        game.state = "instructions"
                        game.instruction_scroll = 0

                elif game.state == "instructions":
                    if event.key == pygame.K_BACKSPACE:
                        game.state = "menu"

                    elif event.key == pygame.K_DOWN:
                        game.scroll_instructions(-30)

                    elif event.key == pygame.K_UP:
                        game.scroll_instructions(30)

                elif game.state == "playing":
                    if event.key == pygame.K_1:
                        game.select_entity(0)

                    elif event.key == pygame.K_2:
                        game.select_entity(1)

                    elif event.key == pygame.K_3:
                        game.select_entity(2)

                    elif event.key == pygame.K_4:
                        game.select_entity(3)

                    elif event.key == pygame.K_SPACE:
                        game.move_boat()

                    elif event.key == pygame.K_p:
                        game.pause_game()

                    elif event.key == pygame.K_r:
                        game.start_game()

                elif game.state == "paused":
                    if event.key == pygame.K_p:
                        game.pause_game()

                    elif event.key == pygame.K_r:
                        game.start_game()

                elif game.state in ["win", "lose"]:
                    if event.key == pygame.K_r:
                        game.start_game()

        game.update()
        game.draw()
        pygame.display.flip()

    stop_music()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()