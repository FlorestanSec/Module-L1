#!/usr/bin/python3.4
# -*-coding: utf-8 -*

import xml.etree.ElementTree as xet
import tkinter as tk
import re
import os
from math import ceil
from random import randint, randrange, sample, shuffle
from collections import namedtuple
from copy import deepcopy
from pickle import Pickler, Unpickler
import logging
import logging.config

import config

class Journalisation :
    def __init__(self, fichier, terminal=False) :
        '''
        Journalisation de l'application.
        @param fichier  : fichier où le log doit être enregistré.    
        @param terminal : booléen, False par défaut, définit si le log doit être
                          également en sortie dans le terminal ou la console.
        '''
        parametres = config.PARAMETRES_LOGGING
        parametres['handlers']['fichier_debug']['filename'] = fichier
        parametres['handlers']['fichier_info']['filename'] = fichier
        try :
            os.remove(fichier)
        except :
            pass
        logging.config.dictConfig(parametres)
        if terminal :
            self.info = logging.getLogger('terminal.info').info
            self.debug = logging.getLogger('terminal.debug').debug
        else :
            self.info = logging.getLogger('fichier.info').info
            self.debug = logging.getLogger('fichier.debug').debug


def definirNomsBateaux() :
    '''
    Retourne une liste contenant l'identifiant dans langue en relation avec la
    liste des bateaux définis dans config.bateaux
    '''
    liste = {}
    for tb in set(config.bateaux) :
        liste[tb] = sample(range(len(config.langue.bateaux[tb])),
                           config.bateaux.count(tb))
    nomsBateaux = []
    for index, tb in enumerate(config.bateaux) :
        nomsBateaux.append('bateaux[{}][{}]'.format(tb, liste[tb].pop()))
    return nomsBateaux


def chargerFichierSerialise(fichier) :
    try :
        with open(fichier, 'rb') as f :
            try :
                pr = Unpickler(f)
                donnees = pr.load()
            except Exception as erreur :
                raise RuntimeError('Le fichier {} ne peut être lu par pickle,'
                                   ' erreur rencontrée : {}'\
                                   .format(fichier, erreur))
    except OSError as erreur :
        raise OSError('Le fichier {} ne peut être ouvert en lecture, erreur'
                       ' rencontrée : {}'.format(fichier, erreur))
    return donnees


def enregistrerFichierSerialise(fichier, donnees) :
    try :
        with open(fichier, 'wb') as f :
            try :
                pp = Pickler(f)
                pp.dump(donnees)
            except Exception as erreur :
                raise RuntimeError('Le fichier {} ne peut être enregistré par'
                                   ' pickle, erreur rencontrée : {}'\
                                   .format(fichier, erreur))
    except OSError as erreur :
        raise OSError('Le fichier {} ne peut être ouvert en écriture, erreur'
                      ' rencontrée : {}'.format(fichier, erreur))


PREFS = {'grille':'standard',
         'theme':'gris',
         'langue':'fr',
         'methode':'souris',
         #'son':'sans', # => abandonné
         'adjacent':False}

def chargerPreferences() :
    if os.path.isfile(config.fichierPreferences) :
        #XXX Aucune vérif n'est faite sur le retour du fichier
        # A voir pour la gestion de données invalides
        prefs = chargerFichierSerialise(config.fichierPreferences)
    else :
        prefs = PREFS
        enregistrerFichierSerialise(config.fichierPreferences, prefs)
    return prefs


def enregistrerPreferences(**valeurs) :
    prefs = chargerFichierSerialise(config.fichierPreferences)
    dif = set(valeurs.keys()) - set(prefs.keys())
    if dif :
        raise KeyError(', '.join(dif)\
                        + ' ne sont pas des clés existantes des préférences')
    for c, v in valeurs.items() :
        prefs[c] = v
    enregistrerFichierSerialise(config.fichierPreferences, prefs)


def chargerResultats() :
    #XXX A faire => exclure les résultats n'ayant plus références dans les
    # grilles définies
    # Voir si suppression ou non
    try :
        return chargerFichierSerialise(config.fichierResultats)
    except :
        return None


