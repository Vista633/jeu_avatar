import random
import pygame
from enums import Element
from enemy import Enemy

class Kingdom:
    def __init__(self, name, element, bg_color, bg_image_path=None, screen_width=1366, screen_height=768, kingdom_index=0):
        self.name = name
        self.element = element
        self.bg_color = bg_color
        self.completed = False
        self.obstacles = []
        self.enemies = []
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.kingdom_index = kingdom_index
        
        # Largeur du monde = 2 écrans
        self.world_width = screen_width * 2
        
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
        self.obstacles = []
        
        # Nombre d'ennemis par royaume
        enemy_counts = [3, 5, 6, 8]
        enemy_count = enemy_counts[min(self.kingdom_index, 3)]
        ground_level = 640
        
        # Répartir les ennemis sur les 2 écrans
        for i in range(enemy_count):
            # Distribution régulière sur la largeur totale (2 écrans)
            x = int(self.screen_width * 0.5 + (i * (self.world_width - self.screen_width) / max(enemy_count, 1)))
            y = ground_level
            enemy_type = random.choice(["mini", "normal", "normal"])
            enemy = Enemy(x, y, enemy_type, self.element, self.kingdom_index)
            self.enemies.append(enemy)
        
        # Boss à la fin du monde (près de la fin du 2ème écran)
        if self.element != Element.NONE:
            boss_x = int(self.world_width - 200)
            boss_y = ground_level
            boss = Enemy(boss_x, boss_y, "boss", self.element, self.kingdom_index)
            self.enemies.append(boss)
