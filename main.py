# TEE PELI TÄHÄN
import pygame
import os
import random as rnd
import numpy as np

click_values = {    'Menu': 0,          # Initialisoidaan painikkeita varten sanakirja
                    'Start Game': 1,
                    'Help': 2,
                    'Exit Game': 3}

screen_width = 640  # Peli-ikkunan dimensiot
screen_height = 480

file_path_prefix = 'src/'   # Textuuritiedostoja varten tiedostopolun alku, tämä tulee muuttaa tyhjäksi,
                            # jos ohjelma suoritetaan kansiossa src
debug = False   # Debug flag, jos True, pelissä näytetään eräitä debug-ominaisuuksia ja tiettyjä
                # tietoja tulostetaan komentoriville

class Game:
    def __init__(self):
        pygame.init()
        
        # Alustetaan Game-luokan globaalit muuttujat
        self.mouse_pos = (0,0)
        self.click_pos = (-1,-1)
        self.clickable = True   # Käytetään estämään useat klikkaukset ennen painikkeen nostamista
        self.current_state = 0  # Merkkaa missä pelitilassa ollaan
        self.timer = pygame.time.Clock()
        self.velocity = np.array([0,0])
        self.speed = 2
        self.quitting_safeguard = False # Varmistetaan pelaajalta haluaako tämä varmasti poistua pelistä
        self.ammunition_shot = False 

        self.projectiles = []   # Eri olioiden piirtämistä ja käsittelyä varten
        self.monsters = []
        self.coins = []
        self.door = []

        self.font = pygame.font.SysFont('Arial', 24)    # Alustetaan muutama fontti
        self.h1 = pygame.font.SysFont('Arial', 32)
        self.p = pygame.font.SysFont('Arial', 18)
        
        self.screen = pygame.display.set_mode((screen_width, screen_height))

        pygame.display.set_caption('Game')
        self.game_loop()
    
    def load_resources(self):
        self.textures = []
        for resource in ['hirvio', 'kolikko', 'ovi', 'robo']:
            self.textures.append(pygame.image.load(file_path_prefix + resource + '.png'))

    def game_loop(self):    # Peli looppi
        self.load_resources()
        while True:
            self.event_handler()    # Käsittele tapahtumat
            self.update_display()   # Päivitä näyttö
            self.reset_click_pos()  # Resetoi mahdollisen klikkauksen paikka
    
    def event_handler(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                exit()
            if e.type == pygame.MOUSEMOTION:
                self.mouse_pos = e.pos
            if e.type == pygame.MOUSEBUTTONDOWN and self.clickable:
                self.click_pos = e.pos
                self.clickable = False
            if e.type == pygame.MOUSEBUTTONUP:
                self.click_pos = (-1,-1)
                self.clickable = True
            if e.type == pygame.KEYDOWN:
                spd = self.speed
                if e.key == pygame.K_w:
                    self.velocity += np.array([0,-spd])
                if e.key == pygame.K_d:
                    self.velocity += np.array([spd,0])
                if e.key == pygame.K_s:
                    self.velocity += np.array([0,spd])
                if e.key == pygame.K_a:
                    self.velocity += np.array([-spd,0])
                if e.key == pygame.K_SPACE and not self.ammunition_shot and self.player.mp >= 10:
                    # Määritä pelaajan ampumissuunta ja ammu
                    vector = np.array([ self.mouse_pos[0]- (self.player.pos[0] + self.player.texture.get_width()/2) ,
                                        self.mouse_pos[1]- (self.player.pos[1] + self.player.texture.get_height()/2)])
                    norm = np.linalg.norm(vector)
                    direction_vector = vector / norm
                    self.shoot(direction_vector)
                    self.ammunition_shot = True
                if debug: print(self.velocity)
            if e.type == pygame.KEYUP:
                spd = -self.speed
                if e.key == pygame.K_w:
                    self.velocity += np.array([0,-spd])
                if e.key == pygame.K_d:
                    self.velocity += np.array([spd,0])
                if e.key == pygame.K_s:
                    self.velocity += np.array([0,spd])
                if e.key == pygame.K_a:
                    self.velocity += np.array([-spd,0])
                if e.key == pygame.K_SPACE:
                    self.ammunition_shot = False

    def shoot(self,direction):
        player_w = self.player.texture.get_width()/2
        player_h = self.player.texture.get_height()/2
        self.player.mp -= 10
        self.projectiles.append(Ammunition(self.player.pos+np.array([player_w,player_h]),direction))

    def reset_click_pos(self):
        self.click_pos = (-1,-1) # Siirtää klikkausposition näytön ulkopuolelle
                                 # Jossa ei toivottavasti ole mitään klikattavaa

    def set_state(self, state_definition):
        self.current_state = click_values[state_definition] # Vaihda pelin pelitilaa
        if self.current_state == 1:
            self.init_game()            

    def init_game(self):    # Alusta pelitila
        self.player = Player(self.textures[3])
        self.door = []
        self.coins = []

    def update_display(self):
        self.screen.fill((109, 66, 128))

        if self.current_state == 0:     # MAIN MENU
            # MAIN MENU BUTTONS
            # Piirrä menupainikkeet
            init_height = 270
            start_game_btn = Btn(self.screen, 200, 50, (30,init_height), 'Start Game', self)
            start_game_btn.draw_btn(self.mouse_pos,self.click_pos)
            help_btn = Btn(self.screen, 200, 50, (30,init_height+60), 'Help', self)
            help_btn.draw_btn(self.mouse_pos,self.click_pos)
            exit_game_btn = Btn(self.screen, 200, 50, (30,init_height+120), 'Exit Game', self)
            exit_game_btn.draw_btn(self.mouse_pos,self.click_pos)

            # Piirrä painikkeiden hover-efektit
            buttons = [start_game_btn, help_btn, exit_game_btn]
            for button in buttons:
                if button.hover(self.click_pos):
                    if debug: print('Clicked',button.annotation)
                    self.set_state(button.annotation)
        elif self.current_state == 1:   # GAME MODE
            # Pelitila
            if (self.player.get_score_count() < 30 or not self.player.has_won) and self.player.hp > 0:
                # Jos itse peli on käynnissä, piirrä pelin olennaiset osat näytölle
                self.game_mode_display()
            elif self.player.hp <= 0:
                # Jos peli hävittiin, piirrä Game over -ruutu
                pygame.draw.rect(self.screen, (0, 0, 0),
                                (150,100,
                                self.screen.get_width()-300,
                                self.screen.get_height()-200 ),
                                border_radius=15)
                youwin = [  self.h1.render('GAME OVER', True, (255,0,0)),
                            self.h1.render('You have lost the game..', True, (255,0,0))]
                init_height = 120
                for text in youwin:
                    self.screen.blit(text, (170, init_height+40*youwin.index(text)))
                button_x = 150 + (self.screen.get_width()-300-200)/2
                return_to_menu_btn = Btn(self.screen, 200, 50, (button_x,screen_height-200), 'Return to Main Menu', self)
                return_to_menu_btn.draw_btn(self.mouse_pos,self.click_pos)
                if return_to_menu_btn.hover(self.click_pos):
                    if debug: print('Clicked',return_to_menu_btn.annotation)
                    self.current_state = 0
            else:
                # Jos peli voitettiin, piirrä Congratulations-ruutu
                pygame.draw.rect(self.screen, (255, 89, 128),
                                (150,100,
                                self.screen.get_width()-300,
                                self.screen.get_height()-200 ),
                                border_radius=15)
                youwin = [  self.h1.render('Congratulations!', True, (0,0,0)),
                            self.h1.render('You have won the game!', True, (0,0,0))]
                init_height = 120
                for text in youwin:
                    self.screen.blit(text, (170, init_height+40*youwin.index(text)))
                button_x = 150 + (self.screen.get_width()-300-200)/2
                return_to_menu_btn = Btn(self.screen, 200, 50, (button_x,screen_height-200), 'Return to Main Menu', self)
                return_to_menu_btn.draw_btn(self.mouse_pos,self.click_pos)
                if return_to_menu_btn.hover(self.click_pos):
                    if debug: print('Clicked',return_to_menu_btn.annotation)
                    self.current_state = 0

        elif self.current_state == 2:   # HELP MODE
            # Ohjeet pelin pelaamista varten
            scrn_height = self.screen.get_height()
            left_placement = 200
            heading = 'Objective'
            help_label = self.h1.render(heading, True, (255,255,255))
            self.screen.blit(help_label, (left_placement, 30))
            paragraphs = [  'Your objective is to defeat the waves of monsters that are',
                            'trying to kill you.',
                            'Replenish your mana (your shots) by collecting ammunition',
                            '(coins).',
                            'Shoot at enemies by aiming with your mouse cursor and',
                            'pressing the spacebar.',
                            'If you run out of HP, the game is over.',
                            'You have won, when a door appears and you',
                            'enter said door.']
            height = 70
            for paragraph in paragraphs:
                objective_text = self.p.render(paragraph, True, (255,255,255))
                self.screen.blit(objective_text, (left_placement, height))
                height += 20

            return_to_menu_btn = Btn(self.screen, 200, 50, (30,scrn_height-100), 'Return to Main Menu', self)
            return_to_menu_btn.draw_btn(self.mouse_pos,self.click_pos)
            if return_to_menu_btn.hover(self.click_pos):
                if debug: print('Clicked',return_to_menu_btn.annotation)
                self.current_state = 0
        elif self.current_state == 3:   # EXIT GAME
            init_height = 270

            text = 'Are sure you want to quit?'
            label = self.h1.render(text, True, (255,255,255))
            self.screen.blit(label, (30, init_height-40))

            yes_btn = Btn(self.screen, 200, 50, (30,init_height), 'Yes', self)
            yes_btn.draw_btn(self.mouse_pos,self.click_pos)
            no_btn = Btn(self.screen, 200, 50, (30,init_height+60), 'No', self)
            no_btn.draw_btn(self.mouse_pos,self.click_pos)
            if yes_btn.hover(self.click_pos):
                if debug: print('Clicked',yes_btn.annotation)
                self.quitting_safeguard = True
            elif no_btn.hover(self.click_pos):
                if debug: print('Clicked',no_btn.annotation)
                self.set_state('Menu')
            if self.quitting_safeguard:
                pygame.time.delay(100)
                quit()

        pygame.display.flip()
        self.timer.tick(60)

    def game_mode_display(self):
        # HEALTH AND MANA BARS
            bar_height = 400

            # Jos vaaditut saavutukset saavutettu, piirrä ovi
            if self.player.get_score_count() >= 30:
                if len(self.door) == 0:
                    self.door.append(Door(self.textures[2]))
                    self.monsters = []
                else:
                    door = self.door[0]
                    door.draw_door(self.screen)
                    dw = door.texture.get_width()
                    dh = door.texture.get_height()
                    dx,dy = door.pos[0]+dw,door.pos[1]+dh
                    pw = self.player.texture.get_width()
                    ph = 65
                    px,py = self.player.pos[0]+pw/2,self.player.pos[1]+ph/2
                    if self.bbcd_rect_to_rect(dx,dy,dw,dh,px,py,pw,ph):
                        self.player.has_won = True

            # Satunnaistettu kolikkojen luominen
            if len(self.coins) < 10 and rnd.randint(1,150) == 1 and self.player.mp < 100:
                self.coins.append(Coin(self.textures[1]))
            
            # Käsittele kolikoiden olennaiset ominaisuudet
            # Piirrä kolikot sekä testaa niiden hitboxit pelaajan kanssa 
            for coin in self.coins:
                coin.draw_coin(self.screen)
                cw = coin.texture.get_width()
                ch = coin.texture.get_height()
                cx,cy = coin.pos[0]+cw,coin.pos[1]+ch
                pw = self.player.texture.get_width()
                ph = 65
                px,py = self.player.pos[0]+pw/2,self.player.pos[1]+ph/2
                if self.bbcd_rect_to_rect(cx, cy, cw, ch, px, py, pw, ph):
                    self.coins.pop(self.coins.index(coin))
                    if self.player.mp < 100: self.player.mp += 10
            
            # Piirrä ammukset, liikuta niitä ja testaa niiden hitbox vihollisten kanssa
            for proj in self.projectiles:
                proj.draw_ammunition(self.screen)
                proj.move()
                ox,oy = proj.pos[0],proj.pos[1]
                ow = proj.width/2
                sw = self.screen.get_width()
                for monster in self.monsters:
                    mx = monster.pos[0]
                    my = monster.pos[1]
                    mw = monster.texture.get_width()
                    mh = monster.texture.get_height()
                    if self.bbcd_square_to_rect(ox,oy,np.sqrt(2*ow),mx,my,mw,mh):
                        self.monsters.pop(self.monsters.index(monster))
                        self.projectiles.pop(self.projectiles.index(proj))
                        self.player.defeat_monster()
                        break
                if ox <= -ow or ox >= sw + ow or oy <= -ow or oy >= bar_height-20+ow:
                    self.projectiles.pop(self.projectiles.index(proj))
            # Siirrä sekä piirrä pelaaja
            self.player.move(self.velocity)
            self.player.draw_player(self.screen)

            # Satunnaistettu hirvioiden luominen
            if rnd.randint(1,60) == 1 and len(self.monsters) < 3 and self.player.get_score_count() < 30:
                self.monsters.append(Monster(self.textures[0], self.player.pos))
            # Käsittele hirviöiden liike, piirto ja testaa niiden hitbox pelaajan kanssa
            for monster in self.monsters:
                monster.draw_monster(self.screen)
                monster.move(self.player.pos)
                mw = monster.texture.get_width()
                mh = monster.texture.get_height()
                mx,my = monster.pos[0]+mw,monster.pos[1]+mh
                pw = self.player.texture.get_width()
                ph = 65
                px,py = self.player.pos[0]+pw/2,self.player.pos[1]+ph/2
                if self.bbcd_rect_to_rect(mx, my, mw, mh, px, py, pw, ph):
                    if not self.player.invincible:  # Tarkasta onko pelaaja "kuolematon"
                        self.player.invincible = True
                        self.player.invincibility_timer = pygame.time.get_ticks()
                        if self.player.hp >= 10: self.player.hp -= 10
            # Jos 800 ms kulunut pelaajan kuolemattomuuden alusta, poista kuolemattomuus
            if pygame.time.get_ticks() - self.player.invincibility_timer >= 800:
                self.player.invincible = False

            # Piirrä käyttöliittymän tausta
            pygame.draw.rect(self.screen, (40,40,40),
                             (0,bar_height - 20,
                             self.screen.get_width(),
                             self.screen.get_height()+(bar_height-20) )
                            )
            # Piirrä elämä- ja manamittarit
            health_bar = Bars(self.screen, 'HP', self)
            health_bar.draw_bar(200, 40,
                                (20,bar_height),
                                (255, 54, 74),
                                (255,0,0),
                                self.player.hp/self.player.max_hp
                               )
            mana_bar = Bars(self.screen, 'MP', self)
            mana_bar.draw_bar(200, 40,
                              (260,bar_height),
                              (54, 101, 255),
                              (0,0,255),
                              self.player.mp/self.player.max_mp
                             )
            # Kirjaa pistemäärä ruudulle
            label = self.p.render('Score: '+ str(self.player.get_score_count()), True, (0,255,0))
            self.screen.blit(label, (screen_width - 120, bar_height))

    # Bounding Box Collision Detection
    # Testaa joko neliön ja suorakaiteen tai kahden suorakaiteen päällekkäisyys
    def bbcd_square_to_rect(self, r1_x, r1_y, r1_s, r2_x, r2_y, r2_w, r2_h):
        return (r1_x >= r2_x-r1_s/2 and r1_x <= r2_x+r1_s/2+r2_w) and (r1_y >= r2_y-r1_s/2 and r1_y <= r2_y+r1_s/2+r2_w)
    
    def bbcd_rect_to_rect(self, r1_x, r1_y, r1_w, r1_h, r2_x, r2_y, r2_w, r2_h):
        return (r1_x >= r2_x-r1_w/2 and r1_x <= r2_x+r1_w/2+r2_w) and (r1_y >= r2_y-r1_h/2 and r1_y <= r2_y+r1_h/2+r2_w)

class Door:
    def __init__(self, texture):
        self.texture = texture
        self.width = self.texture.get_width()
        self.height = self.texture.get_height()
        self.pos = self.shuffle_pos()

    def shuffle_pos(self):
        return np.array([rnd.randint(10,screen_width-10-self.width),rnd.randint(0,380-self.height)])
    
    def draw_door(self, screen):
        screen.blit(self.texture, self.pos)
        if debug:
            hitbox_color = pygame.Color(0,0,255)
            hitbox_w = self.texture.get_width()
            hitbox_y = self.texture.get_height()
            hitbox = pygame.Surface((hitbox_w, hitbox_y))
            hitbox.set_alpha(100)
            hitbox.fill(hitbox_color)
            screen.blit(hitbox, self.pos)

class Coin:
    def __init__(self, texture):
        self.texture = texture
        self.width = self.texture.get_width()
        self.height = self.texture.get_height()
        self.pos = self.shuffle_pos()

    def shuffle_pos(self):
        return np.array([rnd.randint(10,screen_width-10-self.width),rnd.randint(0,380-self.height)])
    
    def draw_coin(self, screen):
        screen.blit(self.texture, self.pos)
        if debug:
            hitbox_color = pygame.Color(0,0,255)
            hitbox_w = self.texture.get_width()
            hitbox_y = self.texture.get_height()
            hitbox = pygame.Surface((hitbox_w, hitbox_y))
            hitbox.set_alpha(100)
            hitbox.fill(hitbox_color)
            screen.blit(hitbox, self.pos)

class Ammunition:
    def __init__(self, init_pos, direction: np.array):
        self.pos = init_pos
        self.direction = direction
        self.speed = 10
        self.width = 20

    def move(self):
        v = self.speed*self.direction
        unit_dir = np.rint(v)
        self.pos += unit_dir

    def draw_ammunition(self, screen):
        pygame.draw.rect(   screen,
                            (255,0,0),
                            (self.pos[0],self.pos[1],self.width,self.width),
                            border_radius=10)

class Player:
    def __init__(self, texture):
        self.max_hp = 100
        self.hp = self.max_hp
        self.max_mp = 100
        self.mp = self.max_mp
        self.texture = texture
        self.pos = self.start_pos()
        self.__defeated_monsters = 0
        self.invincible = False
        self.invincibility_timer = 0
        self.has_won = False

    def start_pos(self):
        return np.array([   rnd.randint(1,screen_width-self.texture.get_width()),
                            rnd.randint(0,380-self.texture.get_height())])

    def defeat_monster(self):
        self.__defeated_monsters += 1
    
    def get_score_count(self):
        return self.__defeated_monsters

    def move(self, vel):
        newpos = self.pos + vel
        scr_w = screen_width
        scr_h = 380
        plr_w = self.texture.get_width()
        plr_h = self.texture.get_height()
        if newpos[0] <= scr_w-plr_w and newpos[0] >= 0 and newpos[1] >= 0 and newpos[1] <= scr_h-plr_h:
            self.pos = newpos

    def draw_player(self, screen):
        screen.blit(self.texture, self.pos)
        if debug:
            hitbox_color = pygame.Color(0,0,255)
            hitbox_w = self.texture.get_width()
            hitbox_y = 65
            hitbox = pygame.Surface((hitbox_w, hitbox_y))
            hitbox.set_alpha(100)
            hitbox.fill(hitbox_color)
            screen.blit(hitbox, self.pos)

class Monster:
    def __init__(self, texture, player_pos_at_spawn):
        self.status = 'dead'
        self.player_pos_at_spawn = player_pos_at_spawn
        self.texture = texture
        self.pos = np.array(self.start_pos())
        self.speed = 2

    def start_pos(self):
        w = self.texture.get_width()
        h = self.texture.get_height()
        side = rnd.randint(1,4)
        if side == 1:
            pos = np.array([rnd.randint(-w,screen_width+w),340+h])
        elif side == 2:
            pos = np.array([-w,rnd.randint(-h,340+h)])
        elif side == 3:
            pos = np.array([rnd.randint(-w,screen_width+w),-h])
        elif side == 4:
            pos = np.array([screen_width+w,rnd.randint(-h,340+h)])
        return pos

    def move(self, playerpos):
        v = playerpos-self.pos
        if np.linalg.norm(v) == 0:
            v = 1
        else:
            v = v / np.linalg.norm(v)
        unit_v = np.rint(v).astype(int)
        self.pos += unit_v

    def draw_monster(self, screen):
        screen.blit(self.texture, self.pos)
        if debug:
            hitbox_color = pygame.Color(0,0,255)
            hitbox_w = self.texture.get_width()
            hitbox_y = self.texture.get_height()
            hitbox = pygame.Surface((hitbox_w, hitbox_y))
            hitbox.set_alpha(100)
            hitbox.fill(hitbox_color)
            screen.blit(hitbox, self.pos)

class Bars:
    def __init__(self, screen, annotation, game):
        self.screen = screen
        self.annotation = annotation
        self.game = game

    # Piirrä mittari
    def draw_bar(self, width, height, pos, accent_c, c, depletion):
        dims = (pos[0],pos[1],width,height)
        indims = [dims[0]+5,dims[1]+5,dims[2]-10,dims[3]-10]
        pygame.draw.rect(self.screen, accent_c, dims,                   # Pohja
                         border_bottom_right_radius=int(height/2),
                         border_top_left_radius=int(height/2) )
        pygame.draw.rect(self.screen, (0,0,0), indims,                  # Musta tausta
                         border_bottom_right_radius=int((height-10)/2),
                         border_top_left_radius=int((height-10)/2) )
        pygame.draw.rect(self.screen, c,                                # Skaalautuva indikaattori
                         [indims[0],indims[1],indims[2]-(1-depletion)*indims[2],indims[3]],
                         border_bottom_right_radius=int((height-10)/2),
                         border_top_left_radius=int((height-10)/2) )
        # Mittarin teksti
        label = self.game.font.render(self.annotation, True, (200,255,0))
        self.screen.blit(label, (pos[0], pos[1]+height))

class Btn:
    def __init__(self, screen, width, height, pos, annotation, game):
        self.screen = screen
        self.width = width
        self.height = height
        self.pos = pos
        self.annotation = annotation
        self.label = game.font.render(annotation, True, (255, 255, 255))
    
    def draw_btn(self, mouse_pos, click_pos):
        out = self.draw_rect(self.hover(mouse_pos), click_pos)
        self.screen.blit(self.label, (self.pos[0]+4, self.pos[1]+self.label.get_height()/2-4))
        return out

    def draw_rect(self, hover, click_pos):
        if(hover):
            pygame.draw.rect(self.screen, (0,125,int(0.9*255)), self.pos+(self.width,self.height), border_radius=2)
        else:
            pygame.draw.rect(self.screen, (0,0,255), self.pos+(self.width,self.height), border_radius=2)


    def hover(self, mouse_pos):
        width = self.width
        height = self.height
        x = self.pos[0]
        y = self.pos[1]
        mx = mouse_pos[0]
        my = mouse_pos[1]
        offset = 1
        if (mx >= x-offset and mx <= x + width + offset and my <= y + height + offset and my >= y - offset):
            return True
        return False


if __name__ == "__main__":
    Game()