def enregistrerResultats(nomJeu, gagnant, timestampDepart, timestampFin,
                         nbCoups, bateauxAdjacents) :
    if os.path.isfile(config.fichierResultats) :
        resultats = chargerResultats()
    else :
        resultats = []

    resultats.append({'jeu':nomJeu, 'gagnant':gagnant, 'depart':timestampDepart,
                      'fin':timestampFin, 'coups':nbCoups,
                      'adjacent':bateauxAdjacents})
    enregistrerFichierSerialise(config.fichierResultats, resultats)


def themesDiponibles() :
    '''
    Retourne la liste des répertoires (situés dans le répertoire des thèmes)
    des thèmes disponibles et valides.
    Un thème valide doit comporter :
        - un nom de répertoire composé uniquement de caractères alphabétiques
          minuscules.
        - Contenir le fichier du thème et le fichier de ses informations.
        - Ces deux fichiers doivent avoir un xml conforme.
    '''
    #XXX A faire une fois tout établi
    # Vérif de la validité des fichiers xml des thèmes
    repThemes = [n for n in os.listdir(config.repertoireThemes)\
                if n.isalpha() and n.islower()]
    for rep in repThemes.copy() :
        for fichier in (config.fichierTheme, config.fichierThemeInfo) :
            if not os.path.isfile(config.repertoireThemes + rep + '/'\
                                  + fichier) :
                repThemes.remove(rep)
                break
    return repThemes


def themeInfo(repTheme) :
    '''
    Retourne un tuple contenant nom et description du thème
    @param repTheme : répertoire du thème contenu dans le répertoire des thèmes.
    '''
    xml = chargerXML(config.repertoireThemes + repTheme + '/'\
                     + config.fichierThemeInfo)
    return (xml.find('item[@id="nom"]').text,
            xml.find('item[@id="description"]').text)


def languesDisponibles() :
    '''
    Retourne un dict des langues disponibles.
    clé identifiant de la langue (nom  répertoire), valeur nom de la langue
    '''
    #XXX A faire vérif validité xml langue une fois tout établi
    repLangues = [n for n in os.listdir(config.repertoireLangues)\
                  if n.isalpha() and n.islower()]
    langues = {}
    for langue in repLangues :
        xml = chargerXML(config.repertoireLangues + langue + '/'\
                         + config.fichierLangue)
        langues[langue] = xml.find('item[@id="langue"]').text
    return langues


def definirFamillesPolices(root=None) :
    '''
    Détermine la famille de police par défaut à utiliser pour chaque type de
    police, retourne un namedtuple ayant pour attributs :
    serif, sansserif, monospace, cursive et fantasy
    '''
    from tkinter import font as tkfont

    famillesDispo = tkfont.families(root)

    preferences = dict( serif = ('URW Palladio L',
                                 'URW Bookman L',
                                 'Century Schoolbook',
                                 'Georgia',
                                 'Times',
                                 'Times New Roman',
                                 'Palatino Linotype',
                                 ),

                        sansserif = ('Nimbus Sans L',
                                     'URW Gothic L',
                                     'Verdana',
                                     'Tahoma',
                                     'Helvetica',
                                     'Lucida Grande',
                                     'Geneva',
                                     'DejaVu Sans',
                                     'Microsoft Sans Serif',
                                    ),

                        monospace = ('Bitstream Vera Sans Mono',
                                     'Courier 10 Pitch',
                                     'Nimbus Mono L',
                                     'Monaco',
                                     'Courier New',
                                     'Courier',
                                     'OCR A Extended',
                                     'DejaVu Sans Mono',
                                     'Lucida Console',
                                    ),

                        cursive = ('Domestic Manners',
                                   'URW Chancery L',
                                   'Brush Script MT',
                                   'Zapfino',
                                   'Apple Chancery',
                                   'Bradley Hand ITC',
                                   'Monotype Corsiva',
                                   'Comic Sans MS',
                                   ),

                        fantasy = ('Marked Fool',
                                   'Junkyard',
                                   'Balker',
                                   'Papyrus',
                                   'Haettenschweiler',
                                   'Impact',
                                   ),
                    )

    schema = namedtuple('familles_polices', ('serif', 'sansserif', 'monospace',
                                             'cursive', 'fantasy'))
    familles = dict(serif='serif', sansserif='sans-serif',
                    monospace='monospace', cursive='cursive',
                    fantasy='fantasy')

    for c, v in preferences.items() :
        for famille in v :
            if famille in famillesDispo :
                familles[c] = famille
                break

    return schema(**familles)

