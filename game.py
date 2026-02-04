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
from projectile import Projectile, SpecialProjectile, MegaProjectile, UltraProjectile

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
            Kingdom("Royaume de l'Eau", Element.EAU, (50, 100, 150), "eau.jpg", self.screen_width, self.screen_height, kingdom_index=0),
            Kingdom("Royaume de la Terre", Element.TERRE, (100, 70, 40), "jungle.jpg", self.screen_width, self.screen_height, kingdom_index=1),
            Kingdom("Royaume de l'Air", Element.AIR, (135, 206, 235), "air.jpg", self.screen_width, self.screen_height, kingdom_index=2),
            Kingdom("Royaume du Feu", Element.FEU, (139, 50, 30), "feu.jpg", self.screen_width, self.screen_height, kingdom_index=3)
        ]
        self.current_kingdom_index = 0
        self.current_kingdom = None
        
        # Dialogue
        self.dialogue_text = ""
        self.dialogue_timer = 0
        
        # Keybindings - Touches configurables
        self.default_keybindings = {
            'move_left': [pygame.K_q, pygame.K_LEFT],
            'move_right': [pygame.K_d, pygame.K_RIGHT],
            'jump': [pygame.K_SPACE],
            'heal': [pygame.K_e]
        }
        self.keybindings = self.default_keybindings.copy()
        
        # Settings menu state
        self.waiting_for_key = False
        self.selected_action = None
        
        # Double-click detection for special attack
        self.last_click_time = 0
        self.double_click_threshold = 300  # 300ms max between clicks
        
        # Créer le joueur dès le départ (pour la boutique)
        self.player = Player(80, 200)
    
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
        # Caméra suit le joueur horizontalement avec mouvement fluide
        target_x = self.player.x - self.screen_width // 3
        
        # Limiter la caméra aux bords du monde (2 écrans)
        world_width = self.current_kingdom.world_width
        target_x = max(0, min(target_x, world_width - self.screen_width))
        
        # Mouvement fluide vers la cible
        self.camera_x += (target_x - self.camera_x) * 0.15
        self.camera_y = 0
    
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
        start_button = Button(self.screen_width // 2 - button_width // 2, int(340 * self.scale), 
                            button_width, button_height, 
                            "Commencer le Jeu", (34, 139, 34), (50, 180, 50), self.scale)
        shop_button = Button(self.screen_width // 2 - button_width // 2, int(430 * self.scale), 
                           button_width, button_height,
                           "Boutique", (180, 140, 40), (220, 180, 60), self.scale)
        settings_button = Button(self.screen_width // 2 - button_width // 2, int(520 * self.scale), 
                               button_width, button_height,
                               "Paramètres", (70, 70, 150), (100, 100, 200), self.scale)
        quit_button = Button(self.screen_width // 2 - button_width // 2, int(610 * self.scale), 
                           button_width, button_height,
                           "Quitter le Jeu", (139, 0, 0), (180, 0, 0), self.scale)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        start_button.check_hover(mouse_pos)
        shop_button.check_hover(mouse_pos)
        settings_button.check_hover(mouse_pos)
        quit_button.check_hover(mouse_pos)
        
        start_button.draw(self.screen)
        shop_button.draw(self.screen)
        settings_button.draw(self.screen)
        quit_button.draw(self.screen)
        
        # Texte d'ambiance
        ambient_text = self.small_font.render("Le destin d'Aelyra repose entre tes mains...", True, (200, 200, 150))
        ambient_rect = ambient_text.get_rect(center=(self.screen_width // 2, self.screen_height - int(60 * self.scale)))
        self.screen.blit(ambient_text, ambient_rect)
        
        if start_button.is_clicked(mouse_pos, mouse_pressed):
            self.start_game()
        
        if shop_button.is_clicked(mouse_pos, mouse_pressed):
            self.state = GameState.SHOP
        
        if settings_button.is_clicked(mouse_pos, mouse_pressed):
            self.state = GameState.SETTINGS
        
        if quit_button.is_clicked(mouse_pos, mouse_pressed):
            pygame.quit()
            sys.exit()
    
    def draw_shop(self):
        # Fond
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(240)
        overlay.fill((30, 25, 20))
        self.screen.blit(overlay, (0, 0))
        
        # Titre
        title_text = self.title_font.render("BOUTIQUE", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(self.screen_width // 2, int(80 * self.scale)))
        self.screen.blit(title_text, title_rect)
        
        # Or du joueur
        gold_text = self.text_font.render(f"Votre Or: {self.player.gold}", True, (255, 215, 0))
        gold_rect = gold_text.get_rect(center=(self.screen_width // 2, int(150 * self.scale)))
        self.screen.blit(gold_text, gold_rect)
        
        # Attaque actuelle
        attack_names = ["Boule de Base", "Attaque Mega", "Attaque Ultra"]
        current_name = attack_names[self.player.special_attack_type]
        current_text = self.small_font.render(f"Attaque actuelle: {current_name}", True, (200, 200, 200))
        current_rect = current_text.get_rect(center=(self.screen_width // 2, int(200 * self.scale)))
        self.screen.blit(current_text, current_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        button_width = int(400 * self.scale)
        button_height = int(100 * self.scale)
        center_x = self.screen_width // 2 - button_width // 2
        
        # Bouton Mega (200 or)
        mega_y = int(280 * self.scale)
        mega_owned = self.player.special_attack_type >= 1
        mega_color = (50, 100, 50) if mega_owned else ((0, 150, 200) if self.player.gold >= 200 else (80, 80, 80))
        mega_label = "MEGA [POSSEDE]" if mega_owned else "MEGA - 200 Or"
        mega_button = Button(center_x, mega_y, button_width, button_height, mega_label, mega_color, (100, 200, 255), self.scale)
        mega_button.check_hover(mouse_pos)
        mega_button.draw(self.screen)
        
        # Description Mega
        if not mega_owned:
            mega_desc = self.small_font.render("Etoile rotative - 250 degats - Effet cyan", True, (150, 200, 255))
            self.screen.blit(mega_desc, (center_x, mega_y + button_height + int(5 * self.scale)))
        
        # Bouton Ultra (500 or)
        ultra_y = int(430 * self.scale)
        ultra_owned = self.player.special_attack_type >= 2
        ultra_color = (50, 100, 50) if ultra_owned else ((200, 50, 200) if self.player.gold >= 500 else (80, 80, 80))
        ultra_label = "ULTRA [POSSEDE]" if ultra_owned else "ULTRA - 500 Or"
        ultra_button = Button(center_x, ultra_y, button_width, button_height, ultra_label, ultra_color, (255, 150, 255), self.scale)
        ultra_button.check_hover(mouse_pos)
        ultra_button.draw(self.screen)
        
        # Description Ultra
        if not ultra_owned:
            ultra_desc = self.small_font.render("Anneaux cosmiques - 500 degats - Arc-en-ciel", True, (255, 150, 255))
            self.screen.blit(ultra_desc, (center_x, ultra_y + button_height + int(5 * self.scale)))
        
        # Bouton Retour
        back_button = Button(int(50 * self.scale), self.screen_height - int(100 * self.scale), 
                            int(200 * self.scale), int(60 * self.scale),
                            "Retour", (100, 50, 50), (150, 80, 80), self.scale)
        back_button.check_hover(mouse_pos)
        back_button.draw(self.screen)
        
        # Gestion des clics
        if mega_button.is_clicked(mouse_pos, mouse_pressed) and not mega_owned and self.player.gold >= 200:
            self.player.gold -= 200
            self.player.special_attack_type = 1
        
        if ultra_button.is_clicked(mouse_pos, mouse_pressed) and not ultra_owned and self.player.gold >= 500:
            self.player.gold -= 500
            self.player.special_attack_type = 2
        
        if back_button.is_clicked(mouse_pos, mouse_pressed):
            self.state = GameState.MENU
    
    def draw_settings(self):
        # Fond semi-transparent
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(230)
        overlay.fill((20, 20, 40))
        self.screen.blit(overlay, (0, 0))
        
        # Titre
        title_text = self.title_font.render("PARAMÈTRES", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(self.screen_width // 2, int(100 * self.scale)))
        self.screen.blit(title_text, title_rect)
        
        # Sous-titre
        subtitle_text = self.text_font.render("Configuration des touches", True, (200, 200, 200))
        subtitle_rect = subtitle_text.get_rect(center=(self.screen_width // 2, int(180 * self.scale)))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Actions et leurs touches
        actions = {
            'move_left': 'Déplacer à gauche',
            'move_right': 'Déplacer à droite',
            'jump': 'Sauter',
            'heal': 'Soin (Eau)'
        }
        
        y_start = int(260 * self.scale)
        y_spacing = int(80 * self.scale)
        button_width = int(250 * self.scale)
        button_height = int(60 * self.scale)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        # Afficher chaque action avec sa touche
        for i, (action_key, action_name) in enumerate(actions.items()):
            y_pos = y_start + i * y_spacing
            
            # Nom de l'action
            action_text = self.text_font.render(action_name + ":", True, WHITE)
            self.screen.blit(action_text, (int(150 * self.scale), y_pos + int(15 * self.scale)))
            
            # Obtenir le nom de la touche
            keys = self.keybindings.get(action_key, [])
            if keys:
                key_name = pygame.key.name(keys[0]).upper()
                if len(keys) > 1:
                    key_name += " / " + pygame.key.name(keys[1]).upper()
            else:
                key_name = "Non assigné"
            
            # Bouton pour changer la touche
            key_button_x = self.screen_width // 2 + int(50 * self.scale)
            if self.waiting_for_key and self.selected_action == action_key:
                key_button = Button(key_button_x, y_pos, button_width, button_height,
                                  "Appuyez sur une touche...", (100, 100, 0), (130, 130, 0), self.scale)
            else:
                key_button = Button(key_button_x, y_pos, button_width, button_height,
                                  key_name, (50, 50, 100), (80, 80, 150), self.scale)
            
            key_button.check_hover(mouse_pos)
            key_button.draw(self.screen)
            
            # Si on clique sur le bouton, on attend une nouvelle touche
            if key_button.is_clicked(mouse_pos, mouse_pressed) and not self.waiting_for_key:
                self.waiting_for_key = True
                self.selected_action = action_key
        
        # Boutons en bas
        button_width_bottom = int(300 * self.scale)
        button_height_bottom = int(70 * self.scale)
        
        reset_button = Button(self.screen_width // 2 - button_width_bottom - int(20 * self.scale), 
                             self.screen_height - int(150 * self.scale),
                             button_width_bottom, button_height_bottom,
                             "Réinitialiser", (100, 50, 0), (150, 80, 0), self.scale)
        
        back_button = Button(self.screen_width // 2 + int(20 * self.scale), 
                            self.screen_height - int(150 * self.scale),
                            button_width_bottom, button_height_bottom,
                            "Retour", (0, 100, 0), (0, 150, 0), self.scale)
        
        reset_button.check_hover(mouse_pos)
        back_button.check_hover(mouse_pos)
        
        reset_button.draw(self.screen)
        back_button.draw(self.screen)
        
        # Instructions si on attend une touche
        if self.waiting_for_key:
            instruction_text = self.small_font.render("Appuyez sur ESC pour annuler", True, YELLOW)
            instruction_rect = instruction_text.get_rect(center=(self.screen_width // 2, 
                                                                 self.screen_height - int(50 * self.scale)))
            self.screen.blit(instruction_text, instruction_rect)
        
        # Actions des boutons
        if reset_button.is_clicked(mouse_pos, mouse_pressed):
            self.keybindings = {k: v.copy() for k, v in self.default_keybindings.items()}
        
        if back_button.is_clicked(mouse_pos, mouse_pressed):
            self.state = GameState.MENU
    
    def draw_game(self):
        # Fond du royaume - 2 images côte à côte qui défilent
        if self.current_kingdom.bg_image:
            bg = self.current_kingdom.bg_image
            
            # Dessiner 2 copies du fond côte à côte
            self.screen.blit(bg, (-self.camera_x, 0))
            self.screen.blit(bg, (self.screen_width - self.camera_x, 0))
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
        margin = int(20 * self.scale)
        
        # === BARRE DE VIE ===
        hp_y = margin
        
        # Barre de vie directement
        hp_bar_x = margin
        hp_bar_width = int(250 * self.scale)
        hp_bar_height = int(24 * self.scale)
        hp_percentage = self.player.hp / self.player.max_hp
        
        # Fond noir avec bordure dorée (style rétro)
        pygame.draw.rect(self.screen, (0, 0, 0), (hp_bar_x - 2, hp_y - 2, hp_bar_width + 4, hp_bar_height + 4))
        pygame.draw.rect(self.screen, (180, 150, 50), (hp_bar_x - 2, hp_y - 2, hp_bar_width + 4, hp_bar_height + 4), 2)
        
        # Barre de vie (dégradé vert -> jaune -> rouge selon HP)
        if hp_percentage > 0.5:
            bar_color = (50, 220, 50)
        elif hp_percentage > 0.25:
            bar_color = (220, 180, 50)
        else:
            bar_color = (220, 50, 50)
        pygame.draw.rect(self.screen, bar_color, (hp_bar_x, hp_y, int(hp_bar_width * hp_percentage), hp_bar_height))
        
        # Texte HP
        hp_text = self.small_font.render(f"{self.player.hp}/{self.player.max_hp}", True, WHITE)
        self.screen.blit(hp_text, (hp_bar_x + hp_bar_width + int(10 * self.scale), hp_y + int(2 * self.scale)))
        
        # === ÉLÉMENTS (style icônes Avatar) ===
        elem_x = int(500 * self.scale)
        elem_size = int(32 * self.scale)
        elem_spacing = int(50 * self.scale)
        
        element_colors = {
            Element.EAU: ((50, 150, 255), "💧"),
            Element.TERRE: ((139, 90, 43), "🌍"),
            Element.AIR: ((200, 230, 255), "💨"),
            Element.FEU: ((255, 80, 30), "🔥")
        }
        
        for i, elem in enumerate([Element.EAU, Element.TERRE, Element.AIR, Element.FEU]):
            ex = elem_x + i * elem_spacing
            color, _ = element_colors[elem]
            
            if elem in self.player.elements:
                # Élément débloqué - carré brillant
                pygame.draw.rect(self.screen, color, (ex, hp_y, elem_size, elem_size))
                pygame.draw.rect(self.screen, (255, 255, 255), (ex, hp_y, elem_size, elem_size), 2)
                # Effet brillant
                pygame.draw.line(self.screen, (255, 255, 255), (ex + 2, hp_y + 2), (ex + 8, hp_y + 8), 2)
            else:
                # Élément verrouillé - gris avec croix
                pygame.draw.rect(self.screen, (40, 40, 40), (ex, hp_y, elem_size, elem_size))
                pygame.draw.rect(self.screen, (80, 80, 80), (ex, hp_y, elem_size, elem_size), 1)
        
        # === ATTAQUE SPÉCIALE (style barre d'énergie) ===
        special_x = int(750 * self.scale)
        special_width = int(200 * self.scale)
        special_height = int(24 * self.scale)
        
        # Texte
        special_label = self.small_font.render("⚡ SPÉCIAL", True, (255, 200, 50))
        self.screen.blit(special_label, (special_x, hp_y - int(2 * self.scale)))
        
        bar_x = special_x + special_label.get_width() + int(15 * self.scale)
        
        # Calculer progression
        if self.player.special_cooldown_max > 0:
            progress = 1 - (self.player.special_cooldown / self.player.special_cooldown_max)
        else:
            progress = 1
        
        # Fond et bordure
        pygame.draw.rect(self.screen, (0, 0, 0), (bar_x - 2, hp_y - 2, special_width + 4, special_height + 4))
        
        if self.player.special_cooldown <= 0:
            # Prêt = effet pulsant doré
            bar_color = (255, 200, 50)
            pygame.draw.rect(self.screen, (255, 215, 0), (bar_x - 2, hp_y - 2, special_width + 4, special_height + 4), 2)
            status = "PRÊT!"
        else:
            bar_color = (150, 100, 30)
            pygame.draw.rect(self.screen, (100, 80, 30), (bar_x - 2, hp_y - 2, special_width + 4, special_height + 4), 2)
            status = f"{self.player.special_cooldown // 60}s"
        
        pygame.draw.rect(self.screen, bar_color, (bar_x, hp_y, int(special_width * progress), special_height))
        
        # Texte status
        status_text = self.small_font.render(status, True, WHITE)
        self.screen.blit(status_text, (bar_x + special_width // 2 - status_text.get_width() // 2, hp_y + int(2 * self.scale)))
        
        # === ENNEMIS RESTANTS ===
        enemies_x = int(1050 * self.scale)
        enemy_count = len(self.current_kingdom.enemies)
        enemies_text = self.small_font.render(f"x{enemy_count}", True, (255, 100, 100) if enemy_count > 0 else (100, 255, 100))
        self.screen.blit(enemies_text, (enemies_x, hp_y + int(2 * self.scale)))
        
        # === OR ===
        gold_x = int(1150 * self.scale)
        gold_text = self.small_font.render(f"OR: {self.player.gold}", True, (255, 215, 0))
        self.screen.blit(gold_text, (gold_x, hp_y + int(2 * self.scale)))
    
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
        # Mettre à jour le joueur avec les keybindings et la largeur du monde
        self.player.update(keys, self.current_kingdom.obstacles, self.keybindings, self.current_kingdom.world_width)
        
        # Tir avec clic gauche de la souris
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:  # Left click
            projectile = self.player.shoot()
            if projectile:
                self.projectiles.append(projectile)
        
        # Mise à jour du cooldown de l'attaque spéciale
        if self.player.special_cooldown > 0:
            self.player.special_cooldown -= 1
        
        # Soin
        heal_pressed = any(keys[k] for k in self.keybindings.get('heal', []) if k < len(keys))
        if heal_pressed and Element.EAU in self.player.elements:
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
                        # Récompense en or selon le type d'ennemi
                        if enemy.enemy_type == "boss":
                            gold_reward = 50
                        elif enemy.enemy_type == "normal":
                            gold_reward = 20
                        else:
                            gold_reward = 10
                        self.player.gold += gold_reward
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
                
                # Gestion des touches pour les paramètres
                if self.state == GameState.SETTINGS and self.waiting_for_key:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            # Annuler
                            self.waiting_for_key = False
                            self.selected_action = None
                        else:
                            # Assigner la nouvelle touche
                            self.keybindings[self.selected_action] = [event.key]
                            self.waiting_for_key = False
                            self.selected_action = None
                
                # Double-clic pour attaque spéciale
                if self.state == GameState.GAME and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        current_time = pygame.time.get_ticks()
                        if current_time - self.last_click_time < self.double_click_threshold:
                            # Double-clic détecté ! Lancer l'attaque spéciale
                            if self.player.special_cooldown <= 0:
                                # Créer le projectile selon le type acheté
                                elem = list(self.player.elements)[0] if self.player.elements else Element.NONE
                                px = self.player.x + self.player.width // 2
                                py = self.player.y + self.player.height // 2
                                
                                if self.player.special_attack_type == 2:
                                    special = UltraProjectile(px, py, self.player.direction, elem)
                                    particle_color = (255, 100, 255)
                                elif self.player.special_attack_type == 1:
                                    special = MegaProjectile(px, py, self.player.direction, elem)
                                    particle_color = (100, 255, 255)
                                else:
                                    special = SpecialProjectile(px, py, self.player.direction, elem)
                                    particle_color = (255, 200, 50)
                                
                                self.projectiles.append(special)
                                self.player.special_cooldown = self.player.special_cooldown_max
                                self.create_particles(px, py, particle_color, 40)
                        self.last_click_time = current_time
                
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
            elif self.state == GameState.SHOP:
                self.draw_shop()
            elif self.state == GameState.SETTINGS:
                self.draw_settings()
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
