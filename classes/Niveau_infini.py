""""
Gestion du niveau infini (Easter Egg)
"""
import pygame
import random
from constantes import *
from classes.ennemis import Tornade, UFO, Meteorite, Comet
from classes.items import ItemVie


def update_niveau_infini(jeu_instance):
    """Met à jour la logique du niveau infini"""
    # Updates de base
    jeu_instance.update_fond()
    jeu_instance.vfx.update()
    jeu_instance.all_sprites.update()
    jeu_instance.items.update()
    
    # Tir automatique du joueur
    balles = jeu_instance.joueur.verifier_tir_auto()
    if balles:
        jeu_instance.musique.jouer_effet("tir")
        jeu_instance.vfx.ajouter(jeu_instance.joueur.rect.centerx, jeu_instance.joueur.rect.top, JAUNE, 2)
        for balle in balles:
            jeu_instance.all_sprites.add(balle)
            jeu_instance.balles.add(balle)
    
    temps_ecoule = (pygame.time.get_ticks() - jeu_instance.debut_niveau) / 1000

    now = pygame.time.get_ticks()
    nb_mobs = len(jeu_instance.mobs)

    # ===== SPAWN DU BOSS À 5 MINUTES =====
    if temps_ecoule >= 300:  # 5 minutes = 300 secondes
        # Faire apparaître le boss une seule fois
        if not hasattr(jeu_instance, 'boss_infini_apparu'):
            from classes.boss import Boss
            jeu_instance.boss = Boss()
            jeu_instance.all_sprites.add(jeu_instance.boss)
            jeu_instance.mobs.add(jeu_instance.boss)
            jeu_instance.boss_infini_apparu = True
            print("[INFO] 🔥 BOSS INFINI APPARAÎT ! Survivez !")

    # Déterminer le nombre max d'ennemis et le délai selon le temps
    # TOUTES LES PHASES DURENT 1 MINUTE
    if temps_ecoule < 60:
        # Phase 1 (0-1min) : Facile - Tornades simples uniquement
        max_ennemis = 2
        delai_spawn = 2000
        types_ennemis = ["tornade"]
    elif temps_ecoule < 120:
        # Phase 2 (1-2min) : Introduction progressive des UFO
        max_ennemis = 2
        delai_spawn = 1800
        types_ennemis = ["tornade", "tornade", "tornade", "ufo"]
    elif temps_ecoule < 180:
        # Phase 3 (2-3min) : Tornades difficiles + UFO
        max_ennemis = 3
        delai_spawn = 1600
        types_ennemis = ["tornade", "tornade", "ufo", "ufo"]
    elif temps_ecoule < 240:
        # Phase 4 (3-4min) : Météorites arrivent !
        max_ennemis = 3
        delai_spawn = 1500
        types_ennemis = ["tornade", "ufo", "meteorite"]
    elif temps_ecoule < 300:
        # Phase 5 (4-5min) : Comètes arrivent - TOUS les ennemis ! Préparation au boss
        max_ennemis = 4
        delai_spawn = 1400
        types_ennemis = ["tornade", "ufo", "meteorite", "comet"]
    else:
        # Phase 6+ (5min+) : BOSS + ennemis modérés
        # BOSS EST LÀ : Moins d'ennemis et spawn plus lent pour rendre le combat gérable
        max_ennemis = 3  # Boss + 2 autres seulement
        delai_spawn = 2000  # Spawn toutes les 2 secondes
        types_ennemis = ["tornade", "ufo", "meteorite", "comet"]

    # Spawner les ennemis normaux (pas le boss)
    if nb_mobs < max_ennemis:
        if now - jeu_instance.dernier_spawn > delai_spawn:
            type_ennemi = random.choice(types_ennemis)

            if type_ennemi == "tornade":
                # 0-1min : Tornades niveau 1 (1 PV, pas de barre de vie)
                # 1-2min : Tornades niveau 2 (2 PV, avec barre de vie)
                # 2min+ : Tornades niveau 3 (3 PV, avec barre de vie)
                if temps_ecoule < 60:
                    ennemi = Tornade(1)  # 1 PV - faciles
                elif temps_ecoule < 120:
                    ennemi = Tornade(2)  # 2 PV - moyennes
                else:
                    ennemi = Tornade(3)  # 3 PV - difficiles
            elif type_ennemi == "ufo":
                ennemi = UFO()
            elif type_ennemi == "meteorite":
                ennemi = Meteorite()
            else:  # comet
                ennemi = Comet()

            jeu_instance.all_sprites.add(ennemi)
            jeu_instance.mobs.add(ennemi)
            jeu_instance.dernier_spawn = now

    # Collisions balles/ennemis
    hits = pygame.sprite.groupcollide(jeu_instance.mobs, jeu_instance.balles, False, True)
    for mob, balles_touchees in hits.items():
        mob.pv -= len(balles_touchees)
        jeu_instance.musique.jouer_effet("degats")
        jeu_instance.vfx.ajouter(mob.rect.centerx, mob.rect.centery, JAUNE, 3)

        if mob.pv <= 0:
            # Drop de vache (vie) si on a moins que le maximum de vies
            if random.random() < 0.10 and jeu_instance.vies < jeu_instance.joueur.max_vies:
                vie_item = ItemVie(mob.rect.centerx, mob.rect.centery)
                jeu_instance.items.add(vie_item)

            # Son différent selon le type d'ennemi
            if isinstance(mob, Tornade):
                jeu_instance.musique.jouer_effet("vent")
            else:
                jeu_instance.musique.jouer_effet("explosion")

            mob.kill()
            jeu_instance.score_total += mob.valeur
            jeu_instance.argent += mob.valeur
            jeu_instance.vfx.ajouter(mob.rect.centerx, mob.rect.centery, GRIS_FONCE, 10)

    # Ramassage des vaches (vies)
    recup_vies = pygame.sprite.spritecollide(jeu_instance.joueur, jeu_instance.items, True)
    for vie_item in recup_vies:
        if jeu_instance.vies < jeu_instance.joueur.max_vies:
            jeu_instance.vies += 1
            jeu_instance.musique.jouer_effet("extra_vie")
            jeu_instance.vfx.ajouter(vie_item.rect.centerx, vie_item.rect.centery, ROUGE, 10)

    # ===== GESTION DU BOSS =====
    if hasattr(jeu_instance, 'boss') and jeu_instance.boss:
        # Mettre à jour les projectiles du boss
        for projectile in jeu_instance.boss.projectiles[:]:
            projectile.update()
            # Supprimer si hors écran
            if not projectile.rect.colliderect(pygame.Rect(0, 0, LARGEUR_JEU, HAUTEUR_JEU)):
                jeu_instance.boss.projectiles.remove(projectile)
        
        # Collision laser du boss avec le joueur (enlève 2 vies !)
        if jeu_instance.boss.laser_actif:
            laser_rect = jeu_instance.boss.get_laser_rect()
            if laser_rect and jeu_instance.joueur.rect.colliderect(laser_rect):
                if not jeu_instance.joueur.invincible:
                    jeu_instance.vies -= 2  # Le laser enlève 2 vies !
                    jeu_instance.vfx.declencher_degats()
                    jeu_instance.vfx.ajouter(jeu_instance.joueur.rect.centerx, jeu_instance.joueur.rect.centery, ROUGE_SANG, 20)
                    jeu_instance.musique.jouer_effet("degats")
                    # Rendre temporairement invincible
                    jeu_instance.joueur.invincible = True
                    jeu_instance.joueur.fin_invincibilite = pygame.time.get_ticks() + 2000
        
        # Collision projectiles du boss avec le joueur
        for projectile in jeu_instance.boss.projectiles[:]:
            if jeu_instance.joueur.rect.colliderect(projectile.rect):
                if not jeu_instance.joueur.invincible:
                    jeu_instance.vies -= 1
                    jeu_instance.vfx.declencher_degats()
                    jeu_instance.vfx.ajouter(jeu_instance.joueur.rect.centerx, jeu_instance.joueur.rect.centery, ROUGE_SANG, 10)
                    jeu_instance.musique.jouer_effet("degats")
                jeu_instance.boss.projectiles.remove(projectile)

    # Collisions joueur/ennemis
    if pygame.sprite.spritecollide(jeu_instance.joueur, jeu_instance.mobs, True):
        if not jeu_instance.joueur.invincible:
            jeu_instance.vies -= 1
            jeu_instance.vfx.declencher_degats()
            jeu_instance.vfx.ajouter(jeu_instance.joueur.rect.centerx, jeu_instance.joueur.rect.centery, ROUGE_SANG, 15)
            jeu_instance.musique.jouer_effet("degats")

    # Ennemis hors écran (pas pour comètes/météorites/boss)
    from classes.boss import Boss
    for m in list(jeu_instance.mobs):
        if m.rect.top > HAUTEUR_JEU and not isinstance(m, (Comet, Meteorite, Boss)):
            m.kill()
            if not jeu_instance.joueur.invincible:
                jeu_instance.vies -= 1
                jeu_instance.vfx.declencher_degats()
                jeu_instance.musique.jouer_effet("degats")
                jeu_instance.vfx.ajouter(m.rect.centerx, HAUTEUR_JEU - 10, ROUGE, 5)

    if jeu_instance.vies <= 0:
        jeu_instance.etat = "GAMEOVER"
        pygame.mouse.set_visible(True)
        jeu_instance.musique.jouer_effet("gameover")
        jeu_instance.musique.arreter_musique()