#XXX Ne sert nulle part dans l'application
def creerIdGrille(nbCases, bateaux) :
    '''
    Crée un identifiant grille de la forme gXbn.....bn
    Exemple : g10b5b4b3b2b2b2 pour une grille de 10 cases avec 1 bateau de 5
    cases, 1 de 4 cases, 1 de 3 cases, et 3 de 2 cases.
    @param nbCases  : nombre de cases du côté de la grille
    @param bateaux  : dict avec pour clé taille bateau et valeur son nombre
    '''
    return 'g{}{}'.format(nbCases, ''.join(['b{}'.format(t)*nb for t, nb\
                            in sorted(bateaux.items(), reverse=True) if nb]))


def bornesGrille(case, nbCases) :
    '''
    Retourne les bornes gauche et droite de la grille selon le numéro de la case
    fournie en paramètre
    '''
    bd = ceil(case / nbCases) * nbCases
    bg = bd - nbCases + 1
    return (bg, bd)


def genChaine(longueur, cars=None) :
    '''
    Génère une chaine aléatoire
    '''
    if not cars :
        cars = 'AZERTYUIOPQSDFGHJKLMWXCVBN0123456789'
    if longueur > len(cars) :
        raise ValueError('longueur de chaine demandée trop conséquente')
    while True :
        yield ''.join(sample(cars, longueur))


def genItemListe(liste) :
    '''
    Générateur retournant les items un à un de l'itérable fourni de façon
    infinie (retour au 1er item si dernier envoyé)
    '''
    index = 0
    while True :
        try :
            yield liste[index]
        except IndexError :
            index = 0
            continue
        index += 1


def chargerXML(fichier) :
    '''
    Charge le fichier xml et retourne le nœud racine
    '''
    try :
        doc = xet.parse(fichier)
    except FileNotFoundError :
        raise FileNotFoundError('Le fichier « {} » n\'existe pas'\
                                .format(fichier))
    except xet.ParseError :
        raise TypeError('Le fichier « {} » n\'a pas un format xml valide'\
                         .format(fichier))
    return doc.getroot()


class GestionnaireFenetresTierces :
    '''
    Gestionnaire de fenêtres tierces de l'application afin de n'avoir qu'une
    seule instance pour chaque type de fenêtre toplevel tkinter.
    (liste de singleton)
    '''
    _fenetresOuvertes = {}
    _fenetresDestroy = {}
    def __new__(classe, fenetre, *args, **dargs) :
        if fenetre.__name__ not in classe._fenetresOuvertes.keys() :
            classe._fenetresDestroy[fenetre.__name__] = fenetre.destroy
            fenetre.destroy = lambda obj :\
                              classe._gftDetruireFenetre(obj)
            instance = fenetre(*args, **dargs)
            classe._fenetresOuvertes[fenetre.__name__] = instance
        classe._fenetresOuvertes[fenetre.__name__].lift()
        return classe._fenetresOuvertes[fenetre.__name__]

    @classmethod
    def _gftDetruireFenetre(classe, obj) :
        classe._fenetresDestroy[obj.__class__.__name__](obj)
        obj.__class__.destroy = classe._fenetresDestroy[obj.__class__.__name__]
        del(classe._fenetresDestroy[obj.__class__.__name__],
            classe._fenetresOuvertes[obj.__class__.__name__])



