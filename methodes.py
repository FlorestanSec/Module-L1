#Méthodes

import tkinter as tk
import re

import libs
import config

class CiblePlateau :
    '''
    Affiche et gère une « cible » focalisant une case d'une grille plateau
    '''
    def __init__(self, plateau, cg, visible=True) :
        '''
        @param plateau  : plateau du jeu
        @param cg       : instance d'une classe CasesGrille
        @param visible  : booléen, (True par défaut) spécifiant si la cible doit
                          être affichée lors de sa création.
        '''
        self.plateau = plateau
        self.cg = cg
        etat = tk.DISABLED if visible else tk.HIDDEN
        cmin = self.cg.coords(1)
        cmax = self.cg.coords(config.nombreCases ** 2)
        self.ccx = (cmin[0], cmax[2]-2)
        self.ccy = (cmin[1], cmax[3]-2)

        self.aj = round(config.tailleCases/2)
        self.dif = round(config.tailleCases/5)

        x, y, x2, y2 = cmin[0], cmin[1], cmax[2]-2, cmax[3]-2
        self._tags = {'x':'cibleLigneH',
                      'y':'cibleLigneV',
                      'cercle':'cibleCercle'}

        self.ligneH = self.plateau.create_line(x, y + self.aj, x2-2,
                                               y + self.aj, fill=':cible',
                                               tags='{} {}'\
                                               .format('cible',
                                                    self._tags['x']),
                                                state=etat)
        self.ligneV = self.plateau.create_line(x + self.aj, y, x+self.aj, y2-2,
                                               fill=':cible',
                                               tags='{} {}'\
                                               .format('cible',
                                                    self._tags['y']),
                                                state=etat)


        self.cercle = self.plateau.create_oval(cmin[0] + self.dif,
                                               cmin[1] + self.dif,
                                               cmin[2] - self.dif,
                                               cmin[3] - self.dif,
                                               outline=':cible',
                                               tags='{} {}'\
                                               .format('cible',
                                                    self._tags['cercle']),
                                               state=etat)

        self.plateau.lift('cible')

    def deplacerLigneH(self, case) :
        '''
        Déplace la ligne horizontale sur la case spécifiée
        '''
        self.lift()
        cc = self.cg.coords(case)
        self.plateau.coords(self.ligneH, self.ccx[0], cc[1]+self.aj,
                            self.ccx[1], cc[1]+self.aj)

    def deplacerLigneV(self, case) :
        '''
        Déplace la ligne verticale sur la case spécifiée
        '''
        self.lift()
        cc = self.cg.coords(case)
        self.plateau.coords(self.ligneV, cc[0]+self.aj, self.ccy[0],
                            cc[0]+self.aj, self.ccy[1])

    def deplacerCercle(self, case) :
        '''
        Déplace le cercle sur la case spécifiée
        '''
        self.lift()
        x, y, x2, y2 = self.cg.coords(case)
        self.plateau.coords(self.cercle, x+self.dif, y+self.dif, x2-self.dif,
                            y2-self.dif)

    def deplacerCible(self, case) :
        '''
        Déplace la cible sur la case spécifiée
        '''
        self.deplacerLigneH(case)
        self.deplacerLigneV(case)
        self.deplacerCercle(case)

    def afficher(self, quoi=None) :
        '''
        Rend visible la cible entière ou un de ses éléments si « quoi » est
        spécifié.
        @param quoi : « x », « y » ou « cercle »
        '''
        if not quoi :
            self.itemconfigure('cible', state=tk.DISABLED)
        else :
            self._verifQuoi('afficher', quoi)
            self.plateau.itemconfigure(self._tags[quoi], state=tk.DISABLED)

    def cacher(self, quoi=None) :
        '''
        Rend invisible la cible entière ou un de ses éléments si « quoi » est
        spécifié.
        @param quoi : « x », « y » ou « cercle »
        '''
        if not quoi :
            self.plateau.itemconfigure('cible', state=tk.HIDDEN)
        else :
            self._verifQuoi('cacher', quoi)
            self.plateau.itemconfigure(self._tags[quoi], state=tk.HIDDEN)

    def lift(self) :
        '''
        Met en avant-plan la cible sur le plateau
        '''
        #self.plateau.after(20, self.plateau.lift('cible'))
        self.plateau.lift('cible')

    def detruire(self) :
        '''
        Supprime la cible du plateau
        '''
        self.plateau.delete('cible')

    def _verifQuoi(self, methode, valeur) :
        ''' Méthode interne '''
        '''
        Vérifie la validité du paramètre quoi des méthodes afficher et cacher
        '''
        if valeur not in self._tags.keys() :
            raise ValueError('{} n\'est pas une valeur valide pour le paramètre'
                             ' « quoi » de la méthode {}, valeurs autorisées :'
                             ' {}'.format(valeur, methode,
                                          ', '.join(self._tags.keys())))



