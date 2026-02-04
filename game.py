import pygame
import sys
import random
import math
import cv2
import os
from constants import *
from enums import GameState, Element, Direction
from particles import Particle
from ui import Button
from player import Player
from kingdom import Kingdom

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Avatar : L'Équilibre Perdu")
        self.clock = pygame.time.Clock()
        self.state = GameState.MENU
        
        # Récupérer la taille réelle de l'écran
        self.screen_width, self.screen_height = self.screen.get_size()
        
        # Calculer le facteur d'échelle (référence: 1366x768)
        self.scale_x = self.screen_width / 1366
        self.scale_y = self.screen_height / 768
        self.scale = min(self.scale_x, self.scale_y)  # Utiliser le plus petit pour garder les proportions
        
        # Polices - adaptées à la taille de l'écran
        self.title_font = pygame.font.Font(None, int(90 * self.scale))
        self.subtitle_font = pygame.font.Font(None, int(55 * self.scale))
        self.text_font = pygame.font.Font(None, int(40 * self.scale))
        self.small_font = pygame.font.Font(None, int(30 * self.scale))
        
        # Animation du menu - Vidéo en arrière-plan
        video_path = os.path.join(os.path.dirname(__file__), "Dragon_incrusté_dans_les_montagnes.mp4")
        self.menu_video = cv2.VideoCapture(video_path)
        self.menu_video_frame = None
        
        # Jeu
        self.player = None
        self.camera_x = 0
        self.camera_y = 0
        self.particles = []
        self.projectiles = []
        
        # Royaumes
        self.kingdoms = [
            Kingdom("Royaume de l'Eau", Element.EAU, (50, 100, 150), "eau.jpg", self.screen_width, self.screen_height),
            Kingdom("Royaume de la Terre", Element.TERRE, (100, 70, 40), "jungle.jpg", self.screen_width, self.screen_height),
            Kingdom("Royaume de l'Air", Element.AIR, (135, 206, 235), "air.jpg", self.screen_width, self.screen_height),
            Kingdom("Royaume du Feu", Element.FEU, (139, 50, 30), "feu.jpg", self.screen_width, self.screen_height)
        ]
        self.current_kingdom_index = 0
        self.current_kingdom = None
        
        # Dialogue
        self.dialogue_text = ""
        self.dialogue_timer = 0
    
    def start_game(self):
        self.player = Player(80, 200)  # Spawn au sol
        self.current_kingdom = self.kingdoms[self.current_kingdom_index]
        self.camera_x = 0
        self.camera_y = 0
        self.projectiles = []
        self.particles = []
        self.state = GameState.GAME
        self.show_dialogue(f"Bienvenue dans le {self.current_kingdom.name}...")
    
    def show_dialogue(self, text):
        self.dialogue_text = text
        self.dialogue_timer = 180
    
    def update_camera(self):
        # Centrer la caméra sur le joueur
        target_x = self.player.x - SCREEN_WIDTH // 2 + self.player.width // 2
        target_y = self.player.y - SCREEN_HEIGHT // 2 + self.player.height // 2
        
        # Limiter la caméra aux bords du monde
        target_x = max(0, min(target_x, 2000 - SCREEN_WIDTH))
        offset_y = 250
        target_y = self.player.y - SCREEN_HEIGHT // 2 + self.player.height // 2 - offset_y

        
        # Mouvement fluide de la caméra
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
    
    def create_particles(self, x, y, color, count=15):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 8)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            self.particles.append(Particle(x, y, color, velocity))
    
    def draw_menu(self):
        # Lire et afficher la vidéo en arrière-plan
        ret, frame = self.menu_video.read()
        
        # Si la vidéo est terminée, recommencer au début
        if not ret:
            self.menu_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.menu_video.read()
        
        if ret:
            # Convertir le frame OpenCV (BGR) en format Pygame (RGB)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Obtenir les dimensions de la vidéo
            video_height, video_width = frame.shape[:2]
            
            # Calculer les ratios pour remplir l'écran (mode "cover")
            scale_width = self.screen_width / video_width
            scale_height = self.screen_height / video_height
            scale = max(scale_width, scale_height)  # Utiliser le plus grand pour couvrir tout l'écran
            
            # Nouvelles dimensions après scaling
            new_width = int(video_width * scale)
            new_height = int(video_height * scale)
            
            # Redimensionner la vidéo
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            # Calculer les offsets pour centrer et cropper
            x_offset = (new_width - self.screen_width) // 2
            y_offset = (new_height - self.screen_height) // 2
            
            # Cropper la partie centrale pour qu'elle corresponde exactement à la taille de l'écran
            frame = frame[y_offset:y_offset + self.screen_height, x_offset:x_offset + self.screen_width]
            
            # Convertir en surface Pygame
            frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            self.screen.blit(frame_surface, (0, 0))
        
        # Titre
        title_text = self.title_font.render("AVATAR", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(self.screen_width // 2, int(180 * self.scale)))
        
        # Ombre du titre
        shadow_text = self.title_font.render("AVATAR", True, (139, 69, 19))
        shadow_offset = int(5 * self.scale)
        shadow_rect = shadow_text.get_rect(center=(self.screen_width // 2 + shadow_offset, int(185 * self.scale)))
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
        
        # Sous-titre
        subtitle_text = self.subtitle_font.render("Héritier des 4 Mondes", True, (255, 250, 205))
        subtitle_rect = subtitle_text.get_rect(center=(self.screen_width // 2, int(260 * self.scale)))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Boutons
        button_width = int(350 * self.scale)
        button_height = int(75 * self.scale)
        start_button = Button(self.screen_width // 2 - button_width // 2, int(360 * self.scale), 
                            button_width, button_height, 
                            "Commencer le Jeu", (34, 139, 34), (50, 180, 50), self.scale)
        quit_button = Button(self.screen_width // 2 - button_width // 2, int(460 * self.scale), 
                           button_width, button_height,
                           "Quitter le Jeu", (139, 0, 0), (180, 0, 0), self.scale)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        start_button.check_hover(mouse_pos)
        quit_button.check_hover(mouse_pos)
        
        start_button.draw(self.screen)
        quit_button.draw(self.screen)
        
        # Texte d'ambiance
        ambient_text = self.small_font.render("Le destin d'Aelyra repose entre tes mains...", True, (200, 200, 150))
        ambient_rect = ambient_text.get_rect(center=(self.screen_width // 2, self.screen_height - int(60 * self.scale)))
        self.screen.blit(ambient_text, ambient_rect)
        
        if start_button.is_clicked(mouse_pos, mouse_pressed):
            self.start_game()
        
        if quit_button.is_clicked(mouse_pos, mouse_pressed):
            pygame.quit()
            sys.exit()
    
    def draw_game(self):
        # Fond du royaume - use image if available, otherwise use color
        if self.current_kingdom.bg_image:
            self.screen.blit(self.current_kingdom.bg_image, (0, 0))
        else:
            self.screen.fill(self.current_kingdom.bg_color)
        
        # No grid or obstacles in platform mode
        
        # Dessiner les ennemis
        for enemy in self.current_kingdom.enemies:
            enemy.draw(self.screen, self.camera_x, self.camera_y)
        
        # Dessiner les projectiles
        for projectile in self.projectiles:
            projectile.draw(self.screen, self.camera_x, self.camera_y)
        
        # Dessiner les particules
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Dessiner le joueur
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        # HUD
        self.draw_hud()
        
        # Dialogue
        if self.dialogue_timer > 0:
            self.draw_dialogue()
            self.dialogue_timer -= 1
    
    def draw_hud(self):
        # Panneau HUD semi-transparent
        hud_height = int(110 * self.scale)
        hud_surface = pygame.Surface((self.screen_width, hud_height))
        hud_surface.set_alpha(180)
        hud_surface.fill((20, 20, 40))
        self.screen.blit(hud_surface, (0, 0))
        
        # Marges et espacements adaptés
        margin = int(25 * self.scale)
        
        # Barre de vie
        hp_text = self.text_font.render(f"HP:", True, WHITE)
        self.screen.blit(hp_text, (margin, margin))
        
        hp_bar_x = int(100 * self.scale)
        hp_bar_width = int(320 * self.scale)
        hp_bar_height = int(35 * self.scale)
        hp_percentage = self.player.hp / self.player.max_hp
        
        pygame.draw.rect(self.screen, RED, (hp_bar_x, margin, hp_bar_width, hp_bar_height))
        pygame.draw.rect(self.screen, GREEN, (hp_bar_x, margin, int(hp_bar_width * hp_percentage), hp_bar_height))
        pygame.draw.rect(self.screen, WHITE, (hp_bar_x, margin, hp_bar_width, hp_bar_height), int(3 * self.scale))
        
        hp_value = self.small_font.render(f"{self.player.hp}/{self.player.max_hp}", True, WHITE)
        hp_value_x = hp_bar_x + hp_bar_width // 2 - hp_value.get_width() // 2
        self.screen.blit(hp_value, (hp_value_x, margin + int(7 * self.scale)))
        
        # Royaume actuel
        kingdom_y = margin + hp_bar_height + int(10 * self.scale)
        kingdom_text = self.small_font.render(f"Royaume: {self.current_kingdom.name}", 
                                             True, YELLOW)
        self.screen.blit(kingdom_text, (margin, kingdom_y))
        
        # Ennemis restants
        enemies_x = int(450 * self.scale)
        enemies_text = self.small_font.render(f"Ennemis: {len(self.current_kingdom.enemies)}", 
                                             True, WHITE)
        self.screen.blit(enemies_text, (enemies_x, kingdom_y))
        
        # Éléments débloqués
        elem_start_x = int(720 * self.scale)
        elem_radius = int(18 * self.scale)
        elem_spacing = int(45 * self.scale)
        elem_y = int(50 * self.scale)
        
        for i, elem in enumerate([Element.EAU, Element.TERRE, Element.AIR, Element.FEU]):
            elem_x = elem_start_x + i * elem_spacing
            if elem in self.player.elements:
                if elem == Element.EAU:
                    color = BLUE
                elif elem == Element.TERRE:
                    color = BROWN
                elif elem == Element.AIR:
                    color = LIGHT_BLUE
                else:
                    color = RED
                pygame.draw.circle(self.screen, color, (elem_x, elem_y), elem_radius)
            else:
                pygame.draw.circle(self.screen, GRAY, (elem_x, elem_y), elem_radius)
            pygame.draw.circle(self.screen, WHITE, (elem_x, elem_y), elem_radius, int(2 * self.scale))
        
        # Contrôles
        controls = self.small_font.render("ZQSD/Flèches: Bouger | ESPACE: Attaquer | E: Soin", 
                                        True, (200, 200, 200))
        controls_x = self.screen_width - controls.get_width() - margin
        self.screen.blit(controls, (controls_x, kingdom_y))
    
    def draw_dialogue(self):
        # Boîte de dialogue en bas
        dialogue_height = int(120 * self.scale)
        dialogue_width = self.screen_width - int(150 * self.scale)
        margin_x = int(75 * self.scale)
        margin_bottom = int(30 * self.scale)
        
        dialogue_surface = pygame.Surface((dialogue_width, dialogue_height))
        dialogue_surface.set_alpha(220)
        dialogue_surface.fill((20, 20, 40))
        self.screen.blit(dialogue_surface, (margin_x, self.screen_height - dialogue_height - margin_bottom))
        
        pygame.draw.rect(self.screen, YELLOW, 
                       (margin_x, self.screen_height - dialogue_height - margin_bottom, 
                        dialogue_width, dialogue_height), int(3 * self.scale))
        
        # Texte
        lines = []
        words = self.dialogue_text.split()
        current_line = ""
        
        text_margin = int(80 * self.scale)
        for word in words:
            test_line = current_line + word + " "
            if self.text_font.size(test_line)[0] < dialogue_width - text_margin:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
        
        line_spacing = int(40 * self.scale)
        y = self.screen_height - dialogue_height - int(5 * self.scale)
        for line in lines[:3]:
            text_surf = self.text_font.render(line.strip(), True, WHITE)
            self.screen.blit(text_surf, (margin_x + int(25 * self.scale), y))
            y += line_spacing
    
    def update_game(self, keys):
        # Mettre à jour le joueur
        self.player.update(keys, self.current_kingdom.obstacles)
        
        # Tir avec clic gauche de la souris
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:  # Left click
            projectile = self.player.shoot()
            if projectile:
                self.projectiles.append(projectile)
        
        # Soin
        if keys[pygame.K_e] and Element.EAU in self.player.elements:
            if self.player.hp < self.player.max_hp:
                heal_amount = self.player.heal(30)
                if heal_amount > 0:
                    self.create_particles(self.player.x + self.player.width // 2,
                                        self.player.y + self.player.height // 2,
                                        BLUE, 20)
                    self.show_dialogue(f"Soigné de {heal_amount} HP !")
        
        # Mettre à jour les ennemis
        for enemy in self.current_kingdom.enemies[:]:
            enemy.update(self.player.x, self.player.y, self.current_kingdom.obstacles)
            
            # Collision avec le joueur
            player_rect = pygame.Rect(self.player.x, self.player.y, 
                                     self.player.width, self.player.height)
            if enemy.get_rect().colliderect(player_rect):
                damage = self.player.take_damage(enemy.attack)
                if damage > 0:
                    self.create_particles(self.player.x + self.player.width // 2,
                                        self.player.y + self.player.height // 2,
                                        RED, 15)
        
        # Mettre à jour les projectiles
        for projectile in self.projectiles[:]:
            projectile.update()
            
            # Vérifier collision avec ennemis
            proj_rect = pygame.Rect(projectile.x - projectile.size, 
                                   projectile.y - projectile.size,
                                   projectile.size * 2, projectile.size * 2)
            
            for enemy in self.current_kingdom.enemies[:]:
                if proj_rect.colliderect(enemy.get_rect()):
                    if enemy.take_damage(projectile.damage):
                        self.current_kingdom.enemies.remove(enemy)
                        self.create_particles(enemy.x + enemy.width // 2,
                                            enemy.y + enemy.height // 2,
                                            YELLOW, 30)
                    else:
                        self.create_particles(enemy.x + enemy.width // 2,
                                            enemy.y + enemy.height // 2,
                                            projectile.color, 15)
                    
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    break
            
            if projectile.is_dead() and projectile in self.projectiles:
                self.projectiles.remove(projectile)
        
        # Mettre à jour les particules
        for particle in self.particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                self.particles.remove(particle)
        
        # Vérifier victoire du royaume
        if len(self.current_kingdom.enemies) == 0 and not self.current_kingdom.completed:
            self.current_kingdom.completed = True
            self.player.unlock_element(self.current_kingdom.element)
            self.show_dialogue(f"Royaume libéré ! Élément {self.current_kingdom.element.name} débloqué !")
            
            # Passer au royaume suivant
            self.current_kingdom_index += 1
            if self.current_kingdom_index >= len(self.kingdoms):
                self.state = GameState.VICTORY
            else:
                pygame.time.set_timer(pygame.USEREVENT + 1, 3000, 1)
        
        # Vérifier game over
        if self.player.hp <= 0:
            self.state = GameState.GAME_OVER
        
        # Mettre à jour la caméra
        self.update_camera()
    
    def draw_victory(self):
        self.screen.fill((20, 20, 40))
        
        # Particules de victoire
        for _ in range(3):
            x = random.randint(0, self.screen_width)
            y = random.randint(0, self.screen_height)
            self.create_particles(x, y, random.choice([YELLOW, (255, 215, 0), (255, 255, 150)]), 5)
        
        for particle in self.particles[:]:
            particle.update()
            particle.draw(self.screen)
            if particle.lifetime <= 0:
                self.particles.remove(particle)
        
        # Titre de victoire
        victory_text = self.title_font.render("VICTOIRE !", True, (255, 215, 0))
        victory_rect = victory_text.get_rect(center=(self.screen_width // 2, int(180 * self.scale)))
        self.screen.blit(victory_text, victory_rect)
        
        # Messages
        messages = [
            "Tu as libéré tous les Gardiens !",
            "L'équilibre est restauré dans Aelyra.",
            "Le Néant a été vaincu.",
            "Tu es le véritable Avatar !"
        ]
        
        y = int(300 * self.scale)
        message_spacing = int(55 * self.scale)
        for message in messages:
            msg_text = self.text_font.render(message, True, WHITE)
            msg_rect = msg_text.get_rect(center=(self.screen_width // 2, y))
            self.screen.blit(msg_text, msg_rect)
            y += message_spacing
        
        # Bouton retour au menu
        button_width = int(350 * self.scale)
        button_height = int(75 * self.scale)
        menu_button = Button(self.screen_width // 2 - button_width // 2, int(540 * self.scale), 
                           button_width, button_height,
                           "Retour au Menu", (34, 139, 34), (50, 180, 50), self.scale)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        menu_button.check_hover(mouse_pos)
        menu_button.draw(self.screen)
        
        if menu_button.is_clicked(mouse_pos, mouse_pressed):
            self.__init__()
    
    def draw_game_over(self):
        self.screen.fill((20, 0, 0))
        
        # Titre Game Over
        gameover_text = self.title_font.render("GAME OVER", True, RED)
        gameover_rect = gameover_text.get_rect(center=(self.screen_width // 2, int(210 * self.scale)))
        self.screen.blit(gameover_text, gameover_rect)
        
        # Message
        msg_text = self.text_font.render("Le Néant a triomphé...", True, WHITE)
        msg_rect = msg_text.get_rect(center=(self.screen_width // 2, int(320 * self.scale)))
        self.screen.blit(msg_text, msg_rect)
        
        # Boutons
        button_width = int(350 * self.scale)
        button_height = int(75 * self.scale)
        retry_button = Button(self.screen_width // 2 - button_width // 2, int(420 * self.scale), 
                            button_width, button_height,
                            "Réessayer", (139, 0, 0), (180, 0, 0), self.scale)
        menu_button = Button(self.screen_width // 2 - button_width // 2, int(520 * self.scale), 
                           button_width, button_height,
                           "Menu Principal", (100, 100, 100), (150, 150, 150), self.scale)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        retry_button.check_hover(mouse_pos)
        menu_button.check_hover(mouse_pos)
        
        retry_button.draw(self.screen)
        menu_button.draw(self.screen)
        
        if retry_button.is_clicked(mouse_pos, mouse_pressed):
            self.__init__()
            self.start_game()
        
        if menu_button.is_clicked(mouse_pos, mouse_pressed):
            self.__init__()
    
    def run(self):
        running = True
        keys_pressed = pygame.key.get_pressed()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Timer pour passer au royaume suivant
                if event.type == pygame.USEREVENT + 1:
                    self.current_kingdom = self.kingdoms[self.current_kingdom_index]
                    self.player.x = 100
                    self.player.y = 630  # Spawn on the bridge
                    self.projectiles = []
                    self.show_dialogue(f"Bienvenue dans le {self.current_kingdom.name}...")
            
            # Mettre à jour les touches
            keys_pressed = pygame.key.get_pressed()
            
            # Dessiner selon l'état
            if self.state == GameState.MENU:
                self.draw_menu()
            elif self.state == GameState.GAME:
                self.update_game(keys_pressed)
                self.draw_game()
            elif self.state == GameState.VICTORY:
                self.draw_victory()
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()
