#Controleur

from time import time, sleep
from collections import namedtuple
import threading
from uuid import uuid4
from copy import deepcopy

import config
from composants import (CompteurBateauxPlateau, GrillePlateau,
                        MarqueurTirPlateau, MarqueurTourPlateau,
                        MessagePlateau, CasesGrillePlateau)
import methodes
from libs import CasesGrille, genChaine, MessageResultatTir
from ia import IA


class Joueur :
    def __init__(self, id_, casesBateaux, retourTir) :
        '''
        @param id_          : identifiant joueur
        @param casesBateaux : dict généré par le positionnement au format
                              index:cases
        @param retourTir    : méthode contrôleur auquel l'identifiant joueur
                              et la case choisie doit être envoyés.
        '''
        self.actif = True # Sera mis à false par le controleur
        self.id = id_
        self.casesBateaux = deepcopy(casesBateaux)
        self.casesBateauxRestantes = deepcopy(casesBateaux)

        self.retourTir = retourTir

    def tirer(self) :
        raise NotImplementedError('Cette méthode doit être redéfinie')

    def resultatTir(self, resultat) :
        '''
        @param resultat : 0 pour rien, 1 pour touché, 2 pour coulé
        '''
        pass

    def resultatTirAdverse(self, case) :
        '''
        Retourne un tuple de 3 valeurs correspondants à :
            - Résultat tir, id bateau ou None, cases bateau coulé ou None

            Les retours seront donc :
            - Pour tir dans l'eau   : 0, None, None
            - Pour bateau touché    : 1, id bateau touché, None
            - Pour bateau coulé     : 2, id bateau coulé, cases bateau coulé
            - Pour flotte anéantie  : 3, id bateau coulé (dernier restant), None
        '''
        for c, v in self.casesBateaux.items() :
            try :
                self.casesBateauxRestantes[c].remove(case)
            except (KeyError, ValueError) :
                continue
            if not self.casesBateauxRestantes[c] :
                del(self.casesBateauxRestantes[c])
                if not self.casesBateauxRestantes :
                    return (3, c, None)
                return (2, c, self.casesBateaux[c])
            return (1, c, case)
        return (0, None, None)



class JoueurHumain(Joueur) :

    def __init__(self, *args) :
        '''
        Joueur réel, les méthodes tirer et resultatTir seront redéfinies par le
        controleur.
        '''
        Joueur.__init__(self, *args)
        self.casesTirees = set()

    def exclureCasesTirage(self, cases) :
        ''' Enlève les cases spécifiées des cases pouvant être tirées '''
        self.casesTirees |= set(cases)


    def ajouterCase(self, case) :
        '''
        Ajoute la case spécifiée aux cases tirées.
        Retourne False si la case était déjà présente True si non présente.
        '''
        if case in self.casesTirees :
            return False
        self.casesTirees.add(case)
        return True



class JoueurVirtuel(Joueur) :

    def __init__(self, id_, casesBateaux, retourTir, cg, bateauxAdjacents,
                 delai=2) :
        Joueur.__init__(self, id_, casesBateaux, retourTir)
        self.cg = cg
        self.bateauxAdjacents = bateauxAdjacents
        self.delai = delai
        self.ia = IA(config.nombreCases, config.bateaux, self.bateauxAdjacents)
        self.tir = 0

    def _attendre(self) :
        ''' Méthode interne '''
        i, tour = 0, self.delai * 10
        while i < tour :
            sleep(0.1)
            # Test à chaque tour de l'état du jeu, ceci afin de permettre un
            # arrêt rapide, si arrêt du jeu en cours effectué dans cette boucle.
            if not self.actif :
                break
            i += 1

    def tirer(self) :
        self._attendre()
        self.tir = self.ia.tirer()
        self.retourTir(self.id, self.tir)

    def resultatTir(self, resultat) :
        if resultat[0] == 1 :
            self.ia.explorerAutour(self.tir)
        elif resultat[0] == 2 :
            if not self.bateauxAdjacents :
                # Ceci pourrait être directement géré par l'ia, puisqu'elle sait
                # si les bateaux du jeu sont juxtaposés ou non
                self.ia.supprimerCases(*self.cg.adjacentes(*resultat[2]))
            self.ia.supprimerBateau(resultat[2])



