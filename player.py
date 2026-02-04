import pygame
import math
from enums import Direction, Element
from constants import BLACK, BLUE, WHITE, RED, BROWN, LIGHT_BLUE, GRAY
from projectile import Projectile

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 170
        self.height = 200
        self.speed = 10
        self.direction = Direction.RIGHT
        
        # Physics
        self.velocity_y = 0
        self.gravity = 0.5
        self.jump_power = -15
        self.on_ground = False
        self.ground_level = 550  # Ajusté pour que le personnage soit SUR le sol
        
        # Stats
        self.max_hp = 100
        self.hp = 100
        self.attack = 15
        self.defense = 5
        self.elements = {Element.NONE}
        self.gold = 0  # Pièces d'or
        
        # Animation
        self.animation_frame = 0
        self.animation_counter = 0
        self.is_moving = False
        self.animation_state = 'idle'  # idle, walking
        
        # Combat
        self.attack_cooldown = 0
        self.invincible_frames = 0
        
        # Attaque spéciale (cooldown de 10 secondes = 600 frames à 60 FPS)
        self.special_cooldown = 0
        self.special_cooldown_max = 600
        self.special_attack_type = 0  # 0=base, 1=mega, 2=ultra
        
        # Load animation sprites
        self.sprites = {
            'idle': [],
            'walking': []
        }
        
        try:
            # Load idle sprite
            idle_sprite = pygame.image.load('player_idle.png').convert_alpha()
            idle_sprite = pygame.transform.scale(idle_sprite, (self.width, self.height))
            self.sprites['idle'].append(idle_sprite)
            
            # Load walking sprites
            for i in range(1, 4):  # 3 walking frames
                walk_sprite = pygame.image.load(f'player_walk_{i}.png').convert_alpha()
                walk_sprite = pygame.transform.scale(walk_sprite, (self.width, self.height))
                self.sprites['walking'].append(walk_sprite)
            
            self.sprites_loaded = True
        except Exception as e:
            # Fallback if images not found
            print(f"Error loading sprites: {e}")
            self.sprites_loaded = False
        
        # Couleurs pour le dessin (fallback)
        self.body_color = (100, 150, 255)
        self.head_color = (255, 220, 180)
    
    def unlock_element(self, element):
        self.elements.add(element)
        if element == Element.EAU:
            self.max_hp += 20
            self.hp = min(self.hp + 20, self.max_hp)
        elif element == Element.TERRE:
            self.defense += 5
        elif element == Element.FEU:
            self.attack += 10
        elif element == Element.AIR:
            self.speed += 1
    
    def move(self, dx, obstacles, world_width=2732):
        # Platform movement - only horizontal
        new_x = self.x + dx
        
        # Check world bounds (default: 2 screens of 1366 = 2732)
        if new_x < 0:
            new_x = 0
        elif new_x + self.width > world_width:
            new_x = world_width - self.width
        
        self.x = new_x
        self.is_moving = dx != 0
    
    def apply_gravity(self):
        # Apply gravity
        self.velocity_y += self.gravity
        self.y += self.velocity_y
        
        # Check ground collision
        if self.y >= self.ground_level:
            self.y = self.ground_level
            self.velocity_y = 0
            self.on_ground = True
        else:
            self.on_ground = False
    
    def jump(self):
        if self.on_ground:
            self.velocity_y = self.jump_power
            self.on_ground = False
    
    def update(self, keys, obstacles, keybindings=None, world_width=2732):
        # Utiliser les keybindings par défaut si non fournis
        if keybindings is None:
            keybindings = {
                'move_left': [pygame.K_q, pygame.K_LEFT],
                'move_right': [pygame.K_d, pygame.K_RIGHT],
                'jump': [pygame.K_SPACE],
                'heal': [pygame.K_e]
            }
        
        dx = 0
        
        # Horizontal movement only
        move_left = any(keys[k] for k in keybindings.get('move_left', []) if k < len(keys))
        move_right = any(keys[k] for k in keybindings.get('move_right', []) if k < len(keys))
        
        if move_left:
            dx = -self.speed
            self.direction = Direction.LEFT
        elif move_right:
            dx = self.speed
            self.direction = Direction.RIGHT
        
        # Jump
        jump_pressed = any(keys[k] for k in keybindings.get('jump', []) if k < len(keys))
        if jump_pressed:
            self.jump()
        
        # Move horizontally with world bounds
        self.move(dx, obstacles, world_width)
        
        # Apply gravity
        self.apply_gravity()
        
        # Animation
        if self.is_moving:
            self.animation_state = 'walking'
            self.animation_counter += 1
            if self.animation_counter >= 8:  # Slower animation cycle
                self.animation_frame = (self.animation_frame + 1) % 3  # 3 walking frames
                self.animation_counter = 0
        else:
            self.animation_state = 'idle'
            self.animation_frame = 0
        
        # Cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.invincible_frames > 0:
            self.invincible_frames -= 1
    
    def shoot(self):
        if self.attack_cooldown <= 0:
            self.attack_cooldown = 30
            
            # Position du projectile
            proj_x = self.x + self.width // 2
            proj_y = self.y + self.height // 2
            
            # Élément à utiliser (prendre le plus puissant)
            element = Element.NONE
            if Element.FEU in self.elements:
                element = Element.FEU
            elif Element.AIR in self.elements:
                element = Element.AIR
            elif Element.TERRE in self.elements:
                element = Element.TERRE
            elif Element.EAU in self.elements:
                element = Element.EAU
            
            return Projectile(proj_x, proj_y, self.direction, element, self.attack)
        return None
    
    def take_damage(self, damage):
        if self.invincible_frames <= 0:
            actual_damage = max(1, damage - self.defense)
            self.hp -= actual_damage
            self.invincible_frames = 60
            return actual_damage
        return 0
    
    def heal(self, amount):
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        self.hp = min(self.hp, self.max_hp) # Double verification unnecessary but safe
        return self.hp - old_hp
    
    def draw(self, screen, camera_x, camera_y):
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # Effet de clignotement si invincible
        if self.invincible_frames > 0 and self.invincible_frames % 10 < 5:
            return
        
        # Si les sprites sont chargés, les utiliser
        if self.sprites_loaded and len(self.sprites[self.animation_state]) > 0:
            # Get the current sprite based on animation state and frame
            current_sprite = self.sprites[self.animation_state][self.animation_frame]
            
            # Flip sprite based on direction
            sprite_to_draw = current_sprite
            if self.direction == Direction.LEFT:
                sprite_to_draw = pygame.transform.flip(current_sprite, True, False)
            
            screen.blit(sprite_to_draw, (screen_x, screen_y))
            
            # Indicateur d'élément actif
            if len(self.elements) > 1:
                element_color = None
                if Element.FEU in self.elements:
                    element_color = (255, 100, 30)
                elif Element.AIR in self.elements:
                    element_color = (200, 230, 255)
                elif Element.TERRE in self.elements:
                    element_color = (139, 90, 43)
                elif Element.EAU in self.elements:
                    element_color = (50, 150, 255)
                
                if element_color:
                    pygame.draw.circle(screen, element_color, 
                                     (screen_x + 35, screen_y + 10), 5)
        else:
            # Fallback: dessiner le personnage avec des formes géométriques
            walk_offset = 0
            if self.is_moving:
                walk_offset = math.sin(self.animation_frame * math.pi / 2) * 3
            
            # Corps
            body_rect = pygame.Rect(screen_x + 10, screen_y + 20, 20, 25)
            pygame.draw.rect(screen, self.body_color, body_rect)
            pygame.draw.rect(screen, BLACK, body_rect, 2)
            
            # Tête
            pygame.draw.circle(screen, self.head_color, 
                             (screen_x + 20, int(screen_y + 15 + walk_offset)), 12)
            pygame.draw.circle(screen, BLACK, 
                             (screen_x + 20, int(screen_y + 15 + walk_offset)), 12, 2)
            
            # Yeux
            eye_y = int(screen_y + 13 + walk_offset)
            pygame.draw.circle(screen, BLACK, (screen_x + 16, eye_y), 2)
            pygame.draw.circle(screen, BLACK, (screen_x + 24, eye_y), 2)
            
            # Bras
            if self.direction == Direction.RIGHT:
                pygame.draw.line(screen, self.head_color, 
                               (screen_x + 30, screen_y + 30), 
                               (screen_x + 38, screen_y + 35), 4)
            elif self.direction == Direction.LEFT:
                pygame.draw.line(screen, self.head_color,
                               (screen_x + 10, screen_y + 30),
                               (screen_x + 2, screen_y + 35), 4)
            else:
                pygame.draw.line(screen, self.head_color,
                               (screen_x + 10, screen_y + 30),
                               (screen_x + 5, screen_y + 38), 4)
                pygame.draw.line(screen, self.head_color,
                               (screen_x + 30, screen_y + 30),
                               (screen_x + 35, screen_y + 38), 4)
            
            # Jambes
            leg_offset = int(walk_offset * 2)
            pygame.draw.line(screen, BLUE,
                           (screen_x + 15, screen_y + 45),
                           (screen_x + 13, screen_y + 60 + leg_offset), 4)
            pygame.draw.line(screen, BLUE,
                           (screen_x + 25, screen_y + 45),
                           (screen_x + 27, screen_y + 60 - leg_offset), 4)
            
            # Indicateur d'élément actif
            if len(self.elements) > 1:
                element_color = None
                if Element.FEU in self.elements:
                    element_color = (255, 100, 30)
                elif Element.AIR in self.elements:
                    element_color = (200, 230, 255)
                elif Element.TERRE in self.elements:
                    element_color = (139, 90, 43)
                elif Element.EAU in self.elements:
                    element_color = (50, 150, 255)
                
                if element_color:
                    pygame.draw.circle(screen, element_color, 
                                     (screen_x + 35, screen_y + 10), 5)
