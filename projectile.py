import pygame
from enums import Direction, Element
from constants import WHITE

class Projectile:
    def __init__(self, x, y, direction, element, damage):
        self.x = x
        self.y = y
        self.direction = direction
        self.element = element
        self.damage = damage
        self.speed = 8
        self.size = 12
        self.lifetime = 100
        
        # Couleur selon l'élément
        if element == Element.FEU:
            self.color = (255, 100, 30)
        elif element == Element.EAU:
            self.color = (50, 150, 255)
        elif element == Element.TERRE:
            self.color = (139, 90, 43)
        elif element == Element.AIR:
            self.color = (200, 230, 255)
        else:
            self.color = (200, 200, 200)
    
    def update(self):
        if self.direction == Direction.RIGHT:
            self.x += self.speed
        elif self.direction == Direction.LEFT:
            self.x -= self.speed
        elif self.direction == Direction.UP:
            self.y -= self.speed
        elif self.direction == Direction.DOWN:
            self.y += self.speed
        
        self.lifetime -= 1
    
    def draw(self, screen, camera_x, camera_y):
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), self.size)
        pygame.draw.circle(screen, WHITE, (screen_x, screen_y), self.size, 2)
    
    def is_dead(self):
        return self.lifetime <= 0


class SpecialProjectile:
    """Grosse boule de feu spéciale avec beaucoup de dégâts"""
    def __init__(self, x, y, direction, element):
        self.x = x
        self.y = y
        self.direction = direction
        self.element = element
        self.damage = 150  # Gros dégâts
        self.speed = 6
        self.size = 40  # Grande taille
        self.lifetime = 150
        self.pulse_timer = 0
        
        # Couleurs vives pour l'attaque spéciale
        if element == Element.FEU:
            self.color = (255, 50, 0)
            self.glow_color = (255, 200, 100)
        elif element == Element.EAU:
            self.color = (0, 100, 255)
            self.glow_color = (100, 200, 255)
        elif element == Element.TERRE:
            self.color = (139, 69, 19)
            self.glow_color = (200, 150, 100)
        elif element == Element.AIR:
            self.color = (200, 240, 255)
            self.glow_color = (255, 255, 255)
        else:
            self.color = (255, 215, 0)  # Or par défaut
            self.glow_color = (255, 255, 200)
    
    def update(self):
        if self.direction == Direction.RIGHT:
            self.x += self.speed
        elif self.direction == Direction.LEFT:
            self.x -= self.speed
        
        self.lifetime -= 1
        self.pulse_timer += 1
    
    def draw(self, screen, camera_x, camera_y):
        import math
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        # Effet de pulsation
        pulse = abs(math.sin(self.pulse_timer * 0.2)) * 10
        current_size = int(self.size + pulse)
        
        # Halo externe (glow)
        glow_surface = pygame.Surface((current_size * 4, current_size * 4), pygame.SRCALPHA)
        for i in range(3, 0, -1):
            alpha = 50 // i
            glow_size = current_size + (i * 15)
            pygame.draw.circle(glow_surface, (*self.glow_color, alpha), 
                             (current_size * 2, current_size * 2), glow_size)
        screen.blit(glow_surface, (screen_x - current_size * 2, screen_y - current_size * 2))
        
        # Boule principale
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), current_size)
        # Contour lumineux
        pygame.draw.circle(screen, self.glow_color, (screen_x, screen_y), current_size, 4)
        # Centre blanc brillant
        pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), current_size // 3)
    
    def is_dead(self):
        return self.lifetime <= 0


class MegaProjectile:
    """Attaque Mega - achetable en boutique (200 gold)"""
    def __init__(self, x, y, direction, element):
        self.x = x
        self.y = y
        self.direction = direction
        self.element = element
        self.damage = 250  # Plus de dégâts
        self.speed = 8
        self.size = 55
        self.lifetime = 180
        self.pulse_timer = 0
        self.rotation = 0
        
        # Couleurs cyan/électrique
        self.color = (0, 200, 255)
        self.glow_color = (100, 255, 255)
    
    def update(self):
        if self.direction == Direction.RIGHT:
            self.x += self.speed
        elif self.direction == Direction.LEFT:
            self.x -= self.speed
        
        self.lifetime -= 1
        self.pulse_timer += 1
        self.rotation += 10
    
    def draw(self, screen, camera_x, camera_y):
        import math
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        pulse = abs(math.sin(self.pulse_timer * 0.15)) * 15
        current_size = int(self.size + pulse)
        
        # Étoile rotative
        glow_surface = pygame.Surface((current_size * 4, current_size * 4), pygame.SRCALPHA)
        center = current_size * 2
        
        # Dessiner une étoile à 6 branches
        for i in range(6):
            angle = math.radians(self.rotation + i * 60)
            end_x = center + math.cos(angle) * current_size
            end_y = center + math.sin(angle) * current_size
            pygame.draw.line(glow_surface, (*self.glow_color, 150), (center, center), (end_x, end_y), 6)
        
        screen.blit(glow_surface, (screen_x - center, screen_y - center))
        
        # Cercle central
        pygame.draw.circle(screen, self.color, (screen_x, screen_y), current_size // 2)
        pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), current_size // 4)
    
    def is_dead(self):
        return self.lifetime <= 0


class UltraProjectile:
    """Attaque Ultra - la plus puissante (500 gold)"""
    def __init__(self, x, y, direction, element):
        self.x = x
        self.y = y
        self.direction = direction
        self.element = element
        self.damage = 500  # Dégâts massifs
        self.speed = 5
        self.size = 80
        self.lifetime = 200
        self.pulse_timer = 0
        
        # Couleurs arc-en-ciel/cosmique
        self.colors = [(255, 0, 100), (255, 100, 0), (255, 200, 0), (0, 255, 100), (0, 100, 255), (150, 0, 255)]
    
    def update(self):
        if self.direction == Direction.RIGHT:
            self.x += self.speed
        elif self.direction == Direction.LEFT:
            self.x -= self.speed
        
        self.lifetime -= 1
        self.pulse_timer += 1
    
    def draw(self, screen, camera_x, camera_y):
        import math
        screen_x = int(self.x - camera_x)
        screen_y = int(self.y - camera_y)
        
        pulse = abs(math.sin(self.pulse_timer * 0.1)) * 20
        current_size = int(self.size + pulse)
        
        # Anneaux concentriques multicolores
        for i, color in enumerate(self.colors):
            ring_size = current_size - (i * 12)
            if ring_size > 0:
                pygame.draw.circle(screen, color, (screen_x, screen_y), ring_size, 8)
        
        # Centre blanc brillant qui pulse
        core_size = int(20 + abs(math.sin(self.pulse_timer * 0.3)) * 10)
        pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), core_size)
    
    def is_dead(self):
        return self.lifetime <= 0
