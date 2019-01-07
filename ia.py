#IA

import re
from random import choice, shuffle
from copy import deepcopy
from operator import itemgetter

import config 
from libs import Journalisation, bornesGrille, genItemListe

class IA :
    '''
    Joueur « virtuel » du jeu
    '''
    def __init__(self, nbCases, bateaux, bateauxAdjacents=False) :
        '''
        @param nbCases          : nombre de cases du côté de la grille
        @param bateaux          : liste des tailles de bateaux, par exemple :
                                  [5, 4, 3, 2, 2]
        @param bateauxAdjacents : spécifie si les bateaux sur la grille sont
                                  autorisés à être juxtaposés les uns aux autres
                                  False par défaut
        '''
        self._nbCases = nbCases
        self._tailleMinimumBateau = min(bateaux)
        self._taillesBateaux = bateaux.copy()

        self._casesTirees = set()
        self._exploitation = []

        self._mtb = False
        self._reportExclusion = False

        y = 1
        x = 1
        self._cases = ([], [])
        self._binaires = ([], [])
        while x <= self._nbCases :
            self._cases[0].append(tuple(range(y, y + self._nbCases)))
            self._cases[1].append(tuple(range(x, x + (self._nbCases - 1)\
                                                      * self._nbCases + 1,
                                                  self._nbCases)))
            self._binaires[0].append('0' * self._nbCases)
            self._binaires[1].append('0' * self._nbCases)
            y += self._nbCases
            x += 1

        posIndex = list(range(1, self._tailleMinimumBateau + 1))
        shuffle(posIndex)
        items = genItemListe(posIndex)

        self._bateauxAdjacents = bateauxAdjacents
        if bateauxAdjacents :
            self._ChoisirCasesExploitation = self._ChoisirCasesExploitationBA
        else :
            self.prochainTirages = []
            self._ChoisirCasesExploitation = self._ChoisirCasesExploitationBNA
            # Cases de coins (hg, hd, bg, bd) à exclure si les bateaux ne
            # peuvent être côte à côte
            self.casesCoins = (1, self._nbCases,
                               self._nbCases ** 2 - self._nbCases + 1,
                               self._nbCases ** 2)
            self.casesDiagonaleCoins = (1 + self._nbCases + 1,
                                        self._nbCases * 2 - 1,
                                        self.casesCoins[2] - self._nbCases + 1,
                                        self.casesCoins[3] - self._nbCases - 1)

        # Cases de bases à tirer par l'ia
        self._tirages = []
        index = 0
        y = 0
        case = 1
        while y < self._nbCases :
            index = next(items)
            while index <= self._nbCases :
                self._tirages.append(index + y * self._nbCases)
                index += self._tailleMinimumBateau
            y += 1

        # Séparation de la grille en « zones » de 3 ou 4 cases afin que les tirs
        # soient répartis plus ou moins uniformément sur la grille.
        # Notamment pour éviter que les tirs soient trop ciblés sur les mêmes
        # zones de la grille.
        zones = []
        # Taille de chaque zone doit valoir 3 ou 4
        i = 0
        while i < self._nbCases // 3 :
            zones.append(3)
            i += 1
        # Ajout des reliquats
        reste = self._nbCases % 3
        i = 0
        while i < reste :
            zones[i] += 1
            i += 1

        # De ces zones, on construit les listes des numéros de case qu'elles
        # contiennent.
        # Et par soucis de facilité/perfs, création d'une seconde liste
        # indiquant le ratio taille/contenance qui sera recalculé losqu'une de
        # ces cases sera tirée (supprimée)
        i = 0
        xi = 0
        yi = 1
        n = 1
        self._zonesCases = []
        self._zonesCasesRatio = []
        for y in zones :
            for x in zones :
                self._zonesCases.append([])
                self._zonesCasesRatio.append({})
                z = n
                zx = z + x
                while z < zx :
                    # On ne prend que les valeurs contenues dans self._tirages
                    cz = list(set(self._tirages)\
                              & set(range(z, n +nbCases*y, nbCases)))
                    self._zonesCases[i].extend(cz)
                    z += 1
                # Total des cases de la zone
                self._zonesCasesRatio[i]['taille'] = x * y
                # Nombre de cases pouvant être exploitées contenues dans la zone
                self._zonesCasesRatio[i]['nombre'] = len(self._zonesCases[i])
                # Ratio des 2
                self._zonesCasesRatio[i]['ratio'] = len(self._zonesCases[i])\
                                                       / (x * y)
                n += x
                i += 1
            n += (y-1) * nbCases

        self._tirerCase = self._zcTirerCase
        self._actualiserTirages = self._zcActualiserTirages
        
        self.journal = Journalisation(fichier=config.fichierLogIA)


    def tirer(self) :
        '''
        Tire et retourne une case au hasard ou une case parmi celles ciblées
        selon les indications fournies préalablement via la méthode
        explorerAutour.
        '''
        n = 0
        try :
            if self._exploitation :
                n = self._ChoisirCasesExploitation()
            if not n :
                n = self._tirerCase()
            self._actualiserTirages(n)
        except Exception as e :
            self.journal.debug('%s %s', type(e), e)
            raise type(e)(e)
        self.journal.info('IA tire en %s', n)
        return n


    def explorerAutour(self, case) :
        '''
        Méthode pour indiquer à l'ia qu'il faut explorer autour de la case
        spécifiée en paramètre.
        Cette méthode est à appeler dès lors qu'une case bateau adverse est
        touchée.
        '''
        self.journal.info('Touchée en %s', case)
        self.journal.info('Explore autour %s', case)
        if case in self._exploitation :
            self.journal.debug('Case déjà marquée à exploiter')
            raise ValueError('La case {} a déjà été marquée comme étant à'
                             ' exploiter'.format(case))
        self._exploitation.append(case)
        self.journal.info('Exploitation cases %s', self._exploitation)


    def supprimerCases(self, *cases) :
        '''
        Supprime la ou les cases fournies des cases pouvant être tirées par l'ia
        @param cases : entier(s)
        '''
        cases = list(cases)
        self.journal.info('Suppression cases %s', cases)
        if not self._bateauxAdjacents :
            for c, v in enumerate(self.casesDiagonaleCoins) :
                if v in cases and self.casesCoins[c] not in self._casesTirees :
                    cases.append(self.casesDiagonaleCoins[c])
        self._actualiserTirages(*cases)


    def supprimerBateau(self, cases) :
        '''
        Indique à l'ia de supprimer un bateau de taille indiquée de ceux à
        rechercher.
        @param cases : cases de la grille occupées par le bateau ayant été
                       coulé.

        Cette méthode est à appeler impérativement chaque fois qu'un bateau
        adverse est coulé.
        '''
        self.journal.info('Touché, coulé du bateau sur les cases'
                          ' %s, suppression du bateau', cases)
        try :
            self._taillesBateaux.remove(len(cases))
        except ValueError :
            self.journal.debug('Longueur bateau inexistante %s', cases)
            raise ValueError('Le bateau à supprimer n\'existe pas ou plus,'
                             'les cases {} indiquées sont incorrectes'\
                             .format(cases))

        for n in cases :
            try :
                self._exploitation.remove(n)
            except ValueError :
                continue

        if not self._bateauxAdjacents :
            self.journal.info('vide prochain tirages')
            self.prochainTirages.clear()

        # Dès le 1er bateau coulé, la méthode de tir passe en mode sur appui
        # binaire
        if not self._mtb :
            self.journal.info('Changement méthode tirage')
            self._actualiserBinaires(*self._casesTirees)
            del(self._zonesCases, self._zonesCasesRatio)
            self._tirerCase = self._binTirerCase
            self._actualiserTirages = self._binActualiserTirages
            self._mtb = True

        if not self._exploitation and self._reportExclusion :
            self.journal.info('Effectue report exclusion')
            self._exclureSequencesBinaires()

        if min(self._taillesBateaux) > self._tailleMinimumBateau :
            self.journal.info('Taille min bateau change')
            self._tailleMinimumBateau = min(self._taillesBateaux)
            if not self._exploitation :
                self._exclureSequencesBinaires()
            else :
                # Il y a encore des bateaux à trouver (bateaux pouvant être
                # juxtaposés), donc les exclusions de séquences trop petites ne
                # peut être effectuées tout de suite
                self.journal.info('Report des exclusions')
                self._reportExclusion = True


    def _actualiserGeneriques(self, *cases) :
        ''' Méthode interne '''
        '''
        Méthode interne générique s'occupant de mettre à jour les divers
        attributs de la classe selon les n° de cases fournis en paramètre.
        '''
        for n in cases :
            try :
                self._tirages.remove(n)
            except ValueError :
                continue
        self._casesTirees |= set(cases)

    def _espaceDisponible(self, case, axe) :
        ''' Méthode interne '''
        '''
        Détermine si à partir d'une case donnée et de l'axe donné, il y a assez
        d'espace disponible pour contenir la taille minimum d'un bateau.
        Retourne True si assez d'espace False autrement.
        @param case : case de la grille à partir de laquelle l'espace disponible
                      doit être recherché.
        @param axe  : axe de recherche « horizontal » ou « vertical »
        '''
        cases = self._casesTirees - set([case])
        i = 1
        if axe == 'horizontal' :
            bg, bd = bornesGrille(case, self._nbCases)
            if case > bg :
                n = case - 1
                while n >= bg :
                    if n in cases :
                        break
                    i += 1
                    n -= 1
            if case < bd :
                n = case + 1
                while n <= bd :
                    if n in cases :
                        break
                    i += 1
                    n += 1
        elif axe == 'vertical' :
            if case > self._nbCases :
                n = case - self._nbCases
                while n >= 1 :
                    if n in cases :
                        break
                    i += 1
                    n -= self._nbCases
            if case <= self._nbCases * (self._nbCases-1) :
                n = case + self._nbCases
                while n <= self._nbCases ** 2 :
                    if n in cases :
                        break
                    i += 1
                    n += self._nbCases
        else :
            raise ValueError('paramètre axe doit être « horizontal » ou'
                             ' « vertical », fourni : {}'.format(axe))
        return i >= self._tailleMinimumBateau



    def _choisirCase(self, cases) :
        ''' Méthode interne '''
        '''
        Méthode retournant une case en privilégiant la sélection de cases
        situées dans le même axe des précédents tirs.
        Si pas de possibilité, une case parmi celles fournies sera retournée
        en privilégiant également les cases situées dans le même axe, si leur
        nombre est évidement de 3.

        @param cases : cases représentant les voisines immédiates d'une case
        cible (1 à 4 cases).
        '''
        self.journal.debug('Choisit cases %s', cases)
        self.journal.debug('Exploitation %s', self._exploitation)
        possibilites = []
        if len(self._exploitation) > 1 :
            if self._exploitation[-1] + 1 in self._exploitation\
                or self._exploitation[-1] - 1 in self._exploitation :
                pas = 1
                borne1, borne2 = bornesGrille(self._exploitation[-1],
                                              self._nbCases)
                self.journal.debug('Pas établit à 1')
            elif self._exploitation[-1] + self._nbCases in self._exploitation\
               or self._exploitation[-1] - self._nbCases in self._exploitation :
                pas = self._nbCases
                borne1, borne2 = 1, self._nbCases**2
                self.journal.debug('Pas établit à %s', self._nbCases)
            else :
                self.journal.debug('Pas indéterminé...')
                return self._choisirCaseSelonAxe(cases)

            cmin, cmax = None, None
            # Sélection du min et/ou max de liste des cases à exploiter
            for n in self._exploitation[:-1] :
                if (self._exploitation[-1] - n) % pas == 0 :
                    if n < self._exploitation[-1] and (not cmin or n < cmin) :
                        cmin = n
                    elif n > self._exploitation[-1] and (not cmax or n > cmax) :
                        cmax = n
            # Si seulement min ou max, complément avec la dernière case de la
            # liste
            if not cmin and cmax :
                self.journal.debug('not cmin, cmax : %s', cmax)
                cmin = self._exploitation[-1]
            elif not cmax and cmin :
                self.journal.debug('not cmax, cmin : %s', cmin)
                cmax = self._exploitation[-1]
                
            possibilitesTemporaires = []

            if not cmin and not cmax :
                self.journal.debug('not cmin, not cmax')
                # Les 2 extrémités d'un même axe n'ayant rien donné, ce qui
                # implique que ce sont des bateaux différents qui ont été
                # touchés auparavant, retour sur la dernière case de la liste
                # pour sélectionner les cases de l'axe opposé.

                # Inversion du pas
                pas = self._nbCases if pas == 1 else 1
                if self._exploitation[-1] - pas >= borne1 :
                    possibilitesTemporaires.append(self._exploitation[-1] - pas)
                if self._exploitation[-1] + pas <= borne2 :
                    possibilitesTemporaires.append(self._exploitation[-1] + pas)
            else :
                if cmin and cmin - pas >= borne1 :
                    possibilitesTemporaires.append(cmin - pas)
                elif self._exploitation[-1] - pas >= borne1 :
                    possibilitesTemporaires.append(self._exploitation[-1] - pas)
                
                if cmax and cmax + pas <= borne2 :
                    possibilitesTemporaires.append(cmax + pas)
                elif self._exploitation[-1] + pas <= borne2 :
                    possibilitesTemporaires.append(self._exploitation[-1] + pas)
            possibilites.extend([n for n in possibilitesTemporaires\
                                 if n not in self._casesTirees])
        if not possibilites :
            self.journal.debug('Aucune possibilité')
            return self._choisirCaseSelonAxe(cases)
        else :
            self.journal.debug('Possibiltés : %s', possibilites)
            return choice(possibilites)


    def _choisirCaseSelonAxe(self, cases) :
        ''' Méthode interne '''
        '''
        Retourne une case parmi celles fournies, en privilégiant celles étant
        dans le même axe si leur nombre est de 3.

        @param cases : cases représentant les voisines IMMÉDIATES d'une case
        cible (1 à 4 cases)
        '''
        self.journal.debug('Selon axe %s', cases)
        possibilites = []
        if len(cases) != 3 :
            possibilites.extend(cases)
        else :
            self.journal.debug('3 cases')
            # Différence entre 2 cases opposées des cases
            for n in (2, self._nbCases * 2) :
                # nota bene : cases[0] - n peut être négatif, mais cela n'a
                # aucune incidence
                if cases.count(cases[0] + n) + cases.count(cases[0] - n) :
                    possibilites.append(cases[0])
                    try :
                        possibilites.append(cases[cases.index(cases[0] + n)])
                    except ValueError :
                        possibilites.append(cases[cases.index(cases[0] - n)])
                    break
            # Si 1ère valeur n'est pas sur même axe que la 2ème ou 3ème,
            # c'est que sont la 2ème et 3ème qui le sont.
            if not possibilites :
                possibilites.extend(cases[1:])
        self.journal.debug('Possibilités %s', possibilites)
        return choice(possibilites)


    def _ChoisirCasesExploitationBA(self) :
        ''' Méthode interne '''
        '''
        Méthode spécifique pour une grille où les bateaux peuvent être
        juxtaposés les uns aux autres, ce qui implique que 2 cases touchées
        l'une à côté de l'autre n'appartiennent pas obligatoirement au même
        bateau.
        '''
        vert, hor = True, True
        if len(self._exploitation) == 1 :
            hor = self._espaceDisponible(self._exploitation[0], 'horizontal')
            vert = self._espaceDisponible(self._exploitation[0], 'vertical')

        for case in self._exploitation[::-1] :
            possibilites = []
            if hor :
                bg, bd = bornesGrille(case, self._nbCases)
                if case - 1 >= bg and case - 1 not in self._casesTirees :
                    possibilites.append(case - 1)
                if case + 1 <= bd and case + 1 not in self._casesTirees :
                    possibilites.append(case + 1)
            if vert :
                if case - self._nbCases > 0\
                    and case -self._nbCases not in self._casesTirees :
                    possibilites.append(case - self._nbCases)
                if case + self._nbCases <= self._nbCases ** 2\
                    and case +self._nbCases not in self._casesTirees :
                    possibilites.append(case + self._nbCases)
            if not possibilites :
                continue
            self.journal.debug('Possibilites %s', possibilites)
            return self._choisirCase(possibilites)


    def _ChoisirCasesExploitationBNA(self) :
        ''' Méthode interne '''
        '''
        Méthode spécifique pour une grille où les bateaux ne peuvent être
        juxtaposés les uns aux autres, ce qui implique que 2 cases touchées
        l'une à côté de l'autre appartiennent obligatoirement au même bateau.
        '''
        if len(self._exploitation) > 1 :
            self._exploitation.sort()
            # on réinitialise l'attribut
            self.prochainTirages.clear()
            # On détermine dans quel sens il faut aller
            if self._exploitation[1] - self._exploitation[0] == 1 :
                # En horizontal donc :
                # tirage sur min - 1 ou max + 1
                # si possible selon les bornes g/d de la grille
                bg, bd = bornesGrille(max(self._exploitation), self._nbCases)
                if min(self._exploitation) - 1 >= bg :
                    self.prochainTirages.append(min(self._exploitation) - 1)
                if max(self._exploitation) + 1 <= bd :
                    self.prochainTirages.append(max(self._exploitation) + 1)
            else :
                if min(self._exploitation) - self._nbCases > 0 :
                    self.prochainTirages.append(min(self._exploitation)\
                                                    - self._nbCases)
                if max(self._exploitation)\
                       + self._nbCases <= self._nbCases ** 2  :
                    self.prochainTirages.append(max(self._exploitation)\
                                                    + self._nbCases)
        else :
            if not self.prochainTirages :
                if self._espaceDisponible(self._exploitation[0], 'horizontal') :
                    bg, bd = bornesGrille(self._exploitation[0], self._nbCases)
                    if self._exploitation[0] - 1 >= bg :
                        self.prochainTirages.append(self._exploitation[0] - 1)
                    if self._exploitation[0] + 1 <= bd :
                        self.prochainTirages.append(self._exploitation[0] + 1)
                if self._espaceDisponible(self._exploitation[0], 'vertical') :
                    if self._exploitation[0] - self._nbCases > 0 :
                        self.prochainTirages.append(self._exploitation[0]\
                                                    - self._nbCases)
                    if self._exploitation[0]\
                        + self._nbCases <= self._nbCases ** 2 :
                        self.prochainTirages.append(self._exploitation[0]\
                                                    + self._nbCases)
        # Exclusion des cases déjà tirées
        self.prochainTirages = list(set(self.prochainTirages)\
                                    - self._casesTirees)
        case = self._choisirCaseSelonAxe(self.prochainTirages)
        self.prochainTirages.remove(case)
        return case

    def _actualiserBinaires(self, *cases) :
        ''' Méthode Interne '''
        ''' Met à jour les listes binaires en fonction des cases tirées '''
        for l, c in enumerate(self._cases[0]) :
            for i, case in enumerate(c) :
                if case in cases :
                    self._binaires[0][l] = self._binaires[0][l][:i]\
                                        + '1' + self._binaires[0][l][i+1:]

        for l, c in enumerate(self._cases[1]) :
            for i, case in enumerate(c) :
                if case in cases :
                    self._binaires[1][l] = self._binaires[1][l][:i] + '1'\
                                        + self._binaires[1][l][i+1:]

    def _exclureSequencesBinaires(self) :
        ''' Méthode interne '''
        '''
        Met à 1 toutes les séquences de 0 inférieures à tailleMinimumBateau
        dans les listes binaires.
        '''
        lh, lv = set(), set()
        for ligne, sbin in enumerate(self._binaires[0]) :
            for seq in re.finditer('(?<!0)0{,'\
                    + str(self._tailleMinimumBateau-1) + '}?(?!0)', sbin) :
                for i in range(seq.start(), seq.end()) :
                    lh.add(self._cases[0][ligne][i])

        for colonne, sbin in enumerate(self._binaires[1]) :
            for seq in re.finditer('(?<!0)0{,'\
                    + str(self._tailleMinimumBateau-1) + '}?(?!0)', sbin) :
                for i in range(seq.start(), seq.end()) :
                    lv.add(self._cases[1][colonne][i])

        # Cases ne pouvant être occupées par un bateau
        self._actualiserTirages(*list(lh & lv))

    def _binTirerCase(self) :
        ''' Méthode interne '''
        '''
        Tirage sur appui binaire
        '''
        def adj(case) :
            # Fonction déterminant si la case fournie en paramètre est adjacente
            # à une case déjà tirée.
            bg, bd = bornesGrille(case, self._nbCases)
            ca = set()
            if case - 1 >= bg :
                ca.add(case-1)
            if case + 1 <= bd :
                ca.add(case+1)
            if case - self._nbCases > 0 :
                ca.add(case-self._nbCases)
            if case + self._nbCases < self._nbCases ** 2 :
                ca.add(case+self._nbCases)
            return bool(ca & self._casesTirees)


        # Explication des opérations effectuées dans la boucle
        # tmb = tailleMinimumBateau
        # Si la taille de la séquence est inférieure au double de tmb on prend
        # pour n premiers et derniers index à exclure ts - tmb
        # Sinon on prend tmb - 1
        # Ex : tmb = 3, seq = '00000' => ts = 5, on exclut donc ts - tmb (car
        # inf. à tmb*2) soit 2, on gardera donc l'index 2
        # Car on exclura les 2 premiers index 0 et 1, et les 2 derniers index 3
        # et 4
        #
        # Autre ex : tmb = 3, seq = '000000000' => ts = 9, ts >= tmb * 2, donc
        # on exclut tmb-1 premiers et derniers carac., on ne gardera donc que
        # les index de 3 à 5 inclus

        # listes de set contenant les priorités sur les tirages à faire
        lh = {'th':set(), 'h':set(), 'b':set(), 'tb':set()}
        lv = {'th':set(), 'h':set(), 'b':set(), 'tb':set()}

        for ligne, sbin in enumerate(self._binaires[0]) :
            for seq in re.finditer('0{'\
                        + str(self._tailleMinimumBateau) + ',}', sbin) :
                ts = len(seq.group(0))
                if ts < self._tailleMinimumBateau * 2 :
                    ph = False
                    indDeb = seq.start(0) + (ts - self._tailleMinimumBateau)
                    indFin = seq.end(0) - (ts - self._tailleMinimumBateau)
                else :
                    ph = True
                    indDeb = seq.start(0) + self._tailleMinimumBateau - 1
                    indFin = seq.end(0) - self._tailleMinimumBateau + 1

                while indDeb < indFin :
                    if ph :
                        if not adj(self._cases[0][ligne][indDeb]) :
                            lh['th'].add(self._cases[0][ligne][indDeb])
                        else :
                            lh['h'].add(self._cases[0][ligne][indDeb])
                    else :
                        if not adj(self._cases[0][ligne][indDeb]) :
                            lh['b'].add(self._cases[0][ligne][indDeb])
                        else :
                            lh['tb'].add(self._cases[0][ligne][indDeb])
                    indDeb += 1


        for colonne, sbin in enumerate(self._binaires[1]) :
            for seq in re.finditer('0{'\
                        + str(self._tailleMinimumBateau) + ',}', sbin) :
                ts = len(seq.group(0))
                if ts < self._tailleMinimumBateau * 2 :
                    ph = False
                    indDeb = seq.start(0) + (ts - self._tailleMinimumBateau)
                    indFin = seq.end(0) - (ts - self._tailleMinimumBateau)
                else :
                    ph = True
                    indDeb = seq.start(0) + self._tailleMinimumBateau - 1
                    indFin = seq.end(0) - self._tailleMinimumBateau + 1

                while indDeb < indFin :
                    if ph :
                        if not adj(self._cases[1][colonne][indDeb]) :
                            lv['th'].add(self._cases[1][colonne][indDeb])
                        else :
                            lv['h'].add(self._cases[1][colonne][indDeb])
                    else :
                        if not adj(self._cases[1][colonne][indDeb]) :
                            lv['b'].add(self._cases[1][colonne][indDeb])
                        else :
                            lv['tb'].add(self._cases[1][colonne][indDeb])
                    indDeb += 1

        n = 0
        choix = None
        for priorite in ('th', 'h', 'b', 'tb') :
            if lh[priorite] and lv[priorite] :
                choix = lh[priorite] & lv[priorite]
                if not choix :
                    choix = lh[priorite] | lv[priorite]
                break
            elif lh[priorite] or lv[priorite] :
                choix = lh[priorite] | lv[priorite]
                break

        # Sélection en priorité des cases étant présentes dans le tirage de base
        intersectionTirages = choix & set(self._tirages)
        if intersectionTirages :
            case = choice(list(intersectionTirages))
        else :
            case = choice(list(choix))
        return case

    def _binActualiserTirages(self, *cases) :
        ''' Méthode interne '''
        self._actualiserBinaires(*cases)
        self._actualiserGeneriques(*cases)

    def _zcIndexHautRatios(self) :
        ''' Méthode Interne '''
        ''' Retourne les index des zones ayant le plus gros ratio '''
        ratioMax = max(self._zonesCasesRatio, key=itemgetter('ratio'))['ratio']
        return [c for c, v in enumerate(self._zonesCasesRatio)\
                if v['ratio'] == ratioMax]

    def _zcActualiserRatios(self, *index) :
        ''' Méthode Interne '''
        ''' Met à jour les ratios des zones des index fournis '''
        for k in index :
            self._zonesCasesRatio[k]['nombre'] = len(self._zonesCases[k])
            self._zonesCasesRatio[k]['ratio'] =\
                                        self._zonesCasesRatio[k]['nombre']\
                                        / self._zonesCasesRatio[k]['taille']

    def _zcActualiserTirages(self, *cases) :
        ''' Méthode interne '''
        ''' Suppression des cases indiquées des zones '''
        index = []
        for c, v in enumerate(self._zonesCases) :
            for n in cases :
                try :
                    v.remove(n)
                except ValueError :
                    continue
                index.append(c)
        self._zcActualiserRatios(*index)
        self._actualiserGeneriques(*cases)

    def _zcTirerCase(self) :
        ''' Méthode Interne '''
        ''' Retourne une case parmi les zones ayant le plus gros ratio '''
        return choice(self._zonesCases[choice(self._zcIndexHautRatios())])



if __name__ == '__main__' :

    def genererGrille(taille, casesBateaux=[]) :
        '''
        Génération d'une grille en mode texte
        @param  casesBateaux : list des cases occupées par les bateaux
        '''
        h = ' -----'
        m = '|{}'
        n = 1
        i = 0
        grille = []
        while i < taille :
            lh, lm = '', ''
            j = 0
            while j < taille :
                case = str(n)
                if n in casesBateaux :
                    case = '* ' + case
                lh += h
                lm += m.format(case.center(5))
                j += 1
                n += 1
            grille.append(lh + ' ')
            grille.append(lm + '|')
            i += 1
        grille.append(lh + ' ')
        print('\n'.join(grille))

    #genererGrille(12, [4, 5, 6, 15, 27, 39, 105, 117, 129, 141])

