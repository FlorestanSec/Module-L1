#Disposition

from random import choice

import config
import composants
from libs import CasesGrille, bornesGrille

HORIZONTAL, VERTICAL = 0, 1

class DispositionManuelle :
    '''
    Disposition manuelle des bateaux sur la grille
    '''
    def __init__(self, plateau, bateauxAdjacents, zoneBoutons) :
        '''
        @param plateau          : plateau du jeu
        @param bateauxAdjacents : booléen spécifiant si les bateaux peuvent être
                                  juxtaposés les uns aux autres
        @param zoneBoutons      : zone de la fenêtre où les boutons de jeu
                                  doivent être affichés
        '''
        self.plateau = plateau
        self.bateauxAdjacents = bateauxAdjacents
        self.plateau.bind('<Button-1>', self.selectionBateau)
        self.plateau.bind('<Button1-ButtonRelease>', self.bateauEnSelection)
        self.plateau.bind('<Motion>', self.bougerBateau)
        self.plateau.bind('<Button-3>', self.inverserOrientation)

        self.bateauId = 0
        self.etape = 1
        self.orientationBateau = HORIZONTAL
        self.peutCommencer = False
        self.bateauxPlaces = {}

        self.message = composants.MessagePlateau(self.plateau)
        self.message('message_disposition_selectionner')

        self.grille = composants.GrillePlateau(self.plateau, config.margeGrille,
                                               config.margeGrille)
        self.grille.graduer()

        self.boutons = composants.Boutons(zoneBoutons)
        self.boutonCommencer = self.boutons.creer('bouton_commencer',
                                                  self.commencer, False)
        self.boutonAleatoire = self.boutons.creer('bouton_hasard',
                                                  self.aleatoire, True)
        self.boutons.ancrer()

        self.flotte = composants.FlottePlateau(self.plateau)
        self.cg = CasesGrille(config.margeGrille, config.margeGrille,
                              config.nombreCases, config.tailleCases)

    def curseur(self, evt) :
        oids = self.plateau.find_overlapping(evt.x, evt.y, evt.x, evt.y)
        bats = [v for v in oids if v in self.flotte.bateauxIds]
        if bats :
            self.plateau.configure(cursor='hand2')
        else :
            self.plateau.configure(cursor='left_ptr')


    def aleatoire(self) :
        '''
        Positionne aléatoirement les bateaux sur la grille
        '''
        da = DispositionAleatoire(self.bateauxAdjacents)
        for index, cases in da.positionner().items() :
            self.bateauxPlaces[self.flotte.idIndex(index)] = cases
            self.flotte.bateau(self.flotte.idIndex(index))\
                                .deplacerSur(*self.cg.coords(*cases))
        self.etape = 1
        self.peutCommencer = True
        self.boutonCommencer.activer()
        self.message('message_disposition_commencer', 'bien')

    def commencer(self) :
        if self.peutCommencer :
            bateaux = {}
            indexBateaux = self.flotte.index
            for i, _ in enumerate(config.bateaux) :
                bateaux[i] = self.bateauxPlaces[self.flotte.idIndex(i)]
            config.commencer(bateaux)


    def selectionBateau(self, event) :
        if self.etape == 1 : # 1er clic pressé
            self.x, self.y = event.x, event.y
            ids = self.plateau.find_overlapping(event.x, event.y, event.x,
                                                event.y)
            ids = [v for v in ids if v in self.flotte.bateauxIds]
            if ids :
                self.bateauId = ids[0]
                self.etape = 2
                self.peutCommencer = False
        elif self.etape == 3 : # 2nd clic enfoncé
            self.etape = 4

    def bateauEnSelection(self, event):
        if self.etape == 2 : # 1er clic relâché
            if self.bateauId in self.bateauxPlaces.keys() :
                if self.bateauxPlaces[self.bateauId][1]\
                   - self.bateauxPlaces[self.bateauId][0] == 1 :
                    self.orientationBateau = HORIZONTAL
                else :
                    self.orientationBateau = VERTICAL
                del(self.bateauxPlaces[self.bateauId])
                self.boutonCommencer.desactiver()

            # Repositionnement du bateau afin que le curseur se situe sur son
            # côté gauche (centre de la case la plus à gauche) afin que
            # lorsqu'on change sa position vertical <=> horizontal, le curseur
            # ne se retrouve pas hors de son périmètre.
            coords = self.flotte.bateau(self.bateauId).coords
            self.x, self.y = event.x, event.y
            x = event.x - coords[0] - config.tailleCases/2 + coords[0]
            y = event.y - coords[1] - config.tailleCases/2 + coords[1]

            self.flotte.bateau(self.bateauId).deplacerSur(x, y,
                                                          x+coords[2]-coords[0],
                                                          y+coords[3]-coords[1])
            self.message('message_disposition_placer')
            self.etape = 3

        elif self.etape == 4 :
            destinationBonne = True
            # Vérification que l'on peut le déposer sur un endroit autorisé.
            case = self.cg.point(event.x, event.y)
            if case :
                cases = [case]
                if self.orientationBateau == HORIZONTAL :
                    bornes = bornesGrille(case, config.nombreCases)
                    for n in range(case + 1,
                                   case\
                                   + self.flotte.bateau(self.bateauId).taille) :
                        if n <= bornes[1] :
                            cases.append(n)
                        else :
                            destinationBonne = False
                            break
                else :
                    for n in range(case + config.nombreCases,
                       case + (self.flotte.bateau(self.bateauId).taille - 1)\
                       * config.nombreCases + 1, config.nombreCases) :
                        if n <= config.nombreCases ** 2 :
                            cases.append(n)
                        else :
                            destinationBonne = False
                            break
            else :
                destinationBonne = False

            if destinationBonne and self.bateauxPlaces :
                for c, v in self.bateauxPlaces.items() :
                    if set(cases) & set(v) :
                        destinationBonne = False
                        self.message('message_disposition_superposition',
                                     'attention')
                        break

            if destinationBonne and self.bateauxPlaces\
               and not self.bateauxAdjacents :
                # Les bateaux ne sont pas autorisés à être juxtaposés
                adj = set(self.cg.adjacentes(*cases))
                for casesBateaux in self.bateauxPlaces.values() :
                    if adj & set(casesBateaux) :
                        self.message('message_disposition_contigu', 'attention')
                        destinationBonne = False
                        break

            if destinationBonne :
                self.flotte.bateau(self.bateauId)\
                    .deplacerSur(*self.cg.coords(*cases))
                self.orientationBateau = HORIZONTAL
                self.etape = 1
                self.bateauxPlaces[self.bateauId] = cases
                if len(self.bateauxPlaces) == len(config.bateaux) :
                    self.boutonCommencer.activer()
                    self.peutCommencer = True
                    self.message('message_disposition_commencer', 'bien')
                else :
                    self.message('message_disposition_selectionner')
            else :
                # Si le clic a été effectué »» SUR la grille ««
                # (éventuellement un clic sur une des lignes, un positionnement
                # non possible)
                ids = self.plateau.find_overlapping(event.x, event.y, event.x,
                                                    event.y)
                if self.grille.id in ids :
                    self.etape = 3
                else :
                    # Renvoi du bateau sur sa base, le clic a été fait hors de
                    # la grille
                    self.flotte.bateau(self.bateauId)\
                       .deplacerSur(*self.flotte.bateau(self.bateauId).socle)
                    self.etape = 1
                    self.orientationBateau = HORIZONTAL
                    self.message('message_disposition_selectionner')

    def bougerBateau(self, event) :
        self.curseur(event)
        if self.etape == 3 :
            dx, dy = event.x -self.x, event.y -self.y
            self.flotte.bateau(self.bateauId).deplacer(dx, dy)
            self.x, self.y = event.x, event.y

    def inverserOrientation(self, event) :
        if self.etape == 3 :
            coords = self.flotte.bateau(self.bateauId).coords
            x2 = coords[0] + (coords[3] - coords[1])
            y2 = coords[1] + (coords[2] - coords[0])
            self.flotte.bateau(self.bateauId)\
                .deplacerSur(coords[0], coords[1], x2, y2)
            self.orientationBateau = HORIZONTAL\
                    if self.orientationBateau == VERTICAL else VERTICAL

    def detruire(self) :
        '''
        Détruit les boutons
        '''
        self.boutonCommencer.destroy()
        self.boutonAleatoire.destroy()
        del(self.boutonCommencer)
        del(self.boutonAleatoire)



