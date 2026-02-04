import random
import pygame
import math
from enums import Element
from constants import RED, GREEN, BLACK, BLUE, WHITE

class Enemy:
    def __init__(self, x, y, enemy_type, element, kingdom_index=0):
        self.x = x
        self.ground_level = 640 # Ajusté pour être sur le sol
        self.y = self.ground_level
        self.width = 35
        self.height = 40
        self.enemy_type = enemy_type
        self.element = element
        self.kingdom_index = kingdom_index
        
        # Physics
        self.velocity_y = 0
        self.gravity = 0.8
        self.on_ground = True
        
        # Difficulté progressive
        hp_multiplier = 1.0 + (kingdom_index * 0.15)
        
        # Stats selon le type - dégâts réduits à 5-7
        if enemy_type == "mini":
            base_hp = 75
            self.max_hp = int(base_hp * hp_multiplier)
            self.hp = self.max_hp
            self.attack = 5  # Réduit à 5 dégâts
            self.speed = 2
            self.size = 30
        elif enemy_type == "normal":
            base_hp = 100
            self.max_hp = int(base_hp * hp_multiplier)
            self.hp = self.max_hp
            self.attack = 7  # 7 dégâts
            self.speed = 1.5
            self.size = 35
        else:  # boss
            base_hp = 200
            self.max_hp = int(base_hp * hp_multiplier)
            self.hp = self.max_hp
            self.attack = 7  # 7 dégâts
            self.speed = 1
            self.size = 50
        
        # Couleur selon l'élément
        if element == Element.FEU:
            self.color = (255, 100, 50)
        elif element == Element.EAU:
            self.color = (50, 150, 255)
        elif element == Element.TERRE:
            self.color = (139, 90, 43)
        elif element == Element.AIR:
            self.color = (200, 230, 255)
        else:
            self.color = (80, 50, 100)
        
        # Charger le sprite du monstre
        try:
            self.sprite = pygame.image.load('Monstre.png').convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (self.size * 2, self.size * 2))
            self.has_sprite = True
        except:
            self.has_sprite = False
        
        # IA
        self.direction = random.choice([0, 1])  # 0=left, 1=right
        self.move_timer = 0
        self.attack_cooldown = 0
        self.aggro_range = 300
    
    def update(self, player_x, player_y, obstacles):
        # Apply gravity
        if not self.on_ground:
            self.velocity_y += self.gravity
            self.y += self.velocity_y
            
            # Check ground collision
            if self.y >= self.ground_level:
                self.y = self.ground_level
                self.velocity_y = 0
                self.on_ground = True
        
        # Only move horizontally when on ground
        if self.on_ground:
            # Calculer la distance au joueur
            dx = player_x - self.x
            distance = abs(dx)
            
            # Si le joueur est proche, le suivre horizontalement
            if distance < self.aggro_range:
                if dx > 0:
                    self.x += self.speed
                    self.last_dx = self.speed
                elif dx < 0:
                    self.x -= self.speed
                    self.last_dx = -self.speed
            else:
                # Mouvement aléatoire horizontal
                self.move_timer += 1
                if self.move_timer >= 60:
                    self.direction = random.choice([0, 1])  # 0=left, 1=right
                    self.move_timer = 0
                
                if self.direction == 0:  # Gauche
                    self.x -= self.speed
                elif self.direction == 1:  # Droite
                    self.x += self.speed
            
            # Vérifier les limites horizontales
            if self.x < 0:
                self.x = 0
            elif self.x > 2000 - self.width:
                self.x = 2000 - self.width
        
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
    
    def draw(self, screen, camera_x, camera_y):
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # Dessiner le sprite du monstre si disponible
        if self.has_sprite:
            # Calculer la position centrée
            sprite_x = screen_x + self.width // 2 - self.sprite.get_width() // 2
            sprite_y = screen_y + self.height // 2 - self.sprite.get_height() // 2
            
            # Retourner le sprite si l'ennemi va à gauche
            if hasattr(self, 'last_dx') and self.last_dx < 0:
                sprite_to_draw = pygame.transform.flip(self.sprite, True, False)
            else:
                sprite_to_draw = self.sprite
            
            screen.blit(sprite_to_draw, (sprite_x, sprite_y))
        else:
            # Fallback: dessin géométrique
            # Corps de l'ennemi
            pygame.draw.circle(screen, self.color, 
                             (screen_x + self.width // 2, screen_y + self.height // 2), 
                             self.size // 2)
            pygame.draw.circle(screen, BLACK,
                             (screen_x + self.width // 2, screen_y + self.height // 2),
                             self.size // 2, 2)
            
            # Yeux méchants
            eye_y = screen_y + self.height // 2 - 5
            pygame.draw.circle(screen, RED, (screen_x + self.width // 2 - 8, eye_y), 4)
            pygame.draw.circle(screen, RED, (screen_x + self.width // 2 + 8, eye_y), 4)
        
        # Barre de vie
        hp_bar_width = self.size
        hp_bar_height = 5
        hp_percentage = self.hp / self.max_hp
        
        pygame.draw.rect(screen, RED,
                       (screen_x, screen_y - 10, hp_bar_width, hp_bar_height))
        pygame.draw.rect(screen, GREEN,
                       (screen_x, screen_y - 10, int(hp_bar_width * hp_percentage), hp_bar_height))
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def take_damage(self, damage):
        self.hp -= damage
        return self.hp <= 0