class CasesGrille :
    '''
    Fournit l'accès simple à diverses données concernant les cases d'une grille.
    '''
    def __init__(self, x, y, nbCases, tailleCases, ligne=1) :
        '''
        @param x, y         : coordonnée supérieure gauche de la grille
                              »» Lignes de périmètres incluses ««
                              ce qui signifie qu'un x = 20, y = 40 avec 1 pour
                              ligne que la première case aura comme coordonnée
                              supérieure gacuhe, 21 et 41
        @param nbCases      : nombre de cases d'un côté de la grille
        @param tailleCases  : taille en pixel d'une case de la grille
        '''
        self.x = x
        self.y = y
        self.ligne = ligne
        self.nbCases = nbCases
        self.tailleCases = tailleCases

        # Génération de toutes les cases, leurs coordonnées ainsi que leurs
        # cases adjacentes
        self.cases = {}
        i = 1
        cx = self.x + self.ligne
        cy = self.y + self.ligne
        while i <= self.nbCases ** 2 :
            adjacentes = []
            # Borne haute
            if i - self.nbCases > 0 :
                adjacentes.append(i - self.nbCases)
            # Borne Basse
            if i + self.nbCases < self.nbCases ** 2 :
                adjacentes.append(i + self.nbCases)
            # Borne droite et gauche
            bg, bd = bornesGrille(i, self.nbCases)
            if i - 1 >= bg :
                adjacentes.append(i - 1)
            if i + 1 <= bd :
                adjacentes.append(i + 1)

            self.cases[i] = {'coords':(cx, cy, cx+self.tailleCases,
                                       cy+self.tailleCases),
                             'adjacentes':adjacentes}
            if i % nbCases == 0 :
                cx = self.x + self.ligne
                cy += self.tailleCases + self.ligne
            else :
                cx += self.tailleCases + self.ligne
            i += 1

    def coords(self, *cases) :
        '''
        Retourne les coordonnées (x, y, x2, y2) sur la grille de la case ou des
        cases stipulées.
        x, y sera le coin supérieur gauche de la 1ère case (la plus à gauche
        et/ou la plus en haut)
        x2, y2 sera le coin inférieur droit de la dernière case (la plus à
        droite et/ou la plus en bas)
        '''
        if len(cases) == 1 :
            return self.cases[cases[0]]['coords']
        x = self.cases[min(cases)]['coords'][0]
        y = self.cases[min(cases)]['coords'][1]
        x2 = self.cases[max(cases)]['coords'][2]
        y2 = self.cases[max(cases)]['coords'][3]
        return x, y, x2, y2

    def numeros(self, x, y, x2, y2) :
        '''
        Retourne les numéros de cases de la grille situés entre x, y et x2, y2
        Cette méthode est l'inverse de coords
        '''
        cases = []
        for num, v in self.cases.items() :
            if v['coords'][0] >= x and v['coords'][1] >= y and\
               v['coords'][2] <= x2 and v['coords'][3] <= y2 :
                cases.append(num)
        return tuple(cases)

    def point(self, x, y) :
        '''
        Retourne la case de la grille contenant le point x, y ou 0 si pas de
        résultat
        '''
        for num, v in self.cases.items() :
            if v['coords'][0] <= x <= v['coords'][2]\
               and v['coords'][1] <= y <= v['coords'][3] :
                return num
        return 0

    def adjacentes(self, *cases) :
        '''
        Retourne les cases adjacentes des cases stipulées sur la grille
        '''
        if len(cases) == 1 :
            return self.cases[cases[0]]['adjacentes']
        adj = []
        for c in cases :
            adj.extend(self.cases[c]['adjacentes'])
        return tuple(set(adj) - set(cases))



