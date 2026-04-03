import math
import random
import pyglet

pyglet.options.dpi_scaling = "stretch"

from pyglet import shapes

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import constants, entities




class Explosion:
    def __init__(self, x, y, max_radius=80, duration=0.5):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.duration = duration
        self.elapsed = 0.0

    def draw(self):
        # Simple expanding/fading circle explosion
        progress = min(1.0, self.elapsed / self.duration)
        radius = self.max_radius * progress
        alpha = int(180 * (1.0 - progress))
        circle = shapes.Circle(self.x, self.y, radius, color=(255, 180, 60))
        circle.opacity = alpha
        circle.draw()

    @property
    def alive(self):
        return self.elapsed < self.duration

    def update(self, dt):
        self.elapsed += dt



class VibeProjectileApp(pyglet.window.Window):
    def set_next_tank_goal(self):
        # At the start of the app, the tank should move a random distance (500-5000 meters) towards the city,
        # but never come closer than 10,000 meters to the dome edge.
        min_dist_px = int(10000 / constants.METERS_PER_PIXEL)  # 10,000 meters minimum distance
        dome_left_edge = constants.CITY_X - int(constants.DOME_RADIUS_M / constants.METERS_PER_PIXEL)
        dome_right_edge = constants.CITY_X + int(constants.DOME_RADIUS_M / constants.METERS_PER_PIXEL)
        min_x = dome_left_edge + min_dist_px
        max_x = dome_right_edge - min_dist_px - self.tank.width
        min_x = max(min_x, 40)
        max_x = min(max_x, constants.WINDOW_WIDTH - self.tank.width - 40)
        min_move_m = 500
        max_move_m = 5000
        if getattr(self, "is_first_move", False):
            # First move: always towards the city, clamp so tank never comes closer than 10,000m to dome edge and never passes the dome
            direction = 1 if self.tank.x < constants.CITY_X else -1
            move_dist_m = random.randint(min_move_m, max_move_m)
            move_dist_px = int(move_dist_m / constants.METERS_PER_PIXEL)
            dome_left_edge = constants.CITY_X - int(constants.DOME_RADIUS_M / constants.METERS_PER_PIXEL)
            dome_min_x = dome_left_edge + int(10000 / constants.METERS_PER_PIXEL)
            # Clamp so tank never passes the dome's left edge plus min distance
            if direction == 1:
                max_goal = dome_min_x
                goal = min(self.tank.x + move_dist_px, max_goal)
            else:
                min_goal = dome_min_x
                goal = max(self.tank.x - move_dist_px, min_goal)
        else:
            direction = random.choice([-1, 1])
            move_dist_m = random.randint(min_move_m, max_move_m)
            move_dist_px = int(move_dist_m / constants.METERS_PER_PIXEL) * direction
            goal = self.tank.x + move_dist_px
            goal = max(min_x, min(goal, max_x))
            if abs(goal - self.tank.x) < int(min_move_m / constants.METERS_PER_PIXEL):
                # If too close, force a move in the other direction
                goal = self.tank.x - move_dist_px
                goal = max(min_x, min(goal, max_x))
        self.tank_move_goal = goal
        self.state = "moving"
        self.is_first_move = False

    # (Removed duplicate update method here; see below for the main update method)

    def trigger_spaceship_attack(self):
        # Spaceship flies from top of tallest building, drops bomb on tank, tank explodes
        tallest_building = max(self.city.buildings, key=lambda b: b.height)
        self.spaceship_x = tallest_building.x + tallest_building.width / 2
        self.spaceship_y = self.city.center_y + tallest_building.height + 120
        self.spaceship_target_x = self.tank.x + self.tank.width / 2
        self.spaceship_target_y = self.tank.y + self.tank.height / 2
        self.spaceship_bomb_y = self.spaceship_y
        self.spaceship_active = True
        self.spaceship_bomb_dropped = False
        self.spaceship_explosion_done = False
        self.state = "spaceship_attack"
        print(f"[DEBUG] Spaceship triggered: spaceship_active={self.spaceship_active}, spaceship_x={self.spaceship_x}, spaceship_y={self.spaceship_y}, spaceship_target_x={self.spaceship_target_x}, spaceship_target_y={self.spaceship_target_y}")

    def reset_spaceship_state(self):
        self.spaceship_active = False
        self.spaceship_bomb_dropped = False
        self.spaceship_explosion_done = False
        self.spaceship_x = None
        self.spaceship_y = None
        self.spaceship_target_x = None
        self.spaceship_target_y = None
        self.spaceship_bomb_y = None

    def reset_game(self):
        self.city = entities.City.create()
        self.dome = entities.Dome(self.city.center_x, self.city.center_y, constants.DOME_RADIUS_M)
        self.tank = entities.Tank()
        self.projectile = None
        self.explosions = []
        self.state = "ready"
        self.is_first_move = True
        self.tank_move_goal = self.tank.x
        self.set_next_tank_goal()
        self.close_button_radius = 22
        self.close_button_margin = 26
        self.last_fired_angle = None
        self.missile_result = None
        self.missile_shot = None
        self.missile = None
        self.game_over = False
        self.show_try_again = False
        self.goodbye = False
        self.missile_hit_streak = 0
        self.reset_spaceship_state()
    def fire_projectile(self):
        # Pick a random firing angle between 10 and 60 degrees
        angle_deg = random.uniform(10, 60)
        origin_x = self.tank.x + self.tank.width
        origin_y = self.tank.y + self.tank.height
        target_x = self.city.anti_missile_launcher_x
        target_y = self.city.anti_missile_launcher_y
        dx = target_x - origin_x
        dy = target_y - origin_y
        g = getattr(self, "gravity", constants.GRAVITY)
        angle_rad = math.radians(angle_deg)
        denom = dx * math.tan(angle_rad) - dy
        if denom <= 0:
            speed = constants.PROJECTILE_SPEED
        else:
            speed = math.sqrt((g * dx * dx) / (2 * (math.cos(angle_rad) ** 2) * denom))
            speed = max(speed, constants.PROJECTILE_SPEED)
        self.tank.angle_deg = angle_deg  # Always sync tank cannon angle
        self.last_fired_angle = angle_deg
        self.last_fired_speed = speed
        vx = math.cos(angle_rad) * speed
        vy = math.sin(angle_rad) * speed
        time_of_flight = (vy + math.sqrt(vy * vy + 2 * g * (origin_y - constants.GROUND_HEIGHT))) / g
        projected_range = vx * time_of_flight
        self.last_projected_range = projected_range
        self.projectile = entities.Projectile.create_from_tank(self.tank, angle_deg=angle_deg, speed=speed)
        self.state = "firing"
        self.missile_result = None
        self.missile_shot = None
        self.missile = None

    def __init__(self):
        super().__init__(constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT, caption="Vibe Projectile", resizable=False)
        pyglet.options["dpi_scaling"] = "stretch"
        self.scene_time = 0.0
        self.city = entities.City.create()
        self.dome = entities.Dome(self.city.center_x, self.city.center_y, constants.DOME_RADIUS_M)
        self.tank = entities.Tank()
        self.projectile = None
        self.explosions = []
        self.state = "ready"
        self.is_first_move = True
        self.tank_move_goal = self.tank.x
        self.set_next_tank_goal()

        self.close_button_radius = 22
        self.close_button_margin = 26

        self.title_label = pyglet.text.Label(
            "Vibe Projectile",
            x=28,
            y=constants.WINDOW_HEIGHT - 48,
            font_name="Marker Felt",
            font_size=38,
            color=(244, 230, 192, 255),
        )

    def on_draw(self):
        pyglet.gl.glClearColor(0.58, 0.82, 0.98, 1.0)
        self.clear()
        batch = pyglet.graphics.Batch()

        # Draw background, city, dome, tank, projectile, explosions using batch
        self.city.draw(batch, tank=self.tank, fade=0.0)
        self.dome.draw(batch)
        self.tank.draw(batch)
        if self.projectile is not None:
            self.is_first_move = True
        for explosion in self.explosions:
            explosion.draw()

        # Draw spaceship and bomb if active, using batch
        if getattr(self, "spaceship_active", False):
            ship_y = self.spaceship_y if self.spaceship_y is not None else 0
            ship_x = self.spaceship_x if self.spaceship_x is not None else 0
            pyglet.shapes.Rectangle(ship_x - 90, ship_y, 180, 70, color=(180, 180, 255), batch=batch)
            pyglet.shapes.Circle(ship_x, ship_y + 70, 55, color=(120, 120, 255), batch=batch)
            pyglet.shapes.Triangle(ship_x - 90, ship_y, ship_x - 130, ship_y - 40, ship_x - 50, ship_y + 20, color=(100, 100, 200), batch=batch)
            pyglet.shapes.Triangle(ship_x + 90, ship_y, ship_x + 130, ship_y - 40, ship_x + 50, ship_y + 20, color=(100, 100, 200), batch=batch)
            if self.spaceship_bomb_dropped and self.spaceship_bomb_y is not None:
                pyglet.shapes.Circle(self.spaceship_target_x, self.spaceship_bomb_y, 44, color=(60, 60, 60), batch=batch)
                pyglet.shapes.Circle(self.spaceship_target_x + 12, self.spaceship_bomb_y + 12, 16, color=(180, 180, 180), batch=batch)
            if self.spaceship_explosion_done:
                explosion = pyglet.shapes.Circle(self.spaceship_target_x, self.spaceship_target_y, 160, color=(255, 80, 40), batch=batch)
                explosion.opacity = 180
                explosion.draw()

        # Draw missile if present
        if hasattr(self, "missile") and self.missile is not None and self.missile.alive:
            self.missile.draw(batch)

        # Draw batch (all shapes)
        batch.draw()

        # Draw overlays and UI (labels, prompts, etc.) as before (not in batch)
        # ...existing code for overlays and UI...
        pyglet.gl.glClearColor(0.58, 0.82, 0.98, 1.0)
        self.clear()

        sun_pulse = 2.0 * math.sin(self.scene_time * 1.7)
        sun = shapes.Circle(1110, 600, 54 + sun_pulse, color=(253, 217, 88), batch=None)
        sun.opacity = 235
        sun.draw()
        for ray_dx, ray_dy in ((0, 82), (58, 58), (82, 0), (58, -58), (0, -82), (-58, -58), (-82, 0), (-58, 58)):
            shapes.Line(1110, 600, 1110 + ray_dx, 600 + ray_dy, color=(255, 204, 90), batch=None).draw()

        for mountain in (
            ((20, constants.GROUND_HEIGHT), (220, 418), (440, constants.GROUND_HEIGHT), (150, 190, 94)),
            ((250, constants.GROUND_HEIGHT), (510, 474), (780, constants.GROUND_HEIGHT), (118, 175, 92)),
            ((650, constants.GROUND_HEIGHT), (930, 436), (1210, constants.GROUND_HEIGHT), (138, 182, 104)),
        ):
            left_point, peak_point, right_point, color = mountain
            shapes.Triangle(*left_point, *peak_point, *right_point, color=color, batch=None).draw()
            shapes.Triangle(
                peak_point[0] - 34,
                peak_point[1] - 18,
                peak_point[0],
                peak_point[1] + 8,
                peak_point[0] + 28,
                peak_point[1] - 26,
                color=(248, 248, 242),
                batch=None,
            ).draw()

        for cloud_x, cloud_y in ((175, 615), (430, 565), (760, 630)):
            for offset_x, offset_y, radius in ((0, 0, 20), (25, 10, 24), (55, 0, 20)):
                cloud = shapes.Circle(cloud_x + offset_x, cloud_y + offset_y, radius, color=(250, 250, 246), batch=None)
                cloud.opacity = 220
                cloud.draw()

        bird_drift = 18 * math.sin(self.scene_time * 0.6)
        bird_lift = 4 * math.sin(self.scene_time * 1.2)
        for bird_x, bird_y, wing in ((220, 560, 12), (260, 585, 10), (815, 555, 11), (860, 585, 9)):
            bird_x += bird_drift
            bird_y += bird_lift
            shapes.Arc(bird_x, bird_y, wing, angle=0.0, start_angle=0.2, color=(52, 67, 78), batch=None).draw()
            shapes.Arc(bird_x + wing, bird_y, wing, angle=0.0, start_angle=0.2, color=(52, 67, 78), batch=None).draw()

        block_w = 40
        for i in range(0, constants.WINDOW_WIDTH, block_w):
            shade = 188 if (i // block_w) % 2 == 0 else 162
            shapes.Rectangle(i, 0, block_w, constants.GROUND_HEIGHT, color=(shade, 118, 38), batch=None).draw()
            shapes.Rectangle(i + 5, constants.GROUND_HEIGHT - 16, block_w - 10, 16, color=(shade + 22, 154, 78), batch=None).draw()
        for hill_x, hill_y, hill_r, color in ((150, 120, 60, (110, 176, 88)), (310, 115, 85, (124, 193, 92)), (870, 118, 70, (105, 172, 90))):
            hill = shapes.Circle(hill_x, hill_y, hill_r, color=color, batch=None)
            hill.opacity = 215
            hill.draw()

        for bush_x in (110, 370, 670, 980):
            for offset_x, radius in ((0, 18), (16, 24), (36, 20)):
                bush = shapes.Circle(bush_x + offset_x, constants.GROUND_HEIGHT + 10, radius, color=(66, 146, 52), batch=None)
                bush.opacity = 220
                bush.draw()

        # Do not fade out city if game over, so building explosions are visible
        fade = 0.0
        self.city.draw(None, tank=self.tank, fade=fade)
        self.dome.draw(None)
        self.tank.draw(None)
        if self.projectile is not None:
            self.projectile.draw(None)
        for explosion in self.explosions:
            explosion.draw()

        # Draw missile if present
        if hasattr(self, "missile") and self.missile is not None and self.missile.alive:
            self.missile.draw(None)
        # Draw missile shot line if missile has hit
        elif not getattr(self, "game_over", False) and getattr(self, "missile_shot", None) is not None:
            lx, ly = self.city.anti_missile_launcher_x, self.city.anti_missile_launcher_y
            px, py = self.missile_shot
            shapes.Line(lx, ly, px, py, color=(255, 0, 0), batch=None).draw()

        self.title_label.draw()

        # Draw the last fired angle, speed, and projected range as text
        if getattr(self, "last_fired_angle", None) is not None:
            info_label = pyglet.text.Label(
                f"Angle: {self.last_fired_angle:.1f}°  Speed: {getattr(self, 'last_fired_speed', 0):.1f}  Range: {getattr(self, 'last_projected_range', 0):,.0f} px",
                font_name="Arial",
                font_size=18,
                x=constants.WINDOW_WIDTH // 2,
                y=constants.WINDOW_HEIGHT - 60,
                anchor_x="center",
                anchor_y="center",
                color=(255, 255, 80, 255),
            )
            info_label.draw()

        # Draw a big nuclear cloud over the city if game over (draw last, on top)
        if getattr(self, "game_over", False):
            nuke = shapes.Circle(self.city.center_x, self.city.center_y + 60, 320, color=(255, 200, 60))
            nuke.opacity = 120
            nuke.draw()
            stem = shapes.Rectangle(self.city.center_x - 28, self.city.center_y, 56, 120, color=(220, 180, 80))
            stem.opacity = 90
            stem.draw()
            end_label = pyglet.text.Label(
                "the end",
                font_name="Arial Black",
                font_size=64,
                color=(255, 0, 0, 255),
                x=constants.WINDOW_WIDTH // 2,
                y=constants.WINDOW_HEIGHT // 2,
                anchor_x="center",
                anchor_y="center",
            )
            end_label.draw()
            # Debug overlay
            debug_label = pyglet.text.Label(
                "CITY IS HIT",
                font_name="Arial Black",
                font_size=36,
                color=(255, 0, 0, 255),
                x=constants.WINDOW_WIDTH // 2,
                y=constants.WINDOW_HEIGHT // 2 - 80,
                anchor_x="center",
                anchor_y="center",
            )
            debug_label.draw()
        # Show goodbye message and clear all overlays/text
        if getattr(self, "goodbye", False):
            pyglet.gl.glClearColor(1.0, 1.0, 1.0, 1.0)
            self.clear()
            goodbye_label = pyglet.text.Label(
                "good bye",
                font_name="Arial Black",
                font_size=64,
                color=(0, 0, 0, 255),
                x=constants.WINDOW_WIDTH // 2,
                y=constants.WINDOW_HEIGHT // 2,
                anchor_x="center",
                anchor_y="center",
            )
            goodbye_label.draw()
            return
        # Show try again prompt ON TOP of all overlays
        if getattr(self, "show_try_again", False):
            try_again_label = pyglet.text.Label(
                "Try again? (Y/N)",
                font_name="Arial Black",
                font_size=48,
                color=(0, 0, 0, 255),
                x=constants.WINDOW_WIDTH // 2,
                y=constants.WINDOW_HEIGHT // 2 - 180,
                anchor_x="center",
                anchor_y="center",
            )
            try_again_label.draw()

        # Show debug overlay if projectile was exploded by missile
        if getattr(self, "projectile_exploded_by_missile", False):
            missile_label = pyglet.text.Label(
                "PROJECTILE HIT BY MISSILE!",
                font_name="Arial Black",
                font_size=32,
                color=(0, 180, 255, 255),
                x=constants.WINDOW_WIDTH // 2,
                y=constants.WINDOW_HEIGHT // 2 - 120,
                anchor_x="center",
                anchor_y="center",
            )
            missile_label.draw()
            # Reset after showing once
            self.projectile_exploded_by_missile = False

        self.title_label.draw()

        # Draw the last fired angle, speed, and projected range as text
        if getattr(self, "last_fired_angle", None) is not None:
            info_label = pyglet.text.Label(
                f"Angle: {self.last_fired_angle:.1f}°  Speed: {getattr(self, 'last_fired_speed', 0):.1f}  Range: {getattr(self, 'last_projected_range', 0):,.0f} px",
                font_name="Arial",
                font_size=18,
                x=constants.WINDOW_WIDTH // 2,
                y=constants.WINDOW_HEIGHT - 60,
                anchor_x="center",
                anchor_y="center",
                color=(255, 255, 80, 255),
            )
            info_label.draw()

        ruler_y = 40
        ruler_x0 = 0
        ruler_len = constants.WINDOW_WIDTH
        ruler_end = ruler_x0 + ruler_len
        shapes.Rectangle(ruler_x0, ruler_y - 4, ruler_len, 8, color=(240, 240, 240), batch=None).draw()
        max_m = int(constants.WINDOW_WIDTH * constants.METERS_PER_PIXEL)
        steps = int(max_m / constants.RULER_STEP_M)
        for i in range(steps + 1):
            px = ruler_x0 + i * (ruler_len / steps)
            tick_h = 22 if i % (constants.RULER_MAJOR_STEP_M // constants.RULER_STEP_M) == 0 else 12
            shapes.Line(px, ruler_y - tick_h/2, px, ruler_y + tick_h/2, color=(0, 0, 0), batch=None).draw()
            if i % (constants.RULER_MAJOR_STEP_M // constants.RULER_STEP_M) == 0:
                txt = pyglet.text.Label(
                    f"{i * constants.RULER_STEP_M:,} m",
                    x=px,
                    y=ruler_y + tick_h/2 + 4,
                    anchor_x="center",
                    anchor_y="bottom",
                    font_size=11,
                    color=(84, 57, 28, 255),
                )
                txt.draw()

        for special_x, label_text, label_color in (
            (constants.TANK_X, f"Tank {constants.TANK_X_M:,} m", (250, 222, 140, 255)),
            (constants.CITY_X, f"City {constants.CITY_X_M:,} m", (183, 214, 255, 255)),
        ):
            guide = shapes.Line(special_x, constants.GROUND_HEIGHT + 4, special_x, ruler_y + 18, color=label_color[:3], batch=None)
            guide.draw()
            label = pyglet.text.Label(
                label_text,
                x=min(max(70, special_x + 6), constants.WINDOW_WIDTH - 90),
                y=ruler_y + 20,
                anchor_x="left",
                anchor_y="bottom",
                font_size=13,
                color=label_color,
            )
            label.draw()

        close_center_x = constants.WINDOW_WIDTH - self.close_button_margin - self.close_button_radius
        close_center_y = constants.WINDOW_HEIGHT - self.close_button_margin - self.close_button_radius
        btn = shapes.Circle(close_center_x, close_center_y, self.close_button_radius, color=(196, 48, 48), batch=None)
        btn.draw()
        shapes.Line(close_center_x - 9, close_center_y - 9, close_center_x + 9, close_center_y + 9, color=(255, 255, 255), batch=None).draw()
        shapes.Line(close_center_x - 9, close_center_y + 9, close_center_x + 9, close_center_y - 9, color=(255, 255, 255), batch=None).draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            close_center_x = constants.WINDOW_WIDTH - self.close_button_margin - self.close_button_radius
            close_center_y = constants.WINDOW_HEIGHT - self.close_button_margin - self.close_button_radius
            if math.hypot(x - close_center_x, y - close_center_y) <= self.close_button_radius:
                self.close()

    def on_key_press(self, symbol, modifiers):
        if getattr(self, "show_try_again", False):
            if symbol == pyglet.window.key.Y:
                self.reset_game()
            elif symbol == pyglet.window.key.N:
                self.goodbye = True
                self.show_try_again = False
            return
        if getattr(self, "goodbye", False):
            return
        if getattr(self, "spaceship_active", False):
            print(f"[DEBUG] Drawing spaceship (second pass): spaceship_active={self.spaceship_active}, spaceship_x={self.spaceship_x}, spaceship_y={self.spaceship_y}, bomb_dropped={self.spaceship_bomb_dropped}, bomb_y={self.spaceship_bomb_y}")
            return
        if symbol == pyglet.window.key.SPACE:
            if self.projectile is None or not self.projectile.alive:
                angle_deg, speed = entities.solve_launch_parameters(
                    self.tank.x + self.tank.width,
                    self.tank.y + self.tank.height,
                    self.city.anti_missile_launcher_x,
                    self.city.anti_missile_launcher_y,
                )
                self.tank.angle_deg = angle_deg
                self.projectile = entities.Projectile.create_from_tank(self.tank, angle_deg=angle_deg, speed=speed)

    def update(self, dt):
        # Robust fallback: ensure missile_hit_streak always exists
        if not hasattr(self, "missile_hit_streak") or self.missile_hit_streak is None:
            self.missile_hit_streak = 0
        self.scene_time += dt

        # Spaceship attack logic
        if getattr(self, "spaceship_active", False):
            print(f"[DEBUG] update: spaceship_active={self.spaceship_active}, spaceship_x={self.spaceship_x}, spaceship_y={self.spaceship_y}, bomb_dropped={self.spaceship_bomb_dropped}, bomb_y={self.spaceship_bomb_y}")
            # Move spaceship horizontally and vertically toward above the tank
            speed = 320 * dt
            dx = self.spaceship_target_x - self.spaceship_x
            dy = (self.spaceship_target_y + 120) - self.spaceship_y
            distance = math.hypot(dx, dy)
            if distance > speed:
                # Move spaceship toward target position
                self.spaceship_x += speed * dx / distance
                self.spaceship_y += speed * dy / distance
            elif not self.spaceship_bomb_dropped:
                # Arrived above tank, drop bomb
                self.spaceship_x = self.spaceship_target_x
                self.spaceship_y = self.spaceship_target_y + 120
                self.spaceship_bomb_dropped = True
                self.spaceship_bomb_y = self.spaceship_y
            elif self.spaceship_bomb_dropped and not self.spaceship_explosion_done:
                # Drop bomb
                bomb_speed = 400 * dt
                if self.spaceship_bomb_y > self.spaceship_target_y:
                    self.spaceship_bomb_y -= bomb_speed
                else:
                    self.spaceship_bomb_y = self.spaceship_target_y
                    self.spaceship_explosion_done = True
                    # Tank explodes
                    self.explosions.append(Explosion(self.spaceship_target_x, self.spaceship_target_y, max_radius=120, duration=1.5))
                    self.state = "spaceship_explosion"
                    self.tank.x = -1000  # Hide tank
            elif self.spaceship_explosion_done:
                # After short delay, show try again
                if not hasattr(self, "spaceship_explosion_timer"):
                    self.spaceship_explosion_timer = 0.0
                self.spaceship_explosion_timer += dt
                if self.spaceship_explosion_timer > 1.5:
                    self.show_try_again = True
                    self.spaceship_active = False
                    self.spaceship_explosion_timer = 0.0
            return

        # Tank movement
        if self.state == "moving":
            movement_step = 120 * dt
            distance_to_goal = self.tank_move_goal - self.tank.x
            if abs(distance_to_goal) <= movement_step:
                self.tank.x = self.tank_move_goal
                self.state = "ready"
            elif distance_to_goal > 0:
                self.tank.x += movement_step
            else:
                self.tank.x -= movement_step

        # Fire and projectile logic
        if getattr(self, "game_over", False):
            return

        # Prevent firing new projectile if spaceship event is pending
        if getattr(self, "spaceship_active", False):
            # Spaceship event takes priority, block all firing/game logic
            return

        if self.state in ("ready", "prepare") and (self.projectile is None or not self.projectile.alive):
            self.fire_projectile()
            self.state = "firing"

        if self.projectile is not None and self.projectile.alive:
            self.projectile.update(dt)
            # dome collision
            print(f"[DEBUG] Checking dome collision: projectile=({self.projectile.x:.2f},{self.projectile.y:.2f}), dome=({self.dome.center_x:.2f},{self.dome.center_y:.2f})")
            if self.missile_result is None and self.projectile.hits_dome(self.dome):
                print("[DEBUG] Anti-missile launcher firing at projectile!")
                # Spawn missile animation
                self.missile = entities.Missile(
                    self.city.anti_missile_launcher_x,
                    self.city.anti_missile_launcher_y,
                    self.projectile.x,
                    self.projectile.y,
                    speed=600
                )
                # 95% chance to hit
                if random.random() < 0.95:
                    self.missile_result = "hit"
                    # Immediately destroy projectile if missile hits
                    self.projectile.alive = False
                    self.projectile_exploded_by_missile = True
                    print("Missile HIT projectile, projectile explodes in air! City is safe.")
                    if getattr(self, "last_missile_result", None) == "hit" or getattr(self, "last_missile_result", None) is None:
                        self.missile_hit_streak += 1
                    else:
                        self.missile_hit_streak = 1
                    print(f"Hit = {self.missile_hit_streak}")
                    if self.missile_hit_streak == 4:
                        print("[DEBUG] Spaceship event triggered after 4 consecutive missile hits!")
                        self.trigger_spaceship_attack()
                        self.missile_hit_streak = 0
                        self.last_missile_result = None
                        return  # Interrupt further logic so spaceship event starts immediately
                else:
                    self.missile_result = "miss"
                    print("Missile missed projectile, projectile continues.")
                    self.missile_hit_streak = 0
                self.last_missile_result = self.missile_result

            # If projectile lands (hits ground), city explodes and game ends, but only if missile missed
            if self.projectile.alive:
                if (getattr(self, "missile_result", None) in (None, "fail", "miss")) and self.projectile.y <= constants.GROUND_HEIGHT:
                    print(f"[DEBUG] Projectile hit ground at y={self.projectile.y}, city explodes!")
                    self.projectile.y = constants.GROUND_HEIGHT  # Clamp to ground
                    self.projectile.alive = False
                    self.game_over = True
                    self.show_try_again = True
                    self.goodbye = False
                    print("City explosion triggered: projectile hit the ground!")
                    print("city is hit")
                    for b in self.city.buildings:
                        bx = b.x + b.width / 2
                        by = b.y + b.height / 2
                        self.explosions.append(Explosion(bx, by, max_radius=60, duration=1.2))
                    self.explosions.append(Explosion(self.city.center_x, self.city.center_y, max_radius=260, duration=2.5))
                elif getattr(self, "missile_result", None) in ("hit", "safe"):
                    self.projectile.alive = False
                    print("Missile intercepted projectile. City is safe.")
                    self.laser_shot = None
                    self.laser_result = None
                # Show 'we are safe' message if missile hit
                if getattr(self, "missile_result", None) in ("hit", "safe") and not getattr(self, "game_over", False):
                    safe_label = pyglet.text.Label(
                        "we are safe",
                        font_name="Arial Black",
                        font_size=48,
                        color=(0, 180, 255, 255),
                        x=constants.WINDOW_WIDTH // 2,
                        y=constants.WINDOW_HEIGHT // 2 - 120,
                        anchor_x="center",
                        anchor_y="center",
                    )
                    safe_label.draw()
        # Show try again prompt
        if getattr(self, "show_try_again", False):
            try_again_label = pyglet.text.Label(
                "Try again? (Y/N)",
                font_name="Arial Black",
                font_size=48,
                color=(0, 0, 0, 255),
                x=constants.WINDOW_WIDTH // 2,
                y=constants.WINDOW_HEIGHT // 2 - 180,
                anchor_x="center",
                anchor_y="center",
            )
            try_again_label.draw()
        # Show goodbye message
        if getattr(self, "goodbye", False):
            goodbye_label = pyglet.text.Label(
                "good bye",
                font_name="Arial Black",
                font_size=64,
                color=(0, 0, 0, 255),
                x=constants.WINDOW_WIDTH // 2,
                y=constants.WINDOW_HEIGHT // 2,
                anchor_x="center",
                anchor_y="center",
            )
            goodbye_label.draw()

        # Update missile if present
        if hasattr(self, "missile") and self.missile is not None and self.missile.alive:
            self.missile.update(dt)
            # Check if missile reached projectile
            if not self.missile.alive:
                if self.missile_result == "hit":
                    # Missile hits projectile in air
                    print("missile HIT projectile, projectile explodes in air!")
                    self.missile_result = "safe"
                elif self.missile_result == "miss":
                    # Missile missed projectile
                    self.missile_shot = (self.projectile.x, self.projectile.y)
                    # Do NOT set projectile.alive = False, do NOT explode
                    print("missile missed projectile, projectile continues.")

        # Cleanup finished explosions
        self.explosions = [e for e in self.explosions if e.alive]
        for explosion in self.explosions:
            explosion.update(dt)

        # Erase missile if city is safe and projectile is done
        if getattr(self, "missile_result", None) == "safe" and (self.projectile is None or not self.projectile.alive):
            self.missile_shot = None
            self.missile_result = None
            self.missile = None
            # Do NOT reset missile_hit_streak here; only reset on a true miss or spaceship event

        # if projectile is done, prepare next move
        if self.projectile is None or not self.projectile.alive:
            if self.state == "firing":
                # Only continue if city is safe
                if not getattr(self, "game_over", False):
                    self.state = "ready"
                    self.set_next_tank_goal()


def main():
    window = VibeProjectileApp()
    pyglet.clock.schedule_interval(window.update, 1/60.0)
    pyglet.app.run()


if __name__ == "__main__":
    main()