class ControleurJeu(threading.Thread) :
    '''
    Gère le tour à tour des joueurs et les messages relatifs aux actions
    effectuées.
    '''
    def __init__(self, plateau, bateauxJoueurHumain, bateauxJoueurVirtuel,
                 bateauxAdjacents, retourResultats) :

        self.plateau = plateau
        self.retourResultats = retourResultats
        self.bateauxAdjacents = bateauxAdjacents
        self.largeurMarqueurTour = 50
        self.hauteurMarqueurTour = 20
        # Structure de base joueur
        joueur = namedtuple('joueur', ['id', 'nom', 'joueur', 'bateaux',
                                       'grille', 'tir', 'cg', 'cases',
                                       'marqueur', 'message', 'messageType'])
        # Génération des grilles en 1er, pour quelles se situent en bas de
        # la file des composants canvas tk
        gh = GrillePlateau(self.plateau, config.margeGrille, config.margeGrille)
        gv = GrillePlateau(self.plateau, config.margeGrille * 3\
                                         + config.tailleGrille,
                                         config.margeGrille)

        cgh = CasesGrille(config.margeGrille, config.margeGrille,
                          config.nombreCases, config.tailleCases)
        cgv = CasesGrille(config.margeGrille * 3 + config.tailleGrille,
                          config.margeGrille, config.nombreCases,
                          config.tailleCases)

        tmpId = uuid4()
        self.humain = joueur(id=tmpId,
                             nom=config.nomJoueur,
                             joueur=JoueurHumain(tmpId, bateauxJoueurHumain,
                                                 self.traitementTir),
                             bateaux=bateauxJoueurHumain,
                             grille=gh,
                             tir=MarqueurTirPlateau(self.plateau),
                             cg=CasesGrille(config.margeGrille,
                                            config.margeGrille,
                                            config.nombreCases,
                                            config.tailleCases),
                             cases=CasesGrillePlateau(
                                        self.plateau,
                                        cgv,
                                        bateauxJoueurVirtuel,
                                        not self.bateauxAdjacents,
                                        False),
                             marqueur=MarqueurTourPlateau(
                                        self.plateau,
                                        config.margeGrille * 3\
                                         + config.tailleGrille\
                                         + round((config.tailleGrille\
                                         - self.largeurMarqueurTour) / 2),
                                         config.margeGrille * 2\
                                         + config.tailleGrille\
                                         + round((config.margeGrille\
                                         - self.hauteurMarqueurTour) / 2),
                                         self.largeurMarqueurTour,
                                         self.hauteurMarqueurTour),
                             message=MessageResultatTir('joueur'),
                             messageType=('bien', 'super'),
                            )
        self.humain.grille.graduer()
        self.humain.grille.intituler(config.nomJoueur)
        # Déclaration de la méthode tirer joueur comme méthode interne du
        # contrôleur
        self.humain.joueur.tirer = self.activerBind


        tmpId = uuid4()
        self.virtuel = joueur(id=tmpId,
                              nom=config.nomAdversaire,
                              joueur=JoueurVirtuel(tmpId, bateauxJoueurVirtuel,
                                                   self.traitementTir,
                                                   cgv, self.bateauxAdjacents),
                              bateaux=bateauxJoueurVirtuel,
                              grille=gv,
                              tir=MarqueurTirPlateau(self.plateau),
                              cg=cgv,
                              cases=CasesGrillePlateau(self.plateau,
                                                       cgh,
                                                       bateauxJoueurHumain,
                                                       True, True),

                              marqueur=MarqueurTourPlateau(
                                        self.plateau,
                                        config.margeGrille\
                                        + round((config.tailleGrille\
                                        - self.largeurMarqueurTour) / 2),
                                        config.margeGrille * 2\
                                        + config.tailleGrille\
                                        + round((config.margeGrille\
                                        - self.hauteurMarqueurTour) / 2),
                                        self.largeurMarqueurTour,
                                        self.hauteurMarqueurTour),
                              message=MessageResultatTir('adversaire'),
                              messageType=('attention', 'fatal')
                             )
        self.virtuel.grille.graduer()
        self.virtuel.grille.intituler(config.nomAdversaire)

        self.methodeTir = methodes.ModeTir(config.utilisateur.methode,
                                           self.plateau, self.validerTir,
                                           self.virtuel.cg)
        #XXX c'est crade, mais ça me facilite la chose lors d'un changement de
        # méthode via les préférences (°_º)
        config.methodeTir = self.methodeTir

        self.tempsDepart = 0
        self.cmpt = 0
        self.tours = []
        self.tourFini = False
        self._retournerResultats = False
        self.etatJeu = False
        self.initJeu = False

        self.message = MessagePlateau(self.plateau)

        self.compteurBateaux = CompteurBateauxPlateau(self.plateau,
                                                      config.margeGrille * 3\
                                                      + config.tailleGrille)

        threading.Thread.__init__(self)
        self._arretJeu = threading.Event()
        self._arretEffectif = threading.Event()
        self.start()

    def activerBind(self) :
        '''
        Substitut de la méthode tirer joueur.
        Activation du bind pour que le joueur humain puisse jouer.
        '''
        self.methodeTir.activer()

    def validerTir(self, event) :
        '''
        Méthode passée au bind.
        Action joueur.
        '''
        ids = self.plateau.find_overlapping(event.x, event.y, event.x, event.y)
        if self.virtuel.grille.id in ids :
            case = self.virtuel.cg.point(event.x, event.y)
            if case :
                if self.humain.joueur.ajouterCase(case) :
                    self.methodeTir.desactiver()

                    self.traitementTir(self.humain.joueur.id, case)
                else :
                    self.message('message_information_connue', 'attention')


    def resultatTir(self, resultat) :
        #XXX A virer
        pass

    def _attendre(self, temps, pas=0.1) :
        i, tour = 0, temps / pas
        while i < tour :
            sleep(pas)
            if self._arretJeu.isSet() :
                return
            i += 1

    def traitementTir(self, id_, tir) :
        '''
        Traitement des tirs joueurs.
        '''
        if id_ != self.tours[0].joueur.id :
            raise RuntimeError('Problème, {} a pu jouer 2 coups consécutifs'\
                                .format(self.joueur[1].nom))

        self.tours[0].tir.deplacer(*self.tours[1].cg.coords(tir))
        try :
            resultat = self.tours[1].joueur.resultatTirAdverse(tir)
        except Exception as erreur :
            raise type(erreur)('Erreur « {} » rencontrée lors du retour tir de'
                               ' {}'.format(erreur.args[0], self.tours[1].nom))
        self.cmpt += 1
        self.tours[0].joueur.resultatTir(resultat)
        # Tir manqué
        if resultat[0] == 0 :
            idMessage = self.tours[0].message.rate()
            config.rlangue.remplacements(idMessage,
                                         {'joueur':config.nomJoueur,
                                          'adversaire':config.nomAdversaire})
            self.tours[0].cases.manque(tir)
            self.message(idMessage)
        # Touché
        elif resultat[0] == 1 :
            idMessage = self.tours[0].message.touche()
            config.rlangue.remplacements(idMessage,
                                         {'joueur':config.nomJoueur,
                                          'adversaire':config.nomAdversaire,
                                          'bateau':':{}'\
                                          .format(config\
                                                  .nomsBateaux[resultat[1]])})
            self.message(idMessage, self.tours[0].messageType[0])
            self.tours[0].cases.touche(tir)
        # Coulé / Flotte bateaux coulée
        else :
            self.tours[0].cases.coule(self.tours[1].bateaux[resultat[1]])
            if not self.bateauxAdjacents :
                self.tours[0].cases.manque(*self.tours[0]\
                                           .cg.adjacentes(
                                           *self.tours[1].bateaux[resultat[1]]))
                if self.tours[0].nom == config.nomJoueur :
                    self.tours[0].joueur.exclureCasesTirage(
                                         self.tours[0].cg.adjacentes(
                                           *self.tours[1].bateaux[resultat[1]]))
            if self.tours[0].nom == config.nomJoueur :
                self.compteurBateaux.incremente(len(self.tours[1]\
                                                .bateaux[resultat[1]]))
            if resultat[0] == 2 :
                idMessage = self.tours[0].message.coule()
                config.rlangue.remplacements(idMessage,
                                             {'joueur':config.nomJoueur,
                                              'adversaire':config.nomAdversaire,
                                              'bateau':':{}'.format(
                                              config.nomsBateaux[resultat[1]])})
                self.message(idMessage, self.tours[0].messageType[1])
            else :
                idMessage = self.tours[0].message.gagne()
                config.rlangue.remplacements(idMessage,
                                            {'joueur':config.nomJoueur,
                                             'adversaire':config.nomAdversaire})
                self.message(idMessage, self.tours[0].messageType[1])
                if self.tours[0].nom != config.nomJoueur :
                    self.tours[1].cases.devoiler()
                self._retournerResultats = True
                self.etatJeu = False
                self._arretJeu.set()
                return

        self.tours[0].marqueur.desactiver()
        self.tours[1].marqueur.activer()
        self.tours.reverse()
        self.tourFini = True

    # Tirage au sort du 1er à jouer
    def tirerAuSort(self) :
        self.message('message_information_tirage')
        self._attendre(2)
        t = time()
        while time() < t + 2 :
            self.message(next(genChaine(12)), var=False)
            sleep(0.05)
            # Sorti du tirage si arret demandé
            if self._arretJeu.isSet() :
                return

        if round(time()) % 2 == 0 :
            self.tours = [self.humain, self.virtuel]
            self.cmpt = 0
            self.message('message_information_premier')
            self.humain.marqueur.activer()
            self.virtuel.marqueur.desactiver()
            self.message('message_information_commencer')
        else :
            self.tours = [self.virtuel, self.humain]
            self.cmpt = 1
            config.rlangue.remplacements('message_information_second',
                                         {'adversaire':config.nomAdversaire})
            self.message('message_information_second')
            self.humain.marqueur.desactiver()
            self.virtuel.marqueur.activer()
        self._attendre(1)
        self.initJeu = True
        self.etatJeu = True
        self.tempsDepart = time()
        self.tourFini = True

    def run(self) :
        while not self._arretJeu.isSet() :
            if not self.initJeu :
                try :
                    self.tirerAuSort()
                except Exception as erreur :
                    self.etatJeu = False
                    self._arretJeu.set()
                    break

            while self.etatJeu :
                self._arretJeu.wait(0.10)
                if self.tourFini :
                    self.tourFini = False
                    try :
                        self.tours[0].joueur.tirer()
                    except Exception as erreur :
                        self.etatJeu = False
                        self._arretJeu.set()
                        break

        self._arretEffectif.set()
        config.methodeTir = None
        if self._retournerResultats :
            self.retourResultats(self.tours[0].nom, int(self.cmpt / 2),
                                 self.tempsDepart)


    def arreter(self) :
        '''
        Arrêt du jeu
        '''
        self.etatJeu = False
        self._arretJeu.set()

        self.message = None
        try :
            self.tours[0].joueur.actif = False
            self.tours[1].joueur.actif = False
        except :
            # tours est vide, donc tirage au sort en cours
            pass

        self.humain.joueur.retourTir = None
        self.virtuel.joueur.retourTir = None
        del(config.methodeTir, self.methodeTir)
        del(self.tours, self.message, self.humain, self.virtuel)


        print('Arrêt en cours', sep='', end='')
        i = 0
        while self.is_alive() :
            if i == 10 :
                # kill fenêtre lors du tirage sur windows, thread bloqué...
                # Pas d'autre choix que de kill python
                import os, signal
                os.kill(os.getpid(), signal.SIG_IGN)
            print('.', sep='', end='')
            self._arretEffectif.wait(0.05)
            i += 1
        del(self._arretJeu, self._arretEffectif)
        print('\nJeu terminé')
