import time

from pico2d import (
    SDL_KEYDOWN,
    SDL_KEYUP,
    SDLK_LEFT,
    SDLK_RIGHT,
    SDLK_SPACE,
    SDLK_a,
    load_image,
)
from transitions import Machine


class Boy:
    IDLE = 'IDLE'
    SLEEP = 'SLEEP'
    RUN = 'RUN'
    AUTO_RUN = 'AUTO_RUN'
    IDLE_DURATION = 5.0
    AUTO_RUN_DURATION = 5.0
    RUN_SPEED = 5
    AUTO_RUN_SPEED = 8
    AUTO_RUN_FRAME_COUNT = 8
    SCREEN_WIDTH = 800
    SPRITE_WIDTH = 100
    AUTO_RUN_SPRITE_WIDTH = 200
    NORMAL_Y = 90
    GROUND_TOP = 61
    AUTO_RUN_GROUND_OFFSET = AUTO_RUN_SPRITE_WIDTH // 2
    AUTO_RUN_Y = GROUND_TOP + AUTO_RUN_GROUND_OFFSET

    def __init__(self):
        self.x, self.y = 400, self.NORMAL_Y
        self.frame = 0
        self.face_dir = 1
        self.image = load_image('animation_sheet.png')
        self.run_image = load_image('run_animation.png')
        self.machine = Machine(
            model=self,
            states=[
                {'name': self.IDLE, 'on_enter': 'reset_idle_timer'},
                self.SLEEP,
                self.RUN,
                {
                    'name': self.AUTO_RUN,
                    'on_enter': 'reset_auto_run_timer',
                    'on_exit': 'reset_normal_y'
                }
            ],
            initial=self.IDLE,
            transitions=[
                {'trigger': 'sleep', 'source': self.IDLE, 'dest': self.SLEEP},
                {'trigger': 'wake_up', 'source': self.SLEEP, 'dest': self.IDLE},
                {'trigger': 'start_run', 'source': self.IDLE, 'dest': self.RUN},
                {'trigger': 'start_auto_run', 'source': self.IDLE, 'dest': self.AUTO_RUN},
                {'trigger': 'start_run_from_auto', 'source': self.AUTO_RUN, 'dest': self.RUN},
                {'trigger': 'start_run_from_sleep', 'source': self.SLEEP, 'dest': self.RUN},
                {'trigger': 'stop_run', 'source': self.RUN, 'dest': self.IDLE},
                {'trigger': 'stop_auto_run', 'source': self.AUTO_RUN, 'dest': self.IDLE}
            ],
            auto_transitions=False
        )
        self.pressed_directions = set()
        self.reset_idle_timer()

    def reset_idle_timer(self):
        self.idle_started_at = time.monotonic()

    def reset_auto_run_timer(self):
        self.auto_run_started_at = time.monotonic()
        self.y = self.AUTO_RUN_Y

    def reset_normal_y(self):
        self.y = self.NORMAL_Y

    def clamp_x(self, x, sprite_width):
        half_width = sprite_width // 2
        return max(
            half_width,
            min(self.SCREEN_WIDTH - half_width, x)
        )

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if self.state == self.SLEEP and event.key == SDLK_SPACE:
                self.wake_up()
            elif self.state == self.IDLE and event.key == SDLK_a:
                self.start_auto_run()
            elif event.key in (SDLK_LEFT, SDLK_RIGHT):
                self.pressed_directions.add(event.key)
                self.face_dir = -1 if event.key == SDLK_LEFT else 1
                if self.state == self.IDLE:
                    self.start_run()
                elif self.state == self.AUTO_RUN:
                    self.start_run_from_auto()
                elif self.state == self.SLEEP:
                    self.start_run_from_sleep()
        elif event.type == SDL_KEYUP and event.key in (SDLK_LEFT, SDLK_RIGHT):
            self.pressed_directions.discard(event.key)
            if self.state == self.RUN:
                if self.pressed_directions:
                    direction = next(iter(self.pressed_directions))
                    self.face_dir = -1 if direction == SDLK_LEFT else 1
                else:
                    self.stop_run()

    def update(self):
        if self.state == self.IDLE:
            self.frame = (self.frame + 1) % 8
            if time.monotonic() - self.idle_started_at >= self.IDLE_DURATION:
                self.sleep()
        elif self.state == self.RUN:
            self.frame = (self.frame + 1) % 8
            direction = -1 if self.face_dir == -1 else 1
            self.x = self.clamp_x(
                self.x + direction * self.RUN_SPEED,
                self.SPRITE_WIDTH
            )
        elif self.state == self.AUTO_RUN:
            self.frame = (self.frame + 1) % self.AUTO_RUN_FRAME_COUNT
            direction = -1 if self.face_dir == -1 else 1
            next_x = self.x + direction * self.AUTO_RUN_SPEED
            half_width = self.AUTO_RUN_SPRITE_WIDTH // 2
            if next_x <= half_width or next_x >= self.SCREEN_WIDTH - half_width:
                self.face_dir *= -1
            self.x = self.clamp_x(next_x, self.AUTO_RUN_SPRITE_WIDTH)
            if time.monotonic() - self.auto_run_started_at >= self.AUTO_RUN_DURATION:
                self.stop_auto_run()

    def draw(self):
        if self.state in (self.RUN, self.AUTO_RUN):
            sprite_width = (
                self.AUTO_RUN_SPRITE_WIDTH
                if self.state == self.AUTO_RUN
                else self.SPRITE_WIDTH
            )
            self.run_image.clip_composite_draw(
                self.frame * self.SPRITE_WIDTH,
                0,
                self.SPRITE_WIDTH,
                self.SPRITE_WIDTH,
                0,
                'h' if self.face_dir == -1 else '',
                self.x,
                self.y,
                sprite_width,
                sprite_width
            )
        else:
            self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
