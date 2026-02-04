import random
import pygame
from enums import Element
from enemy import Enemy

class Kingdom:
    def __init__(self, name, element, bg_color, bg_image_path=None, screen_width=1366, screen_height=768):
        self.name = name
        self.element = element
        self.bg_color = bg_color
        self.completed = False
        self.obstacles = []
        self.enemies = []
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Load background image
        self.bg_image = None
        if bg_image_path:
            try:
                self.bg_image = pygame.image.load(bg_image_path).convert()
                # Scale to actual screen size
                self.bg_image = pygame.transform.scale(self.bg_image, (screen_width, screen_height))
            except:
                print(f"Warning: Could not load background image {bg_image_path}")
                self.bg_image = None
        
        self.generate_world()
    
    def generate_world(self):
        # No obstacles in platform mode
        self.obstacles = []
        
        # Générer des ennemis - ils spawnnent sur la droite de l'écran
        enemy_count = 5 if self.element != Element.NONE else 3
        for i in range(enemy_count):
            # Spawn progressivement de la droite vers le centre
            # Entre 50% et 120% de la largeur de l'écran (certains hors écran à droite)
            x = int(self.screen_width * (0.5 + (i * 0.15)))
            # Position Y aléatoire entre 30% et 80% de la hauteur
            y = random.randint(int(self.screen_height * 0.3), int(self.screen_height * 0.8))
            enemy_type = random.choice(["mini", "normal"])
            self.enemies.append(Enemy(x, y, enemy_type, self.element))
        
        # Boss à la fin - complètement à droite
        if self.element != Element.NONE:
            boss_x = int(self.screen_width * 1.3)  # Hors écran à droite
            boss_y = int(self.screen_height * 0.7)
            self.enemies.append(Enemy(boss_x, boss_y, "boss", self.element))