class MethodeJeu :
    def __init__(self, plateau, appel, cg) :
        '''
        @param plateau  : plateau du jeu
        @param appel    : callable de retour devant être appelé
        @param cg       : instance d'une classe CasesGrille
        '''
        self.plateau = plateau
        self.appel = appel
        self.cg = cg

    def activer(self) :
        raise NotImplementedError('Cette méthode doit être redéfinie')

    def desactiver(self) :
        raise NotImplementedError('Cette méthode doit être redéfinie')

    def detruire(self) :
        raise NotImplementedError('Cette méthode doit être redéfinie')



class Souris(MethodeJeu) :
    '''
    Méthode de tir avec clic souris
    '''
    def __init__(self, plateau, appel, cg) :
        MethodeJeu.__init__(self, plateau, appel, None)
        self._bind = None

    def activer(self) :
        try :
            self.plateau.deletecommand(self._bind)
        except TypeError :
            pass
        self.bind = self.plateau.bind('<Button-1>', self.appel)

    def desactiver(self) :
        self.plateau.unbind('<Button-1>')

    def detruire(self) :
        self.desactiver()
        try :
            self.plateau.deletecommand(self._bind)
        except TypeError :
            pass



class Fleches(MethodeJeu) :
    '''
    Méthode de tir utilisant les flèches clavier, et barre d'espace pour
    validation du tir
    '''
    def __init__(self, plateau, appel, cg) :
        MethodeJeu.__init__(self, plateau, appel, cg)

        self._ciblePlateau = CiblePlateau(self.plateau, self.cg)
        # 1ère case ciblée au départ
        self._case = int(config.nombreCases/2)\
                    + (int(config.nombreCases/2)-1)\
                    * config.nombreCases
        self._ciblePlateau.deplacerCible(self._case)

        self._binds = [self.plateau.bind('<Up>',
                        lambda evt : self._temporiser(self.haut, evt)),
                      self.plateau.bind('<Down>',
                        lambda evt : self._temporiser(self.bas, evt)),
                      self.plateau.bind('<Left>',
                        lambda evt : self._temporiser(self.gauche, evt)),
                      self.plateau.bind('<Right>',
                        lambda evt : self._temporiser(self.droite, evt)),
                      ]

        self.delaiTemporisation = 150
        self._derniereAction = None
        self._timestampDerniereAction = float('inf')
        self._bind = None
        self.plateau.focus_set()


    def activer(self) :
        self.plateau.focus_set()
        try :
            self.plateau.deletecommand(self._bind)
        except TypeError :
            pass
        self.plateau.bind('<space>', self.tirer)

    def desactiver(self) :
        self.plateau.unbind('<space>')

    def haut(self) :
        if self._case - config.nombreCases <= 0 :
            self._case += (config.nombreCases - 1) * config.nombreCases
        else :
            self._case -= config.nombreCases
        self._ciblePlateau.deplacerLigneH(self._case)
        self._ciblePlateau.deplacerCercle(self._case)

    def bas(self) :
        if self._case + config.nombreCases > config.nombreCases ** 2 :
            self._case -= (config.nombreCases - 1) * config.nombreCases
        else :
            self._case += config.nombreCases
        self._ciblePlateau.deplacerLigneH(self._case)
        self._ciblePlateau.deplacerCercle(self._case)

    def gauche(self) :
        bg, bd = libs.bornesGrille(self._case, config.nombreCases)
        if self._case - 1 < bg :
            self._case = bd
        else :
            self._case -= 1
        self._ciblePlateau.deplacerLigneV(self._case)
        self._ciblePlateau.deplacerCercle(self._case)

    def droite(self) :
        bg, bd = libs.bornesGrille(self._case, config.nombreCases)
        if self._case + 1 > bd :
            self._case = bg
        else :
            self._case += 1
        self._ciblePlateau.deplacerLigneV(self._case)
        self._ciblePlateau.deplacerCercle(self._case)

    def tirer(self, evt) :
        cc = self.cg.coords(self._case)
        tk.Event.x, tk.Event.y = cc[0]+5, cc[1]+5
        self.appel(tk.Event)
        self.plateau.after(20, self._ciblePlateau.lift())

    def detruire(self) :
        self._ciblePlateau.detruire()
        for n in ('<Up>', '<Down>', '<Left>', '<Right>', '<space>') :
            self.plateau.unbind(n, None)
        for n in self._binds :
            self.plateau.deletecommand(n)
        if self._bind :
            self.plateau.deletecommand(self._bind)

    def _temporiser(self, deplacement, evt) :
        if self._derniereAction == deplacement.__name__\
           and evt.time - self._timestampDerniereAction\
            < self.delaiTemporisation :
            return
        self._derniereAction = deplacement.__name__
        self._timestampDerniereAction = evt.time
        deplacement()



