import random
import pygame
import cv2
from enums import Element
from enemy import Enemy

class Kingdom:
    def __init__(self, name, element, bg_color, bg_path=None, bg_type='image', screen_width=1366, screen_height=768, kingdom_index=0):
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
        
        # Type de fond: 'image' ou 'video'
        self.bg_type = bg_type
        self.bg_video = None
        self.bg_image = None
        self.bg_video_frames = []  # Cache de frames pour performance
        self.bg_video_frame_index = 0  # Index du frame actuel
        
        # Load background (image ou video)
        if bg_path:
            if bg_type == 'video':
                # Charger la vidéo avec cv2 et pré-cacher tous les frames
                try:
                    print(f"Chargement vidéo {bg_path}...")
                    video = cv2.VideoCapture(bg_path)
                    
                    if not video.isOpened():
                        print(f"Warning: Could not load background video {bg_path}")
                        self.bg_video = None
                    else:
                        # Pré-charger TOUS les frames pour performance optimale
                        frame_count = 0
                        while True:
                            ret, frame = video.read()
                            if not ret:
                                break
                            
                            # Convertir BGR -> RGB
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            
                            # Redimensionner pour remplir l'écran
                            video_height, video_width = frame.shape[:2]
                            scale_width = screen_width / video_width
                            scale_height = screen_height / video_height
                            scale = max(scale_width, scale_height)
                            
                            new_width = int(video_width * scale)
                            new_height = int(video_height * scale)
                            
                            frame = cv2.resize(frame, (new_width, new_height), 
                                             interpolation=cv2.INTER_LINEAR)
                            
                            # Cropper au centre
                            x_offset = (new_width - screen_width) // 2
                            y_offset = (new_height - screen_height) // 2
                            frame = frame[y_offset:y_offset + screen_height, 
                                        x_offset:x_offset + screen_width]
                            
                            # Convertir en Surface Pygame et stocker en cache
                            surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
                            self.bg_video_frames.append(surface)
                            frame_count += 1
                        
                        video.release()
                        print(f"✓ {frame_count} frames vidéo chargés et mis en cache")
                        
                except Exception as e:
                    print(f"Error loading video {bg_path}: {e}")
                    self.bg_video = None
            else:  # image
                try:
                    self.bg_image = pygame.image.load(bg_path).convert()
                    # Scale to actual screen size
                    self.bg_image = pygame.transform.scale(self.bg_image, (screen_width, screen_height))
                except:
                    print(f"Warning: Could not load background image {bg_path}")
                    self.bg_image = None
        
        self.generate_world()
    
    def get_video_frame(self):
        """Retourne le frame actuel du cache (optimisé pour performance)"""
        if not self.bg_video_frames:
            return None
        
        # Obtenir le frame actuel depuis le cache
        surface = self.bg_video_frames[self.bg_video_frame_index]
        
        # Avancer à la frame suivante (boucle automatique)
        self.bg_video_frame_index = (self.bg_video_frame_index + 1) % len(self.bg_video_frames)
        
        return surface

    def generate_world(self):
        self.obstacles = []
        self.enemies = []
        
        # Nombre d'ennemis par royaume (5, 7, 8, 9) -> Max 10 avec le boss
        enemy_counts = [5, 7, 8, 9]
        enemy_count = enemy_counts[min(self.kingdom_index, 3)]
        ground_level = 640
        
        # Répartir les ennemis sur les 2 écrans
        for i in range(enemy_count):
            # Distribution régulière sur la largeur totale (2 écrans)
            x = int(self.screen_width * 0.5 + (i * (self.world_width - self.screen_width) / max(enemy_count, 1)))
            y = ground_level
            enemy_type = random.choice(["mini", "normal", "normal"])
            enemy = Enemy(x, y, enemy_type, self.element, self.kingdom_index, self.world_width)
            self.enemies.append(enemy)
        
        # Boss à la fin du monde (près de la fin du 2ème écran)
        if self.element != Element.NONE:
            boss_x = int(self.world_width - 200)
            boss_y = ground_level
            boss = Enemy(boss_x, boss_y, "boss", self.element, self.kingdom_index, self.world_width)
            self.enemies.append(boss)