class Annuaire :
    def __init__(self, identifiant, dico) :
        '''
        Charge et crée un annuaire (dict) identifiant:valeur
        @param identifiant: identifiant
        @param dico : euh, un dict (^-^)
        '''
        self.__dict__['_annuaire'] = dico
        self.__dict__['_id'] = identifiant

    def __setattr__(self, cle, valeur) :
        ''' Empêche toute définition ou redéfinition d'un item de l'annuaire '''
        raise NotImplementedError

    def __delattr__(self, cle) :
        ''' Empêche la suppression d'un item de l'annuaire '''
        raise NotImplementedError

    def __getattr__(self, cle) :
        ''' Retourne la valeur dans l'annuaire relative à la clé fournie '''
        try :
            return self._annuaire[cle]
        except KeyError :
            raise KeyError('{} n\'existe pas dans l\'annuaire {}'\
                           .format(cle, self.__class__.__name__))

    def __str__(self) :
        ''' Retourne une chaine de l'annuaire ordonné par ses clés '''
        an = []
        for c in sorted(self._annuaire.keys()) :
            an.append(c + ' => ' + str(self._annuaire[c]))
        return '\n'.join(an)

    def __add__(self, annuaire) :
        self.__dict__['_annuaire'].update(annuaire.annuaire)
        return self

    def __iadd__(self, annuaire) :
        self.__dict__['_annuaire'].update(annuaire.annuaire)
        return self

    def __call__(self, cle) :
        '''
        Retourne également la valeur dans l'annuaire relative à la clé fournie.
        '''
        return self.__getattr__(cle)

    def cle(self, cle) :
        '''
        Vérifie l'existence de la clé spécifiée dans l'annuaire.
        Retourne la clé donnée, ou lève une erreur si la clé n'existe pas.
        '''
        assert cle in self._annuaire.keys(),\
            '{} n\'est pas une clé existante de l\'annuaire {} avec\
            l\'identifiant {}'\
            .format(cle, self.__class__.__name__, self._id)
        return cle

    @property
    def annuaire(self) :
        ''' Retourne l'annuaire complet '''
        return self._annuaire

    @property
    def identifiant(self) :
        ''' Retourne l'identifiant de l'annuaire '''
        return self._id

    def recharger(self, identifiant, dico) :
        '''
        Change l'annuaire existant ainsi que son identifiant
        en ceux fournis en arguments.
        '''
        self.__dict__['_annuaire'] = dico
        self.__dict__['_id'] = identifiant



class Theme(Annuaire) :
    def __init__(self, identifiant) :
        Annuaire.__init__(self, identifiant, ChargerTheme(identifiant)())

    def changer(self, identifiant) :
        '''
        Change le thème actuel en celui spécifié avec l'identifiant fourni
        '''
        self.recharger(identifiant, ChargerTheme(identifiant)())



class Langue(Annuaire) :
    def __init__(self, identifiant) :
        Annuaire.__init__(self, identifiant, ChargerLangue(identifiant)())

    def changer(self, identifiant) :
        '''
        Change la langue actuelle en celle stipulée par l'identifiant fourni
        '''
        self.recharger(identifiant, ChargerLangue(identifiant)())



class ChargerTheme :
    def __init__(self, identifiant) :
        '''
        Charge le thème spécifié par l'identifiant fourni.
        @param identifiant : nom du thème (répertoire du thème).
        '''
        xml = chargerXML(config.repertoireThemes + identifiant + '/'\
                         + config.fichierTheme)
        self._dico = self._construire(xml.findall('item'))

    def _construire(self, noeud, nom='', dico={}) :
        ''' Méthode interne construisant les clés et valeurs du thème '''
        for n in noeud :
            if n.get('valeur') :
                dico[nom + n.get('id')] = n.get('valeur')
            enfants = n.findall('item')
            if enfants :
                self._construire(enfants, nom + n.get('id') + '_', dico)
        return dico

    def __call__(self) :
        ''' Retourne le thème intégral '''
        return self._dico



class RegistreTheme :
    '''
    Registre destiné à garder en mémoire les propriétés des objets tkinter
    comportant des couleurs nécessitant d'être mises à jour lors d'un changement
    de thème de l'application.
    IMPORTANT :
    Le registre s'appuie sur la variable de configuration theme.
    '''
    def __init__(self) :
        self._registre = {}
        self._registrecoid = {}
        self._registremindex = {}

    def inscrire(self, objet, **proprietes) :
        '''
        Inscrit au registre, l'objet ainsi que les identifiants de ses
        propriétés.
        @param objet        : objet tkinter ou classe en héritant.
        @param proprietes   : dict ayant pour clé le nom de la propriété de
                              l'objet,
                              et pour valeur l'identifiant dans l'annuaire du
                              thème.
        '''
        if objet not in self._registre.keys() :
            self._registre[objet] = {}
        for n, v in proprietes.items() :
            self._registre[objet][n] = config.theme.cle(v)
            #XXX Ne peut être effectué ici, car on ne dispose pas
            # encore du widget tk dans la classe.
            #objet.configure(**{n:self.__dict__['_theme'](v)})

    

