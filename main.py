from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from random import randint

Window.size = (800, 480)
Window.minimum_width, Window.minimum_height = 640, 360

# --- Game Objects ---
class Explorer(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = 'assets/player.png'
        self.size_hint = (None, None)
        self.size = (dp(100), dp(100))
        self.velocity_y = 0
        self.gravity = -1
        self.is_jumping = False
        self.initial_y = 0
        self.move_speed = dp(5)
        self.moving_left = False
        self.moving_right = False

    def update(self):
        self.y += self.velocity_y
        self.velocity_y += self.gravity
        if self.y <= self.initial_y:
            self.y = self.initial_y
            self.is_jumping = False

    def jump(self):
        if not self.is_jumping:
            self.velocity_y = dp(18)
            self.is_jumping = True

    def update_horizontal(self):
        if self.moving_left and self.x > 0:
            self.x -= self.move_speed
        if self.moving_right and self.right < Window.width:
            self.x += self.move_speed

# --- Game Screen ---
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.bg = Image(source='assets/background.jpg', allow_stretch=True, keep_ratio=False)
        self.layout.add_widget(self.bg)

        self.explorer = Explorer()
        self.layout.add_widget(self.explorer)

        self.monkey = Image(source='assets/monkey.png', size_hint=(None, None), size=(dp(80), dp(80)))
        self.layout.add_widget(self.monkey)

        # Coin setup
        self.coin = Image(source='assets/coin.png', size_hint=(None, None), size=(dp(50), dp(50)))
        self.layout.add_widget(self.coin)
        self.coin_sound = SoundLoader.load('assets/coin.mp3')

        self.score = 0
        self.high_score = self.load_high_score()

        self.score_label = Label(text="Score: 0", size_hint=(None, None), size=(dp(150), dp(40)),
                                 pos_hint={'right': 1, 'top': 1}, font_size='20sp', color=(1, 1, 1, 1))
        self.layout.add_widget(self.score_label)

        self.add_widget(self.layout)
        Window.bind(on_resize=self.on_resize)

    def on_resize(self, *args):
        self.update_positions()

    def update_positions(self):
        ground_y = 0.10 * Window.height
        self.explorer.pos = (dp(100), ground_y)
        self.explorer.initial_y = ground_y

        if self.monkey.right < 0:
            self.monkey.pos = (Window.width, ground_y)
        else:
            self.monkey.y = ground_y

        self.place_coin()

    def load_high_score(self):
        try:
            with open("highscore.txt", "r") as f:
                return int(f.read())
        except:
            return 0

    def save_high_score(self):
        with open("highscore.txt", "w") as f:
            f.write(str(self.high_score))

    def start_game(self):
        self.score = 0
        self.explorer.moving_left = False
        self.explorer.moving_right = False
        self.update_positions()
        self.explorer.velocity_y = 0
        self.monkey.pos = (Window.width, self.explorer.y)
        Clock.unschedule(self.update)
        Clock.schedule_interval(self.update, 1 / 60)

    def update(self, dt):
        self.explorer.update()
        self.explorer.update_horizontal()
        self.move_monkey()
        self.check_collision()
        self.update_score()

    def move_monkey(self):
        self.monkey.x -= dp(5)
        if self.monkey.right < 0:
            self.monkey.x = Window.width

    def collide(self, a, b):
        ax, ay = a.pos
        aw, ah = a.size
        bx, by = b.pos
        bw, bh = b.size
        buffer = dp(20)
        return (ax + aw - buffer > bx + buffer and
                ax + buffer < bx + bw - buffer and
                ay + ah - buffer > by + buffer and
                ay + buffer < by + bh - buffer)

    def check_collision(self):
        if self.collide(self.explorer, self.monkey):
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            Clock.unschedule(self.update)
            self.manager.get_screen('game_over').update_labels(self.score, self.high_score)
            self.manager.current = 'game_over'

        # Coin collision
        if self.collide(self.explorer, self.coin):
            self.score += 10
            self.score_label.text = f"Score: {self.score}"
            if self.coin_sound:
                self.coin_sound.play()
            self.place_coin()

    def place_coin(self):
        ground_y = dp(80)  # How far from bottom it stays (like the ground height)
        max_y = ground_y + dp(20)  # It can be a little above ground

        rand_x = randint(int(dp(100)), int(Window.width - dp(80)))
        rand_y = randint(int(ground_y), int(max_y))  # keep Y low

        self.coin.pos = (rand_x, rand_y)


    def update_score(self):
        self.score += 1
        self.score_label.text = f"Score: {self.score}"

# --- Main Menu ---
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        bg = Image(source='assets/blurbackground.png', allow_stretch=True, keep_ratio=False)
        layout.add_widget(bg)

        title = Label(text='[b][color=000000]JUNGLE ESCAPE[/color][/b]', markup=True,
                      font_size='70sp', pos_hint={'center_x': 0.5, 'top': 1.2})
        layout.add_widget(title)

        self.click_sound = SoundLoader.load('assets/click.wav')

        start_btn = Button(text='Start Game',
                           size_hint=(0.3, 0.15), pos_hint={'center_x': 0.5, 'center_y': 0.5},
                           background_color=(0, 0.5, 0, 1), font_size='20sp')
        start_btn.bind(on_press=self.start_game)
        layout.add_widget(start_btn)

        quit_btn = Button(text='Quit',
                          size_hint=(0.3, 0.15), pos_hint={'center_x': 0.5, 'center_y': 0.3},
                          background_color=(0.6, 0, 0, 1), font_size='20sp')
        quit_btn.bind(on_press=self.quit_game)
        layout.add_widget(quit_btn)

        self.add_widget(layout)

    def start_game(self, *args):
        if self.click_sound:
            self.click_sound.play()
        self.manager.get_screen('game').start_game()
        self.manager.current = 'game'

    def quit_game(self, *args):
        App.get_running_app().stop()

# --- Game Over Screen ---
class GameOverScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = FloatLayout()
        bg = Image(source='assets/background.jpg', allow_stretch=True, keep_ratio=False)
        layout.add_widget(bg)

        label = Label(text='[b][color=ff3333]GAME OVER![/color][/b]', markup=True,
                      font_size='50sp', pos_hint={'center_x': 0.5, 'top': 1.25})
        layout.add_widget(label)

        self.score_label = Label(text='', font_size='25sp', pos_hint={'center_x': 0.5, 'center_y': 0.65})
        layout.add_widget(self.score_label)

        self.high_score_label = Label(text='', font_size='22sp', pos_hint={'center_x': 0.5, 'center_y': 0.58})
        layout.add_widget(self.high_score_label)

        restart_btn = Button(text='Restart',
                             size_hint=(0.3, 0.15), pos_hint={'center_x': 0.5, 'center_y': 0.45},
                             background_color=(0, 0.5, 0, 1), font_size='20sp')
        restart_btn.bind(on_press=self.restart_game)
        layout.add_widget(restart_btn)

        quit_btn = Button(text='Quit',
                          size_hint=(0.3, 0.15), pos_hint={'center_x': 0.5, 'center_y': 0.3},
                          background_color=(0.6, 0, 0, 1), font_size='20sp')
        quit_btn.bind(on_press=self.quit_game)
        layout.add_widget(quit_btn)

        self.add_widget(layout)

    def update_labels(self, score, high_score):
        self.score_label.text = f"Your Score: {score}"
        self.high_score_label.text = f"High Score: {high_score}"

    def restart_game(self, *args):
        self.manager.get_screen('game').start_game()
        self.manager.current = 'game'

    def quit_game(self, *args):
        App.get_running_app().stop()

# --- App ---
class JungleApp(App):
    def build(self):
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(MainMenuScreen(name='menu'))
        self.sm.add_widget(GameScreen(name='game'))
        self.sm.add_widget(GameOverScreen(name='game_over'))

        Window.bind(on_key_down=self.on_key_down)
        Window.bind(on_key_up=self.on_key_up)
        return self.sm

    def on_key_down(self, window, key, *args):
        current = self.sm.get_screen('game')
        if self.sm.current != 'game':
            return
        if key in (32, 273):  # Space or Up
            current.explorer.jump()
        elif key == 276:  # Left
            current.explorer.moving_left = True
        elif key == 275:  # Right
            current.explorer.moving_right = True

    def on_key_up(self, window, key, *args):
        current = self.sm.get_screen('game')
        if self.sm.current != 'game':
            return
        if key == 276:  # Left
            current.explorer.moving_left = False
        elif key == 275:  # Right
            current.explorer.moving_right = False

if __name__ == '__main__':
    JungleApp().run()