class DispositionAleatoire :
    def __init__(self, bateauxAdjacents) :
        self.bateauxAdjacents = bateauxAdjacents
        self.totalCases = config.nombreCases ** 2
        self._nbTentative = 0
        self._nbMaxTentative = 100

    def _selectionnerPositions(self, casesDisponibles, tailleBateau) :
        ''' Méthode interne récursive '''
        try :
            n = choice(casesDisponibles)
        except IndexError :
            return None

        bg, bd = bornesGrille(n, config.nombreCases)
        positionnements = {}

        if n - (tailleBateau-1) * config.nombreCases > 0 :
            positionnements['N'] = list(range(n-(tailleBateau-1)\
                                        *config.nombreCases, n+1,
                                        config.nombreCases))
        if n + (tailleBateau-1) * config.nombreCases < self.totalCases :
            positionnements['S'] = list(range(n, n+(tailleBateau-1)\
                                        *config.nombreCases+1,
                                        config.nombreCases))
        if n + tailleBateau - 1 <= bd :
            positionnements['E'] = list(range(n, n+tailleBateau))
        if n - tailleBateau - 1 >= bg :
            positionnements['O'] = list(range(n-tailleBateau+1, n+1))

        if positionnements :
            for c, v in positionnements.copy().items() :
                if set(v) & set(casesDisponibles) != set(v) :
                    del(positionnements[c])
                else :
                    # Juxtaposition de bateux interdites
                    if not self.bateauxAdjacents :
                        adjacentes = []
                        # Vérifications des adjacentes
                        if c in ('N', 'S') :
                            if min(v) - config.nombreCases > 0 :
                                adjacentes.append(min(v)-config.nombreCases)
                            if max(v) + config.nombreCases <= self.totalCases :
                                adjacentes.append(max(v) + config.nombreCases)

                            bgNS, bdNS = bornesGrille(min(v),
                                                      config.nombreCases)
                            if min(v) + 1 <= bdNS :
                                adjacentes.extend([i + 1 for i in v])
                            if min(v) - 1 >= bgNS :
                                adjacentes.extend([i - 1 for i in v])
                        else :
                            if min(v) - 1 >= bg :
                                adjacentes.append(min(v) - 1)
                            if max(v) + 1 <= bd :
                                adjacentes.append(max(v) + 1)
                            if min(v) - config.nombreCases > 0 :
                                adjacentes.extend([i
                                            - config.nombreCases for i in v])
                            if min(v) + config.nombreCases <= self.totalCases :
                                adjacentes.extend([i + config.nombreCases
                                                   for i in v])

                        if set(adjacentes) & set(casesDisponibles)\
                                                            != set(adjacentes) :
                            del(positionnements[c])

        # Si positionnements est vide, c'est que les cases du bateau ou leurs
        # cases adjacentes ne sont pas disponibles
        if not positionnements :
            casesDisponibles.remove(n)
            return self._selectionnerPositions(casesDisponibles, tailleBateau)
        else :
            d = choice(list(positionnements.keys()))
            for v in positionnements[d] :
                casesDisponibles.remove(v)
            return positionnements[d]

    def positionner(self, nbt=0, maxt=100) :
        '''
        Positionne aléatoirement les bateaux sur la grille et retourne un dict
        avec pour clés les ids des bateaux, et pour valeurs la liste des numéros
        de cases sur lesquelles ils se situent.
        '''

        # Ceci ne devrait jamais se produire car le maximum de cases bateaux ne
        # doit jamais excéder 1/4 du nombre total de cases de la grille.
        if nbt == maxt :
            raise RuntimeError('Il n\'a pas été possible de placer après {}'
                               ' tentatives les bateaux sur la grille'\
                               .format(maxt))
        casesDisponibles = list(range(1, self.totalCases+1))
        pos = {}

        for i, taille in enumerate(config.bateaux) :
            sp = self._selectionnerPositions(casesDisponibles, taille)
            if not sp :
                return self.positionner(nbt+1, maxt)
            pos[i] = sp
        self._nbt = nbt
        return pos

    @property
    def nbt(self) :
        '''
        Retourne le nombre de tentatives de positionnements de la dernière
        exécution de positionner
        '''
        return self._nbt
