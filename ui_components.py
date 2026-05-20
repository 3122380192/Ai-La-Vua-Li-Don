from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QTimer
import random
import math

class HackerLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.original_text = text
        self.scramble_timer = QTimer()
        self.scramble_timer.timeout.connect(self.update_text)
        self.scramble_count = 0
        self.max_scrambles = 8
        
    def start_animation(self):
        self.scramble_count = 0
        self.scramble_timer.start(50)
    
    def update_text(self):
        if self.scramble_count < self.max_scrambles:
            scrambled = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(len(self.original_text)))
            self.setText(scrambled)
            self.scramble_count += 1
        else:
            self.setText(self.original_text)
            self.scramble_timer.stop()

class ScrollingLabel(QLabel):
    """Label with scrolling text effect"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.original_text = text
        self.scroll_pos = 0
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.scroll_text)
        self.scroll_timer.start(150)  # Scroll every 150ms
        
    def scroll_text(self):
        # Create scrolling effect
        display_text = self.original_text + "  "  # Add spacing
        self.scroll_pos = (self.scroll_pos + 1) % len(display_text)
        scrolled = display_text[self.scroll_pos:] + display_text[:self.scroll_pos]
        self.setText(scrolled[:len(self.original_text)])

class FireworkParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.5, 2.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.05)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05 # Gravity
        self.life -= self.decay
        return self.life > 0
