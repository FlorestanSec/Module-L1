#Jeu

import os
import libs
import config
from collections import namedtuple
from time import time as timestamp

from composants import Fenetre, Boutons, Preferences, Scores, APropos, Frame
import composants
from disposition import DispositionManuelle, DispositionAleatoire
import controleur


class Jeu(Fenetre) :
    def __init__(self, joueur1=None, joueur2=None, mode=1) :
        '''
        @param joueur1  : Nom du 1er joueur (par défaut nom utilisateur système)
        @param joueur2  : Nom du 2nd joueur (par défaut nom spécifié dans la
                          configuration)
        @param mode     : 1 pour jeu joueur vs ordinateur, 0 pour ordinateur vs
                          ordinateur
                          (fonctionnalité non implémentée actuellement)
        '''
        if joueur1 and joueur2 and joueur1 == joueur2 :
            raise ValueError('joueur1 et joueur2 ne peuvent avoir le même nom')

        # Diminuer tailleGrilleBase diminuera également la taille de la fenêtre
        # Mais en deça d'une certaine limite cela fera sortir des éléments
        # hors plateau, et des textes difficilement lisibles.
        self.tailleGrilleBase = 380 #380 # Base
        self.margeGrilleBase = 40
        config.hauteurZoneSuperieure = 30
        config.hauteurZoneInferieure = 40
        config.hauteurZoneMessage = 40

        #XXX A voir si à garder....
        '''
        config.maxGrille = 16
        config.minGrille = 8
        config.tailleBateauMin = 2
        config.tailleBateauMax = 6
        # % max du nombre de cases bateaux sur la grille (1/4)
        config.quotaBateaux = 0.25
        '''

        config.hauteurPlateau = self.tailleGrilleBase\
                                + config.hauteurZoneMessage\
                                + self.margeGrilleBase * 4
        config.largeurFenetre = self.tailleGrilleBase * 2\
                                + self.margeGrilleBase * 4
        config.hauteurFenetre = config.hauteurZoneSuperieure\
                                + config.hauteurZoneInferieure\
                                + config.hauteurPlateau

        config.nomJoueur = str(joueur1) if joueur1 else os.getlogin()
        config.nomAdversaire = str(joueur2) if joueur2 else\
                               ('Poséidon' if config.nomJoueur != 'Poséidon'\
                                else 'Barbe noire')

        config.commencer = self.commencer

        # Répertoires et fichiers divers
        config.repertoireCourant = os.path.abspath(os.path.dirname(__file__))\
                                    + '/'
        # Thèmes
        config.repertoireThemes = config.repertoireCourant + 'themes/'
        config.fichierTheme = 'theme.xml'
        config.fichierThemeInfo = 'info.xml'
        # Langues
        config.repertoireLangues = config.repertoireCourant + 'langues/'
        config.fichierLangue = 'langue.xml'
        config.repertoireImages = config.repertoireCourant + 'images/'
        # Données
        config.repertoireDonnees = config.repertoireCourant + 'donnees/'
        config.fichierPreferences = config.repertoireDonnees + 'prefs'
        config.fichierResultats = config.repertoireDonnees + 'resultats'
        # Logs
        config.repertoireLogs = config.repertoireCourant + 'logs/'
        config.fichierLogIA = config.repertoireLogs + 'ia.log'
        # Non implémenté
        #config.fichierGrillesUtilisateur = config.repertoireDonnees + 'grilles'

        # Commandes référentes
        config.optionsCommandes = []
        config.optionsCommandes.append(('menu_nouvelle', self.redemarrer))
        config.optionsCommandes.append(('menu_preferences',
                                                self.fenetrePreferences))
        config.optionsCommandes.append(('menu_scores', self.fenetreScores))
        config.optionsCommandes.append(('menu_apropos', self.fenetreApropos))
        config.optionsCommandes.append(('menu_quitter', self.quitter))

        Fenetre.__init__(self)

        self.title('Bataille Navale')
        self.resizable(0, 0)
        self.bind_class('Tk', '<Destroy>', self._arreterDeroulement)

        self.preferences = libs.chargerPreferences()
        self.shemaUtilisateur = namedtuple('utilisateur',
                                           tuple(self.preferences.keys()))

        config.langue = libs.Langue(self.preferences['langue'])
        config.rlangue = libs.RegistreLangue(self)
        config.theme = libs.Theme(self.preferences['theme'])
        config.rtheme = libs.RegistreTheme()

        config.famillesPolice = libs.definirFamillesPolices()

        self.agencer()
        self._deroulement = None
        self._initialiser()


    def _initialiser(self) :
        '''
        Initialise la partie.
        Phase positionnement du jeu.
        '''
        # Rechargement des préférences
        self.preferences = libs.chargerPreferences()
        config.utilisateur = self.shemaUtilisateur(**self.preferences)
        self.bateauxAdjacents = self.preferences['adjacent']
        grilles = libs.Grilles()
        config.idJeu = grilles(self.preferences['grille'])

        self.grilleJeu(self.preferences['grille'])

        config.nombreCases = int(config.idJeu[1:config.idJeu.find('b')])
        config.tailleCases = self.tailleGrilleBase\
                             // int(config.idJeu[1:config.idJeu.find('b')])
        config.tailleGrille = config.tailleCases * config.nombreCases\
                              + config.nombreCases + 1
        config.margeGrille = self.margeGrilleBase\
                             + round((self.tailleGrilleBase\
                             - config.tailleGrille) / 4)
        config.bateaux = sorted([int(n) for n\
                                in config.idJeu[config.idJeu.find('b'):]\
                                if n.isdigit()], reverse=True)
        config.nomsBateaux = libs.definirNomsBateaux()
        self.disposition = DispositionManuelle(self.plateau,
                                               self.bateauxAdjacents,
                                               self.bas)


    def commencer(self, bateaux) :
        '''
        Commence la partie, déroulement du jeu (tour à tour).
        @param bateaux : dict des bateaux
        '''
        self.plateau.vider()
        self.bas.vider()
        self.disposition.detruire()
        self.disposition = None

        da = DispositionAleatoire(self.bateauxAdjacents)
        bateauxAdverse = da.positionner()
        self._deroulement = controleur.ControleurJeu(self.plateau, bateaux,
                                                     bateauxAdverse,
                                                     self.bateauxAdjacents,
                                                     self.resultatsPartie)


    def resultatsPartie(self, gagnant, nombreCoups, timestampDepart) :
        '''
        Enregistre le résultat de la partie.
        @param gagnant          : Nom du gagnant de la partie
        @param nombreCoups      : Total de coups du gagnant ayant venu à bout de
                                  son adversaire
        @param timestampDepart  : time() du départ de la partie
        '''
        gagnant = int(gagnant == config.nomJoueur)
        libs.enregistrerResultats(self.preferences['grille'], gagnant,
                                  timestampDepart, timestamp(), nombreCoups,
                                  self.bateauxAdjacents)
        config.fenetreBas.vider()
        boutons = Boutons(self.bas)

        bidRejouer = boutons.creer('bouton_rejouer', self.redemarrer)
        bidQuitter = boutons.creer('bouton_quitter', self.quitter)
        boutons.ancrer()

    def redemarrer(self) :
        '''
        Redémarre une partie
        '''
        self.bas.vider()
        if self._deroulement :
            self._deroulement.arreter()
            self.plateau.vider()
            del(self._deroulement)
            self._deroulement = None
        else :
            self.plateau.vider()
            self.disposition.detruire()
            self.disposition = None
        self._initialiser()

    def fenetrePreferences(self) :
        ''' Affiche les préférences du jeu '''
        libs.GestionnaireFenetresTierces(Preferences, self.fenetre)

    def fenetreScores(self) :
        ''' Affiche les scores du jeu '''
        libs.GestionnaireFenetresTierces(Scores, self.fenetre)

    def fenetreApropos(self) :
        ''' Affiche les infos relatives au jeu '''
        libs.GestionnaireFenetresTierces(APropos, self.fenetre)

    def quitter(self) :
        ''' Quitte le jeu '''
        super().destroy()
        print('Au revoir')

    def destroy(self) :
        self.quitter()

    def _arreterDeroulement(self, evt=None) :
        if self._deroulement :
            self._deroulement.arreter()

if __name__ == '__main__' :
    jeu = Jeu()
    jeu.mainloop()

