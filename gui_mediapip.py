import tkinter as tk
import random
import time as pytime
import cv2
import pygame
import os
from gaze_tracking import MediaPipeEyeTracker


pygame.mixer.init()
base_path = os.path.dirname(os.path.abspath(__file__))


shoot_path = os.path.join(base_path, "sounds", "shoot.wav")
hit_path = os.path.join(base_path, "sounds", "hit.wav")


shoot_sound = pygame.mixer.Sound(shoot_path)
hit_sound = pygame.mixer.Sound(hit_path)

#shoot_sound = pygame.mixer.Sound("sounds/shoot.wav")
#hit_sound = pygame.mixer.Sound("sounds/hit.wav")

class GazeDodgerGame:
    def __init__(self, master):
        self.master = master
        self.master.title("🚀 Gaze Dodger")
        self.master.configure(bg="#111111")
        self.width = 800
        self.height = 600

        self.canvas = tk.Canvas(master, width=self.width, height=self.height, bg="#111111", highlightthickness=0)
        self.canvas.pack()

        self.gaze = MediaPipeEyeTracker()
        self.webcam = cv2.VideoCapture(0)

        if not self.webcam.isOpened():
            print("Error: Could not open webcam.")
            self.running = False
            return

        self.running = False
        self.last_shot_time = pytime.time()
        self.start_screen()
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_screen(self):
        self.canvas.create_text(self.width//2, self.height//2 - 100, text="🚀 Gaze Dodger", fill="cyan", font=("Helvetica", 48, "bold"))
        self.canvas.create_text(self.width//2, self.height//2 - 30, text="Control the player with your eyes", fill="white", font=("Helvetica", 20))
        self.canvas.create_text(self.width//2, self.height//2 + 10, text="Blink to shoot the enemies!", fill="white", font=("Helvetica", 20))

        self.start_button = tk.Button(self.master, text="Start Game", font=("Helvetica", 18), bg="#222222", fg="white",
                                      activebackground="#444444", activeforeground="cyan", command=self.start_game)
        self.start_button.place(x=self.width//2 - 80, y=self.height//2 + 60)

    def start_game(self):
        self.start_button.destroy()
        self.canvas.delete("all")
        self.init_game_elements()
        self.running = True
        self.spawn_enemy()
        self.update_game()

    def init_game_elements(self):
        self.score = 0
        self.lives = 3
        self.score_text = self.canvas.create_text(10, 10, anchor="nw", text=f"Score: {self.score}", fill="white", font=("Helvetica", 16))
        self.lives_text = self.canvas.create_text(10, 40, anchor="nw", text=f"Lives: {self.lives}", fill="white", font=("Helvetica", 16))
        self.player = self.canvas.create_rectangle(375, 550, 425, 580, fill="cyan")
        self.enemies = []
        self.bullets = []

    def spawn_enemy(self):
        x = random.randint(0, self.width - 30)
        enemy = self.canvas.create_oval(x, 0, x + 30, 30, fill="red")
        self.enemies.append(enemy)
        if self.running:
            self.master.after(1500, self.spawn_enemy)

    def shoot(self):
        px1, py1, px2, py2 = self.canvas.coords(self.player)
        bullet = self.canvas.create_rectangle((px1 + px2) // 2 - 5, py1 - 10, (px1 + px2) // 2 + 5, py1, fill="yellow")
        self.bullets.append(bullet)
        shoot_sound.play()

    def move_bullets(self):
        for bullet in self.bullets[:]:
            self.canvas.move(bullet, 0, -15)
            bx1, by1, bx2, by2 = self.canvas.coords(bullet)
            if by2 < 0:
                self.canvas.delete(bullet)
                self.bullets.remove(bullet)
            else:
                for enemy in self.enemies[:]:
                    if self.check_collision(bullet, enemy):
                        self.canvas.delete(bullet)
                        self.canvas.delete(enemy)
                        self.bullets.remove(bullet)
                        self.enemies.remove(enemy)
                        hit_sound.play()
                        self.score += 1
                        self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
                        break

    def move_enemies(self):
        for enemy in self.enemies[:]:
            self.canvas.move(enemy, 0, 10)
            pos = self.canvas.coords(enemy)
            if pos[3] > self.height:
                self.canvas.delete(enemy)
                self.enemies.remove(enemy)
            elif self.check_collision(enemy, self.player):
                self.canvas.delete(enemy)
                self.enemies.remove(enemy)
                self.lives -= 1
                self.canvas.itemconfig(self.lives_text, text=f"Lives: {self.lives}")
                if self.lives <= 0:
                    self.running = False
                    self.show_game_over()

    def check_collision(self, item1, item2):
        x1, y1, x2, y2 = self.canvas.coords(item1)
        a1, b1, a2, b2 = self.canvas.coords(item2)
        return not (x2 < a1 or x1 > a2 or y2 < b1 or y1 > b2)

    def move_player(self, direction):
        px1, _, px2, _ = self.canvas.coords(self.player)
        if direction == "left" and px1 > 0:
            step = 20
            self.canvas.move(self.player, -step, 0)
        elif direction == "right" and px2 < self.width:
            step = 17
            self.canvas.move(self.player, step, 0)

    def update_game(self):
        if not self.running:
            return

        ret, frame = self.webcam.read()
        if ret and frame is not None:
            position, _, _, _ = self.gaze.analyze(frame)

            if position == "LEFT":
                self.move_player("left")
            elif position == "RIGHT":
                self.move_player("right")
            elif position == "CLOSED":
                now = pytime.time()
                if now - self.last_shot_time > 0.5:
                    self.shoot()
                    self.last_shot_time = now

        self.move_enemies()
        self.move_bullets()
        self.master.after(60, self.update_game)  # Faster updates

    def show_game_over(self):
        self.canvas.create_rectangle(0, 0, self.width, self.height, fill="#111111", outline="")
        self.canvas.create_text(self.width//2, self.height//2 - 50, text="Game Over", fill="red", font=("Helvetica", 48, "bold"))
        self.canvas.create_text(self.width//2, self.height//2, text=f"Score: {self.score}", fill="white", font=("Helvetica", 24))

        self.restart_btn = tk.Button(self.master, text="Restart", font=("Helvetica", 18), bg="#222222", fg="white",
                                     activebackground="#444444", activeforeground="cyan", command=self.restart_game)
        self.restart_btn.place(x=self.width//2 - 60, y=self.height//2 + 50)

    def restart_game(self):
        self.canvas.delete("all")
        if hasattr(self, 'restart_btn'):
            self.restart_btn.destroy()
        self.init_game_elements()
        self.running = True
        self.last_shot_time = pytime.time()
        self.spawn_enemy()
        self.update_game()

    def on_close(self):
        self.running = False
        if self.webcam.isOpened():
            self.webcam.release()
        self.gaze.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    game = GazeDodgerGame(root)
    root.mainloop()
