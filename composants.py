#Composant

import tkinter as tk
import config
import libs

class PhotoImage(tk.PhotoImage) :
    def __del__(self) :
        try :
            super().__del__()
        except TypeError :
            pass



class TkComplementWidget :
    '''
    Classe « modifiant » le comportement de widget tkinter, ceci afin de pouvoir
    mofifier thème et langue de l'application lors de l'exécution.
    '''
    def __init__(self, optionsCouleurs, **options) :
        '''
        @param optionsCouleurs : noms des options du widget tkinter comportant
                                 des valeurs de couleurs.
        @param options : options du widget tkinter fournis au widget.

        Fonctionnement :
            - Gestion dynamique de la langue :
                Un item var (inexistant dans les options de widget tkinter) peut
                être ajouté dans les options.
                Il doit avoir impérativement pour valeur un identifiant de
                config.langue.
                L'ajout de cet item var dans les options permettra une mise à
                jour automatique de la langue de l'application lors d'un
                changement par l'utilisateur.
            - Gestion dynamique des couleurs du thème :
                Pour définir l'identifiant du thème que l'on souhaite utiliser
                dans l'option du widget pouvant reçevoir une couleur (spécifiés
                dans optionsCouleurs), il suffit de définir à l'instance comme
                normalement en spécifiant l'option, mais en mettant « : » en 1er
                caractère de la valeur pour indiquer que ceci est un identifiant
                thème.
                Exemples : bg=':id_bg_theme', fg=':id_fg_theme'
                Ceci fait, chaque changement de thème par l'utilisateur mettra
                à jour toutes les options définies de cette façon.

        IMPORTANT :
        Une fois l'instance du widget tkinter créée, la méthode
        configurerCouleurs doit être obligatoirement appelée pour que les
        couleurs soient prises en compte et s'appliquent au widget.
        '''
        self.inscription = False
        self.optionsCouleurs = optionsCouleurs
        self.options = self._tkcwVar(options)
        self.options = self._tkcwCouleurs(self.options)

    def configurerCouleurs(self) :
        ''' Applique les couleurs du thème aux widgets '''
        if self.inscription :
            config.rtheme.changer(self)

    def configure(self, cnf={}, **options) :
        ''' Surcharge de la méthode configure de tkinter '''
        options.update(cnf)
        if not options :
            return self._configure('configure', None, None)

        options = self._tkcwVar(options)
        options = self._tkcwCouleurs(options)
        self._configure('configure', options, None)


    def _tkcwVar(self, options) :
        ''' Méthode interne '''
        if 'var' in options.keys() :
            options['textvariable'] = config.rlangue.var(options['var'], self)
            del(options['var'])
        return options

    def _tkcwCouleurs(self, options) :
        ''' Méthode interne '''
        for n in self.optionsCouleurs :
            if n in options.keys() and options[n][0] == ':' :
                self.inscription = True
                config.rtheme.inscrire(self, **{n:options[n][1:]})
                del(options[n])
        return options

    def destroy(self) :
        ''' Surcharge de la méthode destroy de tkinter '''
        config.rtheme.radier(self)
        config.rlangue.radier(self)
        super().destroy()



class Canvas(TkComplementWidget, tk.Canvas) :
    '''
    À l'instar de TkComplementWidget, pour la gestion dynamique des changements
    de langues et thèmes, cette classe applique le même principe aux composants
    canevas comportant des options couleurs, et texte (create_text).
    Le fonctionnement est identique (se référer à TkComplementWidget), exemple
    pour le thème :
    can.create_rectangle(.., fill=':id_theme_truc', outline=':id_theme_bidule')
    Pour la gestion de la langue, une option var peut être ajouté uniquement à
    create_text comme dans TkComplementWidget, exemple :
    can.create_text(..., fill=':id_theme_untexte', var='id_langue')
    '''
    def __init__(self, parent, **options) :
        oc = ('bg', 'background', 'hightlightbackground', 'hightlightcolor',
              'selectbackground', 'selectforeground')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Canvas.__init__(self, parent, **self.options)
        self.configurerCouleurs()

        self._tkccListeOid = []
        self._tkccListeTexteId = []

    def _create(self, type_, args, dargs) :
        '''
        Surcharge de la méthode _create de tk.Canvas
        '''
        vid = None
        options, ot = self._tkccOptions(dargs)
        if type_ == 'text' :
            options, vid = self._tkccTexteVar(options)
        oid = super()._create(type_, args, options)
        if ot :
            config.rtheme.inscrireCoid(self, oid, **ot)
            self._tkccListeOid.append(oid)
        if vid :
            config.rlangue.canvar(vid, self, oid)
            self._tkccListeTexteId.append(oid)
        return oid

    def delete(self, oid=None) :
        '''
        Surcharge de la méthode delete de tk.Canvas
        '''
        if oid in self._tkccListeTexteId :
            self._tkccListeTexteId.remove(oid)
            config.rlangue.radierCanvar(self, oid)
        if oid in self._tkccListeOid :
            self._tkccListeOid.remove(oid)
            config.rtheme.radierCoid(self, oid)
        super().delete(oid)

    def itemconfigure(self, oid, cnf={}, **options) :
        '''
        Surcharge de la méthode itemconfigure de tk.Canvas
        '''
        options.update(cnf)
        if not options :
            return self._configure(('itemconfigure', oid), None, None)
        options, vid = self._tkccTexteVar(options)
        if vid :
            if self.type(oid) != 'text' :
                raise TypeError('L\'identifiant canevas fourni n\'est pas de'
                                ' type text et ne possède donc pas d\'attribut'
                                ' var')
            config.rlangue.canvar(vid, self, oid)

        options, ot = self._tkccOptions(options)
        if ot :
            config.rtheme.inscrireCoid(self, oid, **ot)
        if options :
            self._configure(('itemconfigure', oid), None, options)

    def _tkccOptions(self, options) :
        ''' Méthode interne '''
        ot = {}
        for c, v in options.copy().items() :
            if c in ('fill', 'activefill', 'disabledfill', 'outline',
                     'activeoutline', 'disabledoutline') and v[0] == ':' :
                ot[c] = v[1:]
                del(options[c])
        return (options, ot)

    def _tkccTexteVar(self, options) :
        ''' Méthode interne '''
        vid = None
        if 'var' in options.keys() :
            vid = options['var']
            del(options['var'])
        return(options, vid)



class Menu(TkComplementWidget, tk.Menu) :
    '''
    À l'instar de TkComplementWidget, pour la gestion dynamique des changements
    de langues et thèmes, cette classe applique le même principe aux items d'un
    menu comportant des options de couleurs, et label.
    Le fonctionnement est identique (se référer à TkComplementWidget), exemple :
    unMenu = Menu(...) # tk.Menu
    unMenu.add_command(var='id_valeur_langue', background=':id_valeur_theme')
    '''
    def __init__(self, parent=None, **options) :
        oc = ('activebackground', 'activeforeground', 'bg', 'background',
              'disabledforeground', 'fg', 'foreground', 'selectcolor')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Menu.__init__(self, parent, **self.options)
        self.configurerCouleurs()

        self._tkcmIndex = 0

    def add(self, type_, cnf={}, **options) :
        '''
        Surcharge de la méthode add de tk.Menu
        '''
        # (!) : toutes les options des add_n sont passées dans cnf par tkinter
        options.update(cnf)
        vid = None
        if type_ == tk.COMMAND :
            options, vid = self._tkcmLabelVar(options)
        options, ot = self._tkcmOptions(options)

        self.tk.call((self._w, 'add', type_) + self._options(options, {}))
        if vid :
            config.rlangue.labelvar(vid, self, self._tkcmIndex)
        if ot :
            config.rtheme.inscrireMenuIndex(self, self._tkcmIndex, **ot)
        self._tkcmIndex += 1


    def entryconfigure(self, index, cnf={}, **options):
        '''
        Surcharge de la méthode entryconfigure de tk.Menu
        '''
        options.update(cnf)
        if not options :
            return self._configure(('entryconfigure', index), None, None)
        options, vid = self._tkcmLabelVar(options)
        options, ot = self._tkcmOptions(options)
        if vid :
            if self.type(index) != tk.COMMAND :
                raise TypeError('L\'index menu fourni n\'est pas de type'
                                'command et ne possède donc pas d\'attribut'
                                ' var')
        if ot :
            config.rtheme.inscrireMenuIndex(self, self._tkcmIndex, **ot)
        if options :
            self._configure(('entryconfigure', index), options, None)


    def _tkcmOptions(self, options) :
        ''' Méthode interne '''
        ot = {}
        for c, v in options.copy().items() :
            if c in ('activebackground', 'activeforeground', 'background',
                     'foreground') and v[0] == ':' :
                ot[c] = v[1:]
                del(options[c])
        return (options, ot)


    def _tkcmLabelVar(self, options) :
        ''' Méthode interne '''
        vid = None
        if 'var' in options.keys() :
            vid = options['var']
            del(options['var'])
        return(options, vid)



class Label(TkComplementWidget, tk.Label) :
    def __init__(self, parent, **options) :
        oc = ('activebackground', 'activeforeground', 'bg', 'background',
              'disabledforeground', 'fg', 'foreground', 'highlightbackground',
              'highlightcolor')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Label.__init__(self, parent, **self.options)
        self.configurerCouleurs()



class Message(TkComplementWidget, tk.Message) :
    def __init__(self, parent, **options) :
        oc = ('bg', 'background','fg', 'foreground', 'highlightbackground',
              'highlightcolor')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Message.__init__(self, parent, **self.options)
        self.configurerCouleurs()



class Frame(TkComplementWidget, tk.Frame) :
    def __init__(self, parent=None, **options) :
        oc = ('bg', 'background', 'highlightbackground', 'highlightcolor')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Frame.__init__(self, parent, **self.options)
        self.configurerCouleurs()



class Button(TkComplementWidget, tk.Button) :
    def __init__(self, parent=None, **options) :
        oc = ('activebackground', 'activeforeground', 'bg', 'background',
              'disabledforeground', 'fg', 'foreground', 'highlightbackground',
              'highlightcolor')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Button.__init__(self, parent, **self.options)
        self.configurerCouleurs()



class Menubutton(TkComplementWidget, tk.Menubutton) :
    def __init__(self, parent=None, **options) :
        oc = ('activebackground', 'activeforeground', 'bg', 'background',
              'disabledforeground', 'fg', 'foreground', 'highlightbackground',
              'highlightcolor')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Menubutton.__init__(self, parent, **self.options)
        self.configurerCouleurs()


"""
#XXX Ne sert pas dans l'appli
class Spinbox(TkComplementWidget, tk.Spinbox) :
    def __init__(self, parent=None, **options) :
        oc = ('activebackground', 'bg', 'background', 'buttonbackground',
              'disabledbackground', 'disabledforeground', 'fg', 'foreground',
              'highlightbackground', 'highlightcolor', 'insertbackground',
              'readonlybackground', 'selectbackground', 'selectforeground')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Spinbox.__init__(self, parent, **self.options)
        self.configurerCouleurs()



#XXX Ne sert pas dans l'appli
class Text(TkComplementWidget, tk.Text) :
    def __init__(self, parent=None, **options) :
        oc = ('activebackground', 'activeforeground', 'background', 'bg',
              'disabledforeground', 'foreground', 'fg', 'selectcolor')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Text.__init__(self, parent, **self.options)
        self.configurerCouleurs()
"""


class Toplevel(TkComplementWidget, tk.Toplevel) :
    def __init__(self, parent=None, **options) :
        oc = ('background', 'bg', 'highlightbackground', 'highlightcolor')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Toplevel.__init__(self, parent, **self.options)
        self.configurerCouleurs()

    def titre(self, idLangue) :
        '''
        Définit le title de la toplevel
        @param idLangue : identifiant dans config.langue
        '''
        config.rlangue.titlevar(idLangue, self)

    def destroy(self) :
        ''' Surcharge de la méthode destroy de tkinter '''
        config.rlangue.radierTitlevar(self)
        super().destroy()



class Entry(TkComplementWidget, tk.Entry) :
    def __init__(self, parent=None, **options) :
        oc = ('background', 'bg', 'disabledbackground', 'disabledforeground',
              'fg', 'foreground', 'highlightbackground', 'highlightcolor',
              'insertbackground', 'readonlybackground', 'selectbackground',
              'selectforeground')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Entry.__init__(self, parent, **self.options)
        self.configurerCouleurs()



class Radiobutton(TkComplementWidget, tk.Radiobutton) :
    def __init__(self, parent=None, **options) :
        oc = ('activebackground', 'activeforeground', 'background', 'bg',
              'foreground', 'fg', 'disabledforeground', 'highlightbackground',
              'highlightcolor', 'selectcolor')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Radiobutton.__init__(self, parent, **self.options)
        self.configurerCouleurs()



class Scrollbar(TkComplementWidget, tk.Scrollbar) :
    def __init__(self, parent=None, **options) :
        oc = ('activebackground', 'background', 'bg', 'highlightbackground',
              'highlightcolor', 'troughcolor')
        TkComplementWidget.__init__(self, oc, **options)
        tk.Scrollbar.__init__(self, parent, **self.options)
        self.configurerCouleurs()



class Cadre(Frame) :
    def __init__(self, parent=None, **options) :
        Frame.__init__(self, parent, **options)
        self.grid()

    def vider(self) :
        for oid in self.winfo_children() :
            oid.destroy()



class Fenetre(tk.Tk) :

    def agencer(self) :
        '''
        Crée et organise les éléments principaux de la fenêtre
        '''
        self.fenetre = Cadre(self, bg=':fenetre')
        x = int((self.winfo_screenwidth() - config.largeurFenetre) / 2)
        y = int((self.winfo_screenheight() - config.hauteurFenetre) / 2)
        self.geometry('{}x{}+{}+{}'.format(config.largeurFenetre,
                                           config.hauteurFenetre, x, y))
        self.fenetre.grid()

        self.icone = PhotoImage(file=config.repertoireImages\
                                        + 'icone_bateau32.gif')
        self.iconposition(x=10, y=0) # Fonctionne pas chez moi (*_°)
        self.iconphoto(True, self.icone)

        self._haut = Cadre(self.fenetre, width=config.largeurFenetre,
                           height=config.hauteurZoneSuperieure, bg=':fenetre')
        self._haut.grid()
        self._haut.grid_propagate(0)
        self._haut.columnconfigure(1, weight=0)
        self._haut.columnconfigure(2, weight=1)

        menu = OptionsJeu(self._haut)

        frameGrilleJeu = Frame(self.haut)
        frameGrilleJeu.grid(row=1, column=2)
        labelJeu = LabelGrilleJeu(frameGrilleJeu, var='jeu',
                        font=(config.famillesPolice.serif, -15))
        labelJeu.grid(row=1, column=1)
        self._labelGrilleJeu = LabelGrilleJeu(frameGrilleJeu,
                                        font=(config.famillesPolice.serif, -15))
        self._labelGrilleJeu.grid(row=1, column=2)

        self._centre = Cadre(self.fenetre, width=config.largeurFenetre,
                             height=config.hauteurPlateau, bg=':fenetre')
        self._centre.grid()

        self._plateau = Plateau(self._centre)
        self._plateau.grid()

        self._bas = Cadre(self.fenetre, bg=':fenetre',
                          width=config.largeurFenetre,
                          height=config.hauteurZoneInferieure)
        self._bas.grid()
        self._bas.grid_propagate(0)
        self._bas.rowconfigure(1, weight=1)

        config.fenetreHaut = self.haut
        config.fenetreCentre = self.centre
        config.fenetreBas = self.bas

    def grilleJeu(self, nom) :
        '''
        Définit le nom du jeu en cours dans la frame haut de la fenêtre
        '''
        self._labelGrilleJeu.configure(var='grille_{}_nom'.format(nom))

    @property
    def haut(self) :
        ''' Retourne le cadre supérieur de la fenêtre '''
        return self._haut

    @property
    def centre(self) :
        ''' Retourne le cadre central de la fenêtre '''
        return self._centre

    @property
    def bas(self) :
        ''' Retourne le cadre inférieur de la fenêtre '''
        return self._bas

    @property
    def plateau(self) :
        ''' Retourne le plateau du jeu (canevas tkinter) '''
        return self._plateau



class OptionsJeu :
    ''' Menu des options du jeu '''
    def __init__(self, parent) :
        self.parent = parent

        # Menu principal
        self.menuOptions = Menubutton(self.parent, var='menu_options',
                                      bg=':menu_normal_fond',
                                      fg=':menu_normal_texte',
                                      activebackground=':menu_survol_fond',
                                      activeforeground=':menu_survol_texte',
                                      highlightbackground\
                                                    =':menu_normal_surlignage',
                                      highlightcolor=':menu_focus_surlignage',
                                      highlightthickness=1,
                                      relief=tk.FLAT, bd=0,
                                      font=(config.famillesPolice.serif, -13),
                                      padx=10, pady=0, takefocus=True)

        hautMenu = self.menuOptions.winfo_reqheight()
        pady = 0
        if hautMenu <  config.hauteurZoneSuperieure :
            pady = int((config.hauteurZoneSuperieure - hautMenu) / 2)


        self.menuOptions.grid(row=1, column=1, sticky=tk.SW)
        # Sous-menu
        self.sousMenuOptions = Menu(self.menuOptions, bg=':menu_normal_fond',
                                    fg=':menu_normal_texte',
                                    activebackground=':menu_survol_fond',
                                    activeforeground=':menu_survol_texte',
                                    relief=tk.FLAT, bd=0,
                                    font=(config.famillesPolice.serif, -13),
                                    tearoff=0)
        self.menuOptions.configure(menu=self.sousMenuOptions, pady=pady)

        for nom, cmd in config.optionsCommandes :
            n = self.sousMenuOptions.add_command(var=nom, command=cmd)



class Boutons :
    '''
    Destiné à afficher plusieurs boutons et UNIQUEMENT EUX dans une frame, pour
    pouvoir les centrer horizontalement en fonction du nombre de boutons.
    '''
    def __init__(self, parent) :
        self.bids = []
        self.parent = parent

    def creer(self, texte, cmd, etat=True) :
        '''
        Crée un bouton
        @param texte    : texte du bouton
        @param cmd      : commande du bouton
        @param etat     : booléen, etat du bouton, actif, inactif
        '''
        bid = Bouton(self.parent, var=texte, command=cmd, actif=etat)
        self.bids.append(bid)
        return bid

    def ancrer(self) :
        ''' Grid et centre les boutons au parent spécifié '''
        col = 1
        nbCol = len(self.bids)
        optionsGrid = dict(row=1, padx=15)
        for b in self.bids :
            optionsGrid['column'] = col
            if col == 1 :
                optionsGrid['sticky'] = tk.E
                self.parent.columnconfigure(col, weight=2)
            elif col == nbCol :
                optionsGrid['sticky'] = tk.W
                self.parent.columnconfigure(col, weight=2)
            b.grid(optionsGrid)
            col += 1



class Bouton(Button) :
    ''' Crée un simple bouton tkinter '''
    def __init__(self, parent, var, command, actif=True) :
        '''
        @param parent   : widget parent du bouton
        @param var      : identifiant dans config.langue
        @param command  : commande du bouton
        @param actif    : booléen état du bouton
        '''
        options = dict(bg=':bouton_normal_fond',
                       fg=':bouton_normal_texte',
                       activebackground=':bouton_survol_fond',
                       activeforeground=':bouton_survol_texte',
                       disabledforeground=':bouton_inactif_texte',
                       highlightbackground=':bouton_normal_surlignage',
                       highlightcolor=':bouton_focus_surlignage',
                       highlightthickness=1, cursor='hand1',
                       anchor=tk.NW,
                       relief=tk.FLAT,
                       overrelief=tk.FLAT,
                       padx=10, pady=5,
                       bd=0, var=var, command=command,
                       state=tk.NORMAL if actif else tk.DISABLED,
                       )
        Button.__init__(self, parent, **options)

    def activer(self) :
        ''' Autorise l'utilisation du bouton '''
        self.configure(state=tk.NORMAL)

    def desactiver(self) :
        ''' Interdit l'utilisation du bouton '''
        self.configure(state=tk.DISABLED)



class LabelIntitule(Label) :
    def __init__(self, parent, **options) :
        options['bg'] = ':label_fond'
        options['fg'] = ':label_texte'
        Label.__init__(self, parent, **options)



class MessageAPropos(Message) :
    def __init__(self, parent, **options) :
        options['aspect'] = 100
        options['bg'] = ':label_fond'
        options['fg'] = ':label_texte'
        Message.__init__(self, parent, **options)



class LabelDescription(Label) :
    def __init__(self, parent, largeur, hauteur, police) :
        Label.__init__(self, parent, width=largeur, height=hauteur, font=police,
                       relief=tk.SUNKEN, bg=':info_fond', fg=':info_texte',
                       highlightbackground=':info_bord', bd=2)



class LabelGrilleJeu(Label) :
    def __init__(self, parent, **options) :
        options['bg'] = ':menu_normal_fond'
        options['fg'] = ':menu_normal_texte'
        Label.__init__(self, parent, **options)



class BoutonRadio(Radiobutton) :
    def __init__(self, parent, **options) :
        options.update(dict(bg=':label_fond', fg=':label_texte',
                            selectcolor='#ffffff',
                            highlightbackground=':label_fond',
                            highlightcolor=':liste_focus_surlignage',
                            activebackground=':label_fond',
                            activeforeground=':liste_focus_surlignage',
                            highlightthickness=1, padx=2, cursor='hand1'))
        Radiobutton.__init__(self, parent, **options)



class ChampSaisie(Entry) :
    def __init__(self, parent, textvariable, police=None, largeur=12) :
        if not police :
            police = (config.famillesPolice.sansserif, -14)
        Entry.__init__(self, parent, bg=':saisie_normal_fond', width=largeur,
                       fg=':saisie_normal_texte', bd=2,
                       font=police, textvariable=textvariable,
                       disabledbackground=':saisie_inactif_fond',
                       disabledforeground=':saisie_inactif_texte',
                       highlightbackground=':saisie_normal_surlignage',
                       highlightcolor=':saisie_focus_surlignage',
                       highlightthickness=1,
                       insertbackground=':saisie_normal_texte',)



class ListeDeroulante :
    '''
    Crée une liste déroulante à la manière d'un select html
    '''
    def __init__(self, parent, id_, valeurs, selection, appel, var=False) :
        '''
        @param parent :       Widget parent tkinter de la liste déroulante
        @param id_ :          Identifiant de la liste
        @param valeurs :      Liste de valeurs au format dict (id:valeur)
        @param appel :        Méthode à appeler à chaque changement de sélection
                              Elle recevra 2 paramètres id_, et index valeurs
        @param selection :    clé du dict valeurs à sélectionner au 1er
                              affichage
        @param var :          Booléen qui à True utilisera le paramètre var
                              plutôt que label pour les items menu.
        '''

        self.id = id_
        self.appel = appel
        self.var = var

        self.imageFond = PhotoImage(file=config.repertoireImages\
                                            + 'transparent-200-20.gif')
        self.imageFleche = PhotoImage(file=config.repertoireImages\
                                             + 'transparent-200-20-fleche.gif')
        self.listeValeurs = []

        self.liste = Menubutton(parent,
                                bg=':liste_normal_fond',
                                fg=':liste_normal_texte',
                                bd=0, padx=0, pady=0, takefocus=True,
                                relief=tk.FLAT,
                                font=(config.famillesPolice.monospace, -15),
                                activebackground=':liste_survol_fond',
                                activeforeground=':liste_survol_texte',
                                highlightcolor=':liste_focus_surlignage',
                                highlightthickness=1,
                                highlightbackground=':liste_normal_surlignage',
                                justify=tk.CENTER, image=self.imageFleche,
                                compound=tk.CENTER, cursor='double_arrow',
                                )
        self.liste.imageFleche = self.imageFleche
        self.liste.imageFond = self.imageFond

        self.options = Menu(self.liste, bg=':liste_normal_fond',
                            fg=':liste_normal_texte', bd=0, tearoff=0,
                            activeborderwidth=0, relief=tk.FLAT,
                            font=(config.famillesPolice.monospace, -15),
                            activebackground=':liste_survol_fond',
                            activeforeground=':liste_survol_texte'
                            )

        for index, c in enumerate(sorted(valeurs.keys())) :
            if selection == c :
                self.selection = index
            self.listeValeurs.append((c, valeurs[c]))
            coptions = dict(background=':liste_normal_fond',
                            foreground=':liste_normal_texte',
                            activebackground=':liste_survol_fond',
                            activeforeground=':liste_survol_texte',
                            hidemargin=False,
                            image=self.imageFond,
                            compound=tk.CENTER,
                            command=lambda index=index : self.changer(index),
                           )
            if var :
                coptions['var'] = valeurs[c]
            else :
                coptions['label'] = valeurs[c]
            self.options.add_command(**coptions)

        self.liste.configure(menu=self.options)

        self.selectionner(self.selection)
        self.liste.bind('<Button-4>', self.elementPrecedent)
        self.liste.bind('<Up>', self.elementPrecedent)
        self.liste.bind('<Button-5>', self.elementSuivant)
        self.liste.bind('<Down>', self.elementSuivant)
        # Windows & macos
        self.liste.bind('<MouseWheel>', self._parcourir)

    def _parcourir(self, evt) :
        if evt.delta > 0 :
            self.elementPrecedent(None)
        else :
            self.elementSuivant(None)

    def elementPrecedent(self, evt) :
        self.liste.focus_set()
        if self.selection - 1 >= 0 :
            self.changer(self.selection - 1)

    def elementSuivant(self, evt) :
        self.liste.focus_set()
        if self.selection + 1 < len(self.listeValeurs) :
            self.changer(self.selection + 1)

    def selectionner(self, index) :
        self.selection = index
        if self.var :
            self.liste.configure(var=self.listeValeurs[index][1])
        else :
            self.liste.configure(text=self.listeValeurs[index][1])

    def changer(self, index) :
        self.appel(self.id, self.listeValeurs[index][0])
        self.selectionner(index)

    def ancrer(self, **params) :
        self.liste.grid(**params)



class ListeDeroulanteInfo(ListeDeroulante) :
    '''
    Crée une liste déroulante à la manière d'un select html avec la
    fonctionnalité en sus de changer le texte d'un widget tkinter comportant une
    option textvariable (label, message, ..)
    '''
    def __init__(self, parent, id_, valeurs, selection, appel, widget,
                 valeursTexte, var=False) :
        '''
        @param parent       : Widget parent tkinter de la liste déroulante
        @param id_          : Identifiant de la liste
        @param valeurs      : Liste de valeurs au format dict (id:valeur)
        @param appel        : Méthode à appeler à chaque changement de sélection
                              Elle recevra 3 paramètres id_, index et valeur
        @param selection    : Index de la liste valeurs à sélectionner au 1er
                              affichage
        @param widget       : Widget qui devra être modifié à chaque changement
        @param valeursTexte : Liste des textes à afficher au format dict.
                              Les index doivent être en relation avec ceux du
                              paramètre valeurs.
        @param var          : Booléen qui à True utilisera le paramètre var
                              plutôt que label pour les items menu.
        '''
        ListeDeroulante.__init__(self, parent, id_, valeurs, selection, appel,
                                 var)
        self.widget = widget

        self.__selectionner = self.selectionner
        self.selectionner = self._selMajObj
        self.valeursTexte = []
        for c, v in self.listeValeurs :
            self.valeursTexte.append((c, valeursTexte[c]))
        self.selectionner(self.selection)

    def _selMajObj(self, index) :
        ''' Méthode interne '''
        self.__selectionner(index)
        if self.var :
            self.widget.configure(var=self.valeursTexte[index][1])
        else :
            self.widget.configure(text=self.valeursTexte[index][1])



class Tableau(Frame) :
    '''
    Crée une liste tabulaire très basique avec colonnes d'entête.
    '''
    def __init__(self, parent, largeur, hauteur, hauteurLigne, colonnes,
                 couleurFond='#ffffff', largeurScroll=15) :
        '''
        @param parent           : widget tkinter
        @param largeur          : largeur du tableau
        @param hauteur          : hauteur du tableau (indiquer un multiple de
                                  hauteurLigne)
        @param hauteurLigne     : hauteur des lignes du tableau
        @param colonnes         : (tuple, list) colonnes d'entête du tableau
                                  Si le nom de colonne commence par « : » cela
                                  indiquera que c'est un identifiant de
                                  config.langue
        @param couleurFond      : couleur de fond du tableau (#fff par défaut)
        @param largeurScroll    : largeur du scroll vertical (15 par défaut)
        '''
        largeurScroll = largeurScroll
        self.largeur = largeur - largeurScroll
        self.hauteur = hauteur
        self.hauteurLigne = hauteurLigne
        self.colonnes = colonnes
        self.nbColonnes = len(self.colonnes)

        Frame.__init__(self, parent, width=self.largeur + largeurScroll,
                       height=self.hauteur, bg='red')
        self.grid_propagate(0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)

        lc = int(largeur / self.nbColonnes)
        self.largeurColonnes = [lc] * self.nbColonnes
        reliquat = largeur - lc * self.nbColonnes
        i = 0
        while reliquat > 0 :
            self.largeurColonnes[i] += 1
            reliquat -= 1
            i += 1

        self.canevasEntete = Canvas(self, width=self.largeur,
                                    height=hauteurLigne, bd=0,
                                    bg=couleurFond, highlightthickness=0)
        self.canevasEntete.grid(row=1, column=1)

        self.canevasLignes = Canvas(self, width=self.largeur,
                                    height=self.hauteur - self.hauteurLigne,
                                    bd=0, bg=couleurFond, takefocus=True,
                                    highlightthickness=0,
                                    yscrollincrement = self.hauteurLigne)
        self.canevasLignes.grid(row=2, column=1, sticky=tk.N)

        frameScroll = Frame(self, width=largeurScroll, height=self.hauteur)
        frameScroll.grid(row=1, rowspan=2, column=2)
        frameScroll.grid_propagate(0)
        frameScroll.rowconfigure(1, weight=1)

        self.scroll = Scrollbar(frameScroll, width=largeurScroll,
                                orient=tk.VERTICAL, bg=':barre_barre',
                                activebackground=':barre_survol',
                                troughcolor=':barre_creux',
                                highlightthickness=0,
                                )
        self.scroll.grid(row=1, column=1, sticky=tk.NS)

        self.cellulesEntete = None
        self.cellulesLignes = []

        self._policeBase = [config.famillesPolice.serif, -13, 'normal', 'roman']
        self.couleursFond = [couleurFond] * self.nbColonnes
        self.couleursTexte = ['#000000'] * self.nbColonnes
        self.polices = []
        for n in range(self.nbColonnes) :
            self.polices.append(self._policeBase.copy())
        self._liaisons = []
        self._initialiser()


    def _initialiser(self) :
        ''' Méthode interne '''
        ''' Initialise les attributs '''

        self.canevasLignes.configure(scrollregion=(0, 0, 0, 0))
        try :
            self.scroll.deletecommand(self.scroll['command'])
        except tk.TclError :
            pass
        try :
            self.canevasLignes\
                            .deletecommand(self.canevasLignes['yscrollcommand'])
        except tk.TclError :
            pass
        for n in self.canevasLignes.bind() :
            self.canevasLignes.unbind(n)
        for n in self._liaisons :
            self.canevasLignes.deletecommand(n)
        self._liaisons.clear()


        self.y = 0
        self._scrollActif = False
        self.scroll.configure(command=None)

        self.canevasLignes.configure(yscrollcommand=None)

    def _activerScroll(self) :
        ''' Méthode interne '''
        ''' Active le scroll de la liste '''
        if self._scrollActif :
            return
        self._scrollActif = True
        self.scroll.configure(command=self.canevasLignes.yview)
        self.canevasLignes.configure(yscrollcommand=self.scroll.set)

        self._liaisons.extend([
            self.canevasLignes.bind('<Up>', self._parcourir),
            self.canevasLignes.bind('<Button-4>', self._parcourir),
            self.canevasLignes.bind('<Down>', self._parcourir),
            self.canevasLignes.bind('<Button-5>', self._parcourir),
            ])


    def vider(self) :
        ''' Supprime toute les lignes de la liste '''
        for oid in self.canevasLignes.find_all() :
            self.canevasLignes.delete(oid)
        self._initialiser()


    def definirCouleurFond(self, couleur, *index) :
        '''
        Définit les couleurs des cellules des lignes
        @param couleur : valeur de couleur acceptée par tkinter
        @param index   : index des cellules qui auront ces couleurs, si non
                         spécifiés, toutes les cellules de la ligne seront
                         définies à cette couleur.
        '''
        if index :
            for i in index :
                self.couleursFond[i] = couleur
        else :
            self.couleursFond.clear()
            self.couleursFond.extend([couleur]*self.nbColonnes)


    def _parcourir(self, evt) :
        ''' Méthode Interne '''
        '''
        Relie les actions roulette souris et flèches haut et bas au scroll
        vertical du canevas lignes
        '''
        if evt.keysym == 'Down' or evt.num == 5 :
            self.canevasLignes.yview('scroll', 1, tk.UNITS)
        elif evt.keysym == 'Up' or evt.num == 4 :
            self.canevasLignes.yview('scroll', -1, tk.UNITS)


    def definirCouleurTexte(self, couleur, *index) :
        '''
        Définit les couleurs du texte des cellules des lignes
        @param couleur : valeur de couleur acceptée par tkinter
        @param index   : index des cellules qui auront ces couleurs, si non
                         spécifiés, tous les textes des cellules de la ligne
                         seront définis à cette couleur.
        '''
        if index :
            for i in index :
                self.couleursTexte[i] = couleur
        else :
            self.couleursTexte.clear()
            self.couleursTexte.extend([couleur]*self.nbColonnes)


    def definirPoliceTexte(self, police, *index) :
        '''
        Définit la police du texte des cellules des lignes
        @param police : dict ayant pour clés celles de tkinter font.
                        (family, size, weight, slant)
                        Note : il n'est pas nécessaire de spécifier toutes les
                        valeurs, celles devant être changées suffit.
        @param index   : index des cellules qui auront cette police, si non
                         spécifiés, toutes les polices des textes des cellules
                         de la ligne seront définies avec cette police.
        '''
        cles = ('family', 'size', 'weight', 'slant')
        if type(police) != dict :
            raise ValueError('police doit être un dict')
        for v in police.keys() :
            if v not in cles :
                raise ValueError('la clé {} est invalide pour la police,'
                                 ' clés autorisées : {}'.format(v, cles))
        if not index :
            index = range(0, self.nbColonnes)
        for i in index :
            for c, v in police.items() :
                self.polices[i][cles.index(c)] = v


    def creerEntete(self) :
        '''
        Crée les cellules de l'entete de la liste.
        Ne peut être créé qu'une seule fois.
        '''
        if self.cellulesEntete :
            raise UserWarning('L\'entête du tableau a déjà été créée')
        x = 0
        rects = []
        textes = []
        for i, v in enumerate(self.colonnes) :
            rects.append(self.canevasEntete\
                        .create_rectangle(x, 0, x + self.largeurColonnes[i],
                                          self.hauteurLigne, width=0,
                                          fill=self.couleursFond[i])
                        )
            options = dict(fill=self.couleursTexte[i], font=self.polices[i])
            if str(v)[0] == ':' :
                options['var'] = v[1:]
            else :
                options['text'] = v
            textes.append(self.canevasEntete\
                          .create_text(x + int(self.largeurColonnes[i] / 2),
                                       int(self.hauteurLigne / 2), **options)
                          )
            x += self.largeurColonnes[i]
        self.cellulesEntete = (rects, textes)

    def creerLigne(self, valeurs) :
        '''
        Crée une ligne du tableau
        @param valeurs  : valeurs des cellules de la ligne
                          le nombre de valeurs doit être identique au nombre
                          de colonnes.
                          Tout comme pour les colonnes Si le nom d'une valeur
                          commence par « : » cela indiquera que c'est un
                          identifiant de config.langue
        '''
        rects = []
        textes = []
        x = 0
        for i, v in enumerate(valeurs) :
            rects.append(self.canevasLignes\
                         .create_rectangle(x, self.y,
                                           x + self.largeurColonnes[i],
                                           self.y + self.hauteurLigne, width=0,
                                           fill=self.couleursFond[i])
                        )
            options = dict(fill=self.couleursTexte[i], font=self.polices[i])
            if str(v)[0] == ':' :
                options['var'] = v[1:]
            else :
                options['text'] = v
            textes.append(self.canevasLignes\
                          .create_text(x + int(self.largeurColonnes[i] / 2),
                                       self.y + int(self.hauteurLigne / 2),
                                       **options)
                          )
            x += self.largeurColonnes[i]

        self.cellulesLignes.append((rects, textes))

        self.y += self.hauteurLigne
        if self.y > self.hauteur :
            self._activerScroll()
            self.canevasLignes.configure(scrollregion=(0, 0, 0, self.y))



class FenetreTierce(Toplevel) :
    '''
    Crée une fenêtre toplevel tkinter
    Celle-ci sera centrée sur la fenêtre root
    '''
    _decalage = 0
    def __init__(self, parent, titre=None) :
        '''
        @param parent   : widget tkinter parent de la fenêtre
        @param titre    : identifiant dans config.langue
        '''
        self.ajoutDecalage = 20
        self.largeurFenetre = int(config.largeurFenetre / 2)
        self.hauteurFenetre = 500
        Toplevel.__init__(self, parent, bg=':preferences_cadre')
        x = parent.winfo_toplevel().winfo_x() + int((config.largeurFenetre\
                                                     - self.largeurFenetre) / 2)
        y = parent.winfo_toplevel().winfo_y() + 30
        self.geometry('{}x{}+{}+{}'.format(self.largeurFenetre,
                                           self.hauteurFenetre,
                                           x + FenetreTierce._decalage,
                                           y + FenetreTierce._decalage)
                                           )
        self.transient(parent.winfo_toplevel())
        #XXX A voir si je les passe en modales ou non
        #self.grab_set()
        FenetreTierce._decalage += self.ajoutDecalage
        self.resizable(False, False)
        if titre :
            self.titre(titre)

    def destroy(self) :
        super().destroy()
        FenetreTierce._decalage -= self.ajoutDecalage



class Preferences(FenetreTierce) :
    '''
    Crée une fenêtre affichant les préférences
    '''
    def __init__(self, parent) :
        '''
        @param parent   : widget tkinter parent de la fenêtre préférences
        '''
        FenetreTierce.__init__(self, parent, 'preference_titre')

        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self.largeurLabelDesc = 50
        self.policeLabel = (config.famillesPolice.serif, -15)
        self.policeDesc = (config.famillesPolice.serif, -14, 'normal', 'italic')

        ################
        # Grilles
        self.labelGrilles = LabelIntitule(self, var='preference_grille',
                                          font=self.policeLabel)
        self.labelGrilles.grid(row=2, column=1, padx=10, sticky=tk.E)
        self.rowconfigure(2, weight=2)

        self.labelGrillesDesc = LabelDescription(self, self.largeurLabelDesc, 2,
                                                 self.policeDesc)
        self.labelGrillesDesc.grid(row=3, column=1, columnspan=2)
        self.rowconfigure(3, weight=1)

        nomsGrilles, descGrilles = {}, {}
        grilles = libs.Grilles()
        for c in grilles.annuaire.keys() :
            nomsGrilles[c] = 'grille_{}_nom'.format(c)
            descGrilles[c] = 'grille_{}_description'.format(c)

        ldGrilles = ListeDeroulanteInfo(self, 'grille', nomsGrilles,
                                        config.utilisateur.grille,
                                        self.enregistrer, self.labelGrillesDesc,
                                        descGrilles, var=True)
        ldGrilles.ancrer(row=2, column=2, padx=10, sticky=tk.W)

        ################
        # Thèmes

        self.labelThemes = LabelIntitule(self, var='preference_theme',
                                         font=self.policeLabel)
        self.labelThemes.grid(row=4, column=1, padx=10, sticky=tk.E)
        self.rowconfigure(4, weight=2)

        self.labelThemesDesc = LabelDescription(self, self.largeurLabelDesc, 2,
                                                self.policeDesc)
        self.labelThemesDesc.grid(row=5, column=1, columnspan=2)
        self.rowconfigure(5, weight=1)

        lthemes, lthemesDesc = {}, {}
        for rep in libs.themesDiponibles() :
            lthemes[rep], lthemesDesc[rep] = libs.themeInfo(rep)

        ldThemes = ListeDeroulanteInfo(self, 'theme', lthemes,
                                       config.utilisateur.theme,
                                       self.enregistrer, self.labelThemesDesc,
                                       lthemesDesc)
        ldThemes.ancrer(row=4, column=2, padx=10, sticky=tk.W)

        ################
        # Méthodes de tir

        self.labelMethodes = LabelIntitule(self, var='preference_methode',
                                           font=self.policeLabel)
        self.labelMethodes.grid(row=6, column=1, padx=10, sticky=tk.E)
        self.rowconfigure(6, weight=2)

        self.labelMethodesDesc = LabelDescription(self, self.largeurLabelDesc,
                                                  2, self.policeDesc)
        self.labelMethodesDesc.grid(row=7, column=1, columnspan=2)
        self.rowconfigure(7, weight=1)

        lmethodes, lmethodesDesc = {}, {}
        import methodes

        for c in methodes.ModeTir._modes.keys() :
            lmethodes[c] = 'methode_{}_nom'.format(c)
            lmethodesDesc[c] = 'methode_{}_description'.format(c)

        ldMethodes = ListeDeroulanteInfo(self, 'methode', lmethodes,
                                         config.utilisateur.methode,
                                         self.enregistrer,
                                         self.labelMethodesDesc, lmethodesDesc,
                                         var=True)
        ldMethodes.ancrer(row=6, column=2, padx=10, sticky=tk.W)

        ################
        # Langues
        self.labelLangues = LabelIntitule(self, var='preference_langue',
                                          font=self.policeLabel)
        self.labelLangues.grid(row=8, column=1, padx=10, sticky=tk.E)
        self.rowconfigure(8, weight=2)

        ldLangues = ListeDeroulante(self, 'langue', libs.languesDisponibles(),
                                    config.utilisateur.langue, self.enregistrer)
        ldLangues.ancrer(row=8, column=2, padx=10, sticky=tk.W)

        ################
        # Bateaux contigus ou non
        varAdj = tk.IntVar(self,int(config.utilisateur.adjacent))
        self.labelAdj = LabelIntitule(self, var='preference_adjacent',
                                      font=self.policeLabel)
        self.labelAdj.grid(row=9, column=1, padx=10, sticky=tk.E)

        frameAdj = Frame(self, bg=':preferences_cadre')
        frameAdj.grid(row=9, column=2, padx=5, sticky=tk.W)

        avecAdj = BoutonRadio(frameAdj, var='preference_adjacent_options_avec',
                              variable=varAdj, value=1, font=self.policeLabel,
                              command=lambda : self.enregistrer('adjacent',
                              True))
        avecAdj.grid(row=1, column=1, padx=5, sticky=tk.W)

        sansAdj = BoutonRadio(frameAdj, var='preference_adjacent_options_sans',
                              variable=varAdj, value=0, font=self.policeLabel,
                              command=lambda : self.enregistrer('adjacent',
                              False))
        sansAdj.grid(row=1, column=2, padx=5, sticky=tk.W)

        '''
        ################
        # Abandon de l'idée d'ajouter du son au jeu, même si il est aisé
        # d'utiliser winsound pour windows et aplay, afplay, au pire cvlc sur
        # unix, surtout la flemme de créer des sons {º~°}
        # Sons du jeu

        varSon = tk.IntVar(self, 1 if config.utilisateur.son == 'avec' else 0)
        self.labelSon = LabelIntitule(self, var='preference_son',
                                      font=self.policeLabel)
        self.labelSon.grid(row=10, column=1, padx=10, sticky=tk.E)

        frameSon = Frame(self, bg=':preferences_cadre')
        frameSon.grid(row=10, column=2, padx=5, sticky=tk.W)

        avecSon = BoutonRadio(frameSon, var='preference_son_options_avec',
                              variable=varSon, value=1, font=self.policeLabel,
                              command=lambda : self.enregistrer('son', 'avec'))
        avecSon.grid(row=1, column=1, padx=5, sticky=tk.W)

        sansSon = BoutonRadio(frameSon, var='preference_son_options_sans',
                              variable=varSon, value=0, font=self.policeLabel,
                              command=lambda : self.enregistrer('son', 'sans'))
        sansSon.grid(row=1, column=2, padx=5, sticky=tk.W)
        '''
        ################
        # Fermeture
        self.boutonFermer = Bouton(self, var='bouton_fermer',
                                   command=self.destroy)
        self.boutonFermer.grid(row=11, column=1, columnspan=2)
        self.rowconfigure(11, weight=3)


    def enregistrer(self, id_, valeur) :
        '''
        Enregistre la valeur de configuration dans le fichier préférences.
        Si id_ concerne le thème, la langue ou la méthode de tir, modification
        directe dans le jeu.
        '''
        #XXX Déléguer ces tâches à l'application, tout ceci n'a rien à faire ici
        libs.enregistrerPreferences(**{id_:valeur})
        config.utilisateur = config.utilisateur._replace(**{id_:valeur})
        if id_ == 'langue' :
            config.langue.changer(valeur)
            config.rlangue.changer()
        elif id_ == 'theme' :
            config.theme.changer(valeur)
            config.rtheme.changer()
        elif id_ == 'methode' : #XXX Ceci est cracra [*_O)
            try :
                config.methodeTir.changer(valeur)
            except AttributeError :
                pass



class Scores(FenetreTierce) :
    '''
    Crée une fenêtre affichant les scores
    '''
    def __init__(self, parent) :
        '''
        @param parent   : widget tkinter parent de la fenêtre scores
        '''
        self.resultats = libs.chargerResultats()
        FenetreTierce.__init__(self, parent, 'score_titre')
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        if self.resultats :
            self._afficherResultats()
        else :
            self._afficherAucun()

        self.boutonFermer = Bouton(self, var='bouton_fermer',
                                   command=self.destroy)
        self.boutonFermer.grid(row=4, column=1, columnspan=2, pady=15,
                               sticky=tk.S)

    def _afficherResultats(self) :
        import datetime
        import locale
        from operator import itemgetter

        locale.setlocale(locale.LC_TIME, '')

        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=0)
        self.rowconfigure(4, weight=1)

        #XXX À faire :
        # Séparation des scores entre jeux avec bateaux juxtaposés et non
        # juxtaposés
        # checkbox ? radiobutton ? seconde liste ?

        # Formatage des valeurs
        self.grilles = {}
        ldGrilles = {}
        liste = sorted(self.resultats, key=itemgetter('depart'), reverse=True)
        self.selectionGrille = liste[0]['jeu'] # Dernier jeu joué
        for n in liste :
            if n['jeu'] not in self.grilles.keys() :
                self.grilles[n['jeu']] = []
                ldGrilles[n['jeu']] = 'grille_{}_nom'.format(n['jeu'])
            jeu = dict(date=datetime.datetime.fromtimestamp(n['depart'])\
                            .strftime('%x'),
                       temps='{}′{}″'.format(int((n['fin']\
                                             - n['depart']) // 60),
                                             str(int((n['fin'] - n['depart'])\
                                             % 60)).zfill(2)),
                       coups=n['coups'],
                       resultats=':score_{}'.format('gagne' if n['gagnant']\
                                                            else 'perdu'),
                      )
            self.grilles[n['jeu']].append(jeu)

        self.labelGrilles = LabelIntitule(self, var='preference_grille',
                                          font=(config.famillesPolice.serif,
                                          -15))
        self.labelGrilles.grid(row=1, column=1, padx=10, pady=30, sticky=tk.E)

        ldGrilles = ListeDeroulante(self, 'grille', ldGrilles,
                                    self.selectionGrille, self.changer,
                                    var=True)
        ldGrilles.ancrer(row=1, column=2, padx=10, pady=30, sticky=tk.W)

        ht = 200

        self.colonnes = ('date', 'resultats', 'temps', 'coups')
        self.tableau = Tableau(self, self.largeurFenetre, 300, 25,
                               [':score_' + n for n in self.colonnes],
                               ':tableau_fond')
        self.tableau.grid(row=3, column=1, columnspan=2)
        self.tableau.definirCouleurFond(':tableau_entete_fond')
        self.tableau.definirCouleurTexte(':tableau_entete_texte')
        self.tableau.definirPoliceTexte(dict(weight='bold', size=-15))
        self.tableau.creerEntete()

        self.creerLignes(self.selectionGrille)

    def _afficherAucun(self) :
        labelAucun = LabelIntitule(self, var='score_apj',
                                   font=(config.famillesPolice.serif, -16))
        labelAucun.grid(row=1, column=1, columnspan=2)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(4, weight=0)


    def creerLignes(self, idGrille) :
        """
        crée les lignes du tableau
        @param idGrille     : id de la grille dans self.grilles
        """
        self.tableau.vider()
        self.tableau.definirCouleurFond(':tableau_fond')
        self.tableau.definirCouleurTexte(':tableau_ligne_texte')
        self.tableau.definirPoliceTexte(dict(weight='normal', size=-14))
        for v in self.grilles[idGrille] :
            self.tableau.definirCouleurTexte(':tableau_ligne_negatif'
                                             if v['resultats'] == ':score_perdu'
                                             else ':tableau_ligne_positif', 1)
            self.tableau.creerLigne([v[n] for n in self.colonnes])


    def changer(self, id_, cle) :
        '''
        Change les lignes du tableau par celles relatives à la clé indiquée
        @param cle  : clé existante de self.grille
        '''
        if cle != self.selectionGrille :
            self.selectionGrille = cle
            self.creerLignes(cle)



class APropos(FenetreTierce) :
    def __init__(self, parent) :
        FenetreTierce.__init__(self, parent, 'apropos_titre')

        for i in range(4) :
            self.rowconfigure(i, weight=0)
        self.rowconfigure(4, weight=1)

        self.preambule = MessageAPropos(self, width=self.largeurFenetre-30,
                                              justify=tk.LEFT,
                                              var='apropos_preambule')
        self.preambule.grid(padx=10, pady=20, sticky=tk.W)

        self.version = LabelIntitule(self, justify=tk.LEFT,
                                           var='apropos_version')
        self.version.grid(padx=10, pady=20, sticky=tk.W)

        self.notes = MessageAPropos(self, width=self.largeurFenetre-30,
                                          justify=tk.LEFT,
                                          var='apropos_notes')
        self.notes.grid(padx=10, pady=20, sticky=tk.W)

        self.licence = MessageAPropos(self, width=self.largeurFenetre-30,
                                            justify=tk.LEFT,
                                            var='apropos_licence')
        self.licence.grid(padx=10, pady=20, sticky=tk.W)

        self.boutonFermer = Bouton(self, var='bouton_fermer',
                                         command=self.destroy)
        self.boutonFermer.grid(pady=20, sticky=tk.S)

####################
#
# Classes spécifiques au plateau du jeu


class Plateau(Canvas) :
    def __init__(self, parent) :
        Canvas.__init__(self, parent, width=config.largeurFenetre,
                        height=config.hauteurPlateau, highlightthickness=0,
                        bg=':plateau')

        self._bindsPlateau = []

    def bind(self, sequence=None, methode=None) :
        ''' Surcharge de la méthode bind de tkinter '''
        if not sequence :
            return super().bind()
        self._bindsPlateau.append(super().bind(sequence, methode))
        return self._bindsPlateau[-1]

    def vider(self) :
        '''
        Supprime tous les composants du plateau ainsi que tous les événements
        déclarés.
        '''
        for n in self.bind() :
            self.unbind(n)

        for n in self._bindsPlateau :
            try :
                self.deletecommand(n)
            except :
                pass
        self._bindsPlateau.clear()

        for oid in self.find_all() :
            self.delete(oid)



class GrillePlateau :
    '''
    Crée une simple grille carrée
    '''
    def __init__(self, plateau, x, y) :

        self.plateau = plateau

        self.x, self.y = x+1, y+1

        # Arrière plan de la grille
        self._id = plateau.create_rectangle(x, y, x+config.tailleGrille,
                                            y+config.tailleGrille,
                                            fill=':grille_case', width=0,
                                            tags='grille')
        # Lignes horizontales
        i = y
        while i <= config.tailleGrille + y :
            self.plateau.create_line(x, i, x+config.tailleGrille-1, i,
                                     fill=':grille_ligne', tags='grille',
                                     state=tk.DISABLED)
            i += config.tailleCases + 1
        # Lignes verticales
        i = x
        while i <= config.tailleGrille + x :
            self.plateau.create_line(i, y, i, y+config.tailleGrille-1,
                                     fill=':grille_ligne', tags='grille',
                                     state=tk.DISABLED)
            i += config.tailleCases + 1

    def intituler(self, titre) :
        '''
        Affiche le nom joueur au dessus de la grille
        '''
        x = self.x + config.tailleGrille / 2
        ombreTexte = self.plateau\
                     .create_text(x, self.y - 16,
                                  fill=':grille_texte_joueur_relief',
                                  text=titre.upper(),
                                  font=(config.famillesPolice.serif, -16),
                                  state=tk.DISABLED)

        texte = self.plateau.create_text(x - 1, self.y - 17,
                                         fill=':grille_texte_joueur',
                                         text=titre.upper(),
                                         font=(config.famillesPolice.serif,
                                               -16),
                                         state=tk.DISABLED)

    def graduer(self) :
        '''
        Affiche les graduations sur les côtés gauche et bas de la grille
        '''
        l = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        # Taille de police varie en fonction de la taille des cases,
        # on prend 5 par 10 px de tailleCases, mais on limite tout de
        # même afin de ne pas avoir de texte trop gros
        pt = -int((config.tailleCases/10) * 5)
        if pt < -15 :
            pt = -15
        police = (config.famillesPolice.sansserif, pt)

        i = 0
        xg = self.x + pt
        yg = self.y + round(config.tailleCases / 2)
        while i < config.nombreCases :
            self.plateau.create_text(xg + 1, yg + 1,
                                     fill=':grille_texte_graduation_relief',
                                     font=police, state=tk.DISABLED, text=l[i])
            self.plateau.create_text(xg, yg, fill=':grille_texte_graduation',
                                     font=police, state=tk.DISABLED, text=l[i])

            yg += config.tailleCases + 1 # 1 pour la ligne séparant les cases
            i += 1

        i = 1
        xg = self.x + round(config.tailleCases / 2)
        yg = self.y + config.tailleGrille + round((config.tailleCases) / 2)
        while i <= config.nombreCases :
            self.plateau.create_text(xg + 1, yg + 1,
                                     fill=':grille_texte_graduation_relief',
                                     font=police, state=tk.DISABLED, text=i)
            self.plateau.create_text(xg, yg, fill=':grille_texte_graduation',
                                     font=police, state=tk.DISABLED, text=i)
            xg += config.tailleCases + 1
            i += 1

    @property
    def id(self) :
        ''' Retourne l'id de la grille (retour identifiant Canevas) '''
        return self._id



class MessagePlateau :
    def __init__(self, plateau) :
        '''
        Crée la zone où seront affichés les messages sur le plateau
        '''
        self.plateau = plateau
        self.contId = self.plateau\
                      .create_rectangle(config.margeGrille,
                                        config.margeGrille * 3\
                                        + config.tailleGrille,
                                        config.margeGrille * 3\
                                        + config.tailleGrille * 2,
                                        config.margeGrille * 3\
                                        + config.tailleGrille\
                                        + config.hauteurZoneMessage,
                                        fill=':message_neutre_fond',
                                        state=tk.DISABLED,
                                        outline=':message_bordure')
        # Affichage d'un petit triangle afin de faire un petit curseur sur le
        # côté gauche
        self.curId = self.plateau\
                     .create_polygon(config.margeGrille,
                                     config.margeGrille * 3\
                                     + config.tailleGrille,
                                     config.margeGrille\
                                     + round(config.hauteurZoneMessage/2),
                                     config.margeGrille * 3\
                                     + config.tailleGrille\
                                     + round(config.hauteurZoneMessage/2),
                                     config.margeGrille,
                                     config.margeGrille * 3\
                                     + config.tailleGrille\
                                     + config.hauteurZoneMessage,
                                     fill=':message_bordure',
                                     state=tk.DISABLED)

        self.id = self.plateau.create_text(config.margeGrille + 25,
                                           config.margeGrille * 3\
                                           + config.tailleGrille,
                                           anchor=tk.NW,
                                           font=(config.famillesPolice.serif,
                                                 -16),
                                           state=tk.DISABLED)
        # Centrage vertical du texte dans sa zone d'affichage
        bt = self.plateau.bbox(self.id)
        self.plateau.move(self.id, 0, round(config.hauteurZoneMessage / 2\
                                            - (bt[3] - bt[1]) / 2 ))

    def __call__(self, texte, type_=None, var=True, remplacements={}) :
        '''
        Affiche le texte spécifié dans la zone message
        @param texte            : identifiant texte dans langue ou texte brut si
                                  var définit à False
        @param type_            : type du message devant être une valeur parmi :
                                    - neutre (par défaut)
                                    - attention
                                    - fatal
                                    - bien
                                    - super
        @param var              : booléen spécifiant si texte est un identifiant
                                  langue
                                  (True par défaut)
        @param remplacements    : dict, spécifie les remplacements à faire dans
                                  le message
        '''
        if not type_ :
            type_ = 'neutre'
        else :
            ltype = ('neutre', 'attention', 'fatal', 'bien', 'super')
            if type_ not in ltype :
                raise ValueError('argument type_ de afficher doit être une'
                                 ' valeur parmi {}, fourni : {}'\
                                 .format(ltype, type_))
        couleurFond = ':message_' + type_ + '_fond'
        couleurTexte = ':message_' + type_ + '_texte'
        options = {'fill':couleurTexte}
        if var :
            options['var'] = texte
        else :
            options['text'] = texte
        self.plateau.itemconfigure(self.id, **options)
        self.plateau.itemconfigure(self.contId, fill=couleurFond)



class FlottePlateau :
    '''
    Crée la flotte des bateaux sur le plateau
    (phase du potsitionnement)
    '''
    def __init__(self, plateau) :
        self.plateau = plateau
        self._bateaux = {} # id : (objet bateau, index config, id socle)
        self._index = {} # index config : id

        yb = config.margeGrille + config.tailleCases # + 2 # 2nde ligne
        y = yb
        x = config.tailleGrille + config.margeGrille * 2
        ht = 0 # Hauteur de la boite de texte
        #lbMax = 0
        lmax = 0

        for index, tb in enumerate(config.bateaux) :
            nomBateau = config.nomsBateaux[index]
            x2 = x + tb * config.tailleCases + tb - 1
            y2 = y + config.tailleCases
            # Création d'un même rectangle, pour représenter les socles
            br = self.plateau.create_rectangle(x-1, y-1, x2, y2,
                                          fill=':bateau_socle', width=1,
                                          outline=':bateau_socle_bord',
                                          stipple='gray12', state=tk.DISABLED)

            brBox = self.plateau.bbox(br)
            brl = brBox[2] - brBox[0]
            if brl > lmax :
                lmax = brl

            # Texte affichant le nom du bateau sur le rectangle
            self.plateau.create_text(x + 10, y-9, var=config.nomsBateaux[index],
                                     anchor=tk.W, fill=':bateau_texte_relief',
                                     font=(config.famillesPolice.sansserif,
                                           -15),
                                     state=tk.DISABLED)
            bt = self.plateau.create_text(x + 9, y-10,
                                          var=config.nomsBateaux[index],
                                          anchor=tk.W, fill=':bateau_texte',
                                          font=(config.famillesPolice.sansserif,
                                                -15),
                                          state=tk.DISABLED)

            btBox = self.plateau.bbox(bt)
            btl = btBox[2] - btBox[0]
            if btl > lmax :
                lmax = btl

            if not ht :
                ht = btBox[3] - btBox[1]

            bateau = BateauPlateau(self.plateau, 'bateau', tb, x, y, x2, y2)
            self.plateau.lift(bateau.id)
            #XXX socle n'est a-priori pas nécessaire
            self._bateaux[bateau.id] = {'bateau':bateau,
                                        'index':index,
                                        'socle':None}
            self._index[index] = bateau.id

            # Si le prochain positionnement excède le bas de la grille,
            # on remonte en haut en positionnant sur une seconde colonne
            # 10 est l'espace de séparation entre chaque éléments
            if y2 + config.tailleCases + ht + 10\
                    > config.margeGrille + config.tailleGrille :
                y = yb
                x += lmax + config.tailleCases
                lmax = 0
            else :
                y += config.tailleCases + ht + 10

    @property
    def bateauxIds(self) :
        return list(self._bateaux.keys())

    @property
    def index(self) :
        ''' Retourne un dict des index reliés aux ids bateaux '''
        return self._index

    def indexId(self, id_) :
        ''' Retourne l'index du bateau dans config associé à l'id fourni '''
        return self._bateaux[id_]['index']

    def idIndex(self, index) :
        ''' Retourne l'id du bateau associé à son index dans config '''
        return self._index[index]

    def bateau(self, id_) :
        '''
        Retourne l'objet bateau associé à l'id fourni
        Et le place en haut de la file des items plateau
        '''
        self.plateau.lift(self._bateaux[id_]['bateau'].id)
        return self._bateaux[id_]['bateau']



class BateauPlateau :
    '''
    Crée un bateau sur le plateau
    '''
    def __init__(self, plateau, nom, taille, x, y, x2, y2) :
        '''
        @param plateau          : plateau du jeu
        @param nom              : nom du bateau
        @param taille           : taille en case de la longueur bateau
        @params x, y, x2, y2    : coordonnées du rectangle bateau
        '''
        self.plateau = plateau
        self._id = plateau.create_rectangle(x, y, x2, y2, fill=':bateau',
                                            width=0, tags='bateau')
        self._nom = nom
        self._taille = taille
        self._socle = (x, y, x2, y2)
        self._coords = [x, y, x2, y2]

    @property
    def id(self) :
        return self._id

    #XXX A voir si je garde le nom
    @property
    def nom(self) :
        return self._nom

    @property
    def taille(self) :
        return self._taille

    @property
    def socle(self) :
        return self._socle

    @property
    def coords(self) :
        return self._coords

    def deplacerSur(self, x, y, x2, y2) :
        ''' Déplace le bateau sur les coordonnées spécifiées '''
        self._coords.clear()
        self.coords.extend((x, y, x2, y2))
        self.plateau.coords(self.id, x, y, x2, y2)

    def deplacer(self, x, y) :
        ''' Déplace le bateau de x en vertical et y en horizontal '''
        self._coords[0] += x
        self._coords[2] += x
        self._coords[1] += y
        self._coords[3] += y
        self.plateau.move(self.id, x, y)



class CompteurBateauxPlateau :
    '''
    Crée un affichage simpliste du nombre de bateaux restants à couler de
    l'adversaire du joueur sous forme d'un petit rectangle suivi du
    restant/total selon chaque tailles de bateaux
    '''
    def __init__(self, plateau, x, y=None, tailleCases=12) :
        '''
        @param plateau      : plateau du jeu
        @params x, y        : coordonnée haut gauche à partir de laquelle sera
                              affiché la liste
                              des bateaux
        @param tailleCases  : nombre de pixels d'une case bateau (12 par défaut)
        '''
        # x => bord gauche de la grille sous laquelle il doit s'afficher
        if not y :
            y = config.tailleGrille + config.hauteurZoneMessage \
                + config.margeGrille * 3 \
                + round((config.margeGrille - tailleCases) / 2)
        self.plateau = plateau

        self.listeTextes = {}
        self.bateaux = dict([(n, 0) for n in set(config.bateaux)])
        self.bateauxTotaux = dict([(n, config.bateaux.count(n))\
                                    for n in set(config.bateaux)])

        xDepart = x
        # Affichage sous la zone de messages (hauteur d'une marge)

        rids = []
        for tb, nb in self.bateauxTotaux.items() :
            rids.append(self.plateau.create_rectangle(x, y,
                                                      x + tb * tailleCases,
                                                      y + tailleCases,
                                                      width=0, fill=':bateau',
                                                      state=tk.DISABLED))
            x += tb * tailleCases + 5
            self.listeTextes[tb] = self.plateau\
                                   .create_text(x, y,
                                                text='0/' + str(nb),
                                                fill=':bateau_texte',
                                                anchor=tk.NW,
                                                font=(config\
                                                      .famillesPolice.monospace,
                                                      -12, 'normal', 'italic'),
                                                state=tk.DISABLED)
            x += tailleCases * 2 # Marge de séparation

        # repositionnement afin que l'affichage soit aligné à droite
        if x > config.largeurFenetre - config.margeGrille :
            decalage = -(x - (config.largeurFenetre - config.margeGrille))
        else :
            decalage = (config.largeurFenetre - config.margeGrille) - x

        for rid in rids :
            self.plateau.move(rid, decalage, 0)
        for tid in self.listeTextes.values() :
            self.plateau.move(tid, decalage, 0)

    def incremente(self, tailleBateau) :
        '''
        incrémente le nombre de bateaux coulés
        @param tailleBateau     : taille du bateau venant d'être coulé
        '''
        self.bateaux[tailleBateau] += 1
        self.plateau.itemconfigure(self.listeTextes[tailleBateau],
                                  text='{}/{}'\
                                  .format(self.bateaux[tailleBateau],
                                  self.bateauxTotaux[tailleBateau]))



class MarqueurTourPlateau :
    '''
    Affiche un marqueur visuel indiquant qui à la main
    Sera centré sous chaque grille
    '''
    def __init__(self, plateau, x, y, largeur, hauteur) :
        '''
        @param plateau  : plateau du jeu
        @param x, y     :   coordonnées d'affichage
                            - x bord gauche de la grille
                            - y
        @param largeur
        @param hauteur
        x, y est la coordonnée supérieur gauche du marqueur
        '''
        self.plateau = plateau

        largeurDemiCercle = round(largeur/4)
        largeurRect = round(largeur - largeurDemiCercle / 2)

        # Bordures
        bcg = self.plateau.create_oval(x, y, x+largeurDemiCercle*2, y+hauteur,
                                       fill=':marqueur_bordure', width=0,
                                       state=tk.DISABLED)

        bcd = self.plateau.create_oval(x+largeurRect, y,
                                       x+largeurRect+largeurDemiCercle*2,
                                       y+hauteur, fill=':marqueur_bordure',
                                       width=0, state=tk.DISABLED)

        bc = self.plateau.create_rectangle(x+largeurDemiCercle, y+1,
                                           x+largeurDemiCercle+largeurRect,
                                           y+hauteur, fill=':marqueur_bordure',
                                           width=0, state=tk.DISABLED)

        def diminuer(coords, x=1, y=1) :
            return coords[0]+x, coords[1]+y, coords[2]-x, coords[3]-y

        # Fonds
        self.cg = self.plateau.create_oval(*diminuer(self.plateau.coords(bcg)),
                                            fill=':marqueur', width=0,
                                            state=tk.DISABLED)
        self.cd = self.plateau.create_oval(*diminuer(self.plateau.coords(bcd)),
                                            fill=':marqueur', width=0,
                                            state=tk.DISABLED)
        self.c = self.plateau\
                .create_rectangle(*diminuer(self.plateau.coords(bc),
                                   x=0, y=1), fill=':marqueur',
                                   width=0, state=tk.DISABLED)

    def activer(self) :
        self.plateau.itemconfigure(self.cg, fill=':marqueur_actif')
        self.plateau.itemconfigure(self.cd, fill=':marqueur_actif')
        self.plateau.itemconfigure(self.c, fill=':marqueur_actif')

    def desactiver(self) :
        self.plateau.itemconfigure(self.cg, fill=':marqueur_inactif')
        self.plateau.itemconfigure(self.cd, fill=':marqueur_inactif')
        self.plateau.itemconfigure(self.c, fill=':marqueur_inactif')



class MarqueurTirPlateau :
    '''
    Affiche un petit cercle symbolisant le dernier tir
    '''
    def __init__(self, plateau) :
        self.plateau = plateau
        self.dif = round(config.tailleCases/6)
        self.marqueur = None

    def _creer(self, *coords) :
        self.marqueur = self.plateau.create_oval(coords[0] + self.dif,
                                                 coords[1] + self.dif,
                                                 coords[2] - self.dif,
                                                 coords[3] - self.dif,
                                                 width=0, fill=':tir',
                                                 state=tk.DISABLED,
                                                 #stipple='@'+config\
                                                 #.repertoireImages\
                                                 #+'marqueur.xbm',
                                                 )

    def deplacer(self, x, y, x2, y2) :
        '''
        Déplace le marqueur sur les coordonnées spécifiées
        '''
        try :
            self.plateau.coords(self.marqueur, x + self.dif, y + self.dif,
                                x2 - self.dif, y2 - self.dif)
        except tk.TclError :
            self._creer(x, y, x2, y2)
        # Léger décalage pour que le marqueur passe au-dessus de la case venant
        # d'être créée
        self.plateau.after(10, self.plateau.lift, self.marqueur, 'cases')



class CasesGrillePlateau :
    '''
    Création et affichage des cases d'une grille à la volée.
    '''
    def __init__(self, plateau, cg, casesBateaux, liaisons=False,
                 afficherBateaux=False) :
        '''
        @param plateau          : plateau du jeu
        @param cg               : instance d'une classe CasesGrille
        @param casesBateaux     : cases occupées par les bateaux sur la grille
        @param liaisons         : booléen (False par défaut) déterminant si les
                                  cases d'un même bateau doivent être reliées
                                  les unes aux autres lors de l'affichage des
                                  cases touchées.
        @param afficherBateaux  : booléen (False par défaut) déterminant si les
                                  bateaux de la grille doivent être affichés au
                                  départ.

        '''
        self.plateau = plateau
        self.cg = cg
        self.liaisons = liaisons
        self.casesBateaux = casesBateaux

        self.casesTouchees = set()
        self.casesCoulees = set()
        self.cases = {}

        if afficherBateaux :
            for cases in self.casesBateaux.values() :
                for case in cases :
                    self._creerCase(case, ':bateau')

        # Pour relier les cases des bateaux entre elles afin de former une seule
        # pièce sur la grille, ajout entre les cases, des lignes (que l'on
        # changera de couleur si ses deux cases adjacentes changent de couleur
        # en touché ou coulé)
        # L'id de ces lignes est stocké dans un dict avec pour index un tuple
        # des 2 cases qu'elle côtoie
        couleurLigne = ':bateau' if afficherBateaux else ':grille_ligne'
        self.lignesCasesBateaux = {}
        for v in self.casesBateaux.values() :
            # 1 ligne de moins par rapport au nombre de cases
            nbLignes = len(v) - 1
            i = 0
            while i < nbLignes :
                x, y, x2, y2 = self.cg.coords(v[i])
                if v[1] - v[0] == 1 : # Bateau à l'horizontal
                    lid = self.plateau.create_line(x2, y, x2, y2, width=0,
                                                   fill=couleurLigne,
                                                   state=tk.DISABLED)
                    suivante = v[i] + 1
                else :
                    lid = self.plateau.create_line(x, y2, x2, y2, width=0,
                                                   fill=couleurLigne,
                                                   state=tk.DISABLED)
                    suivante = v[i] + config.nombreCases
                self.lignesCasesBateaux[(v[i], suivante)] = lid
                i += 1

    def _creerCase(self, case, couleur) :
        ''' Méthode interne '''
        self.cases[case] = self.plateau.create_rectangle(*self.cg.coords(case),
                                                         width=0, fill=couleur,
                                                         state=tk.DISABLED,
                                                         tags='cases')
        self.plateau.lift(self.cases[case], 'grille')


    def touche(self, case) :
        '''
        Crée (ou transforme si existante) la case spécifiée de la grille en case
        touchée
        @param case : entier
        '''
        if type(case) != int :
            raise ValueError('case doit être un entier')
        try :
            self.plateau.itemconfigure(self.cases[case], fill=':bateau_touche')
        except KeyError :
            self._creerCase(case, ':bateau_touche')

        self.casesTouchees.add(case)

        # Transformation des lignes de liaison si plus d'une case touchée
        if self.liaisons :
            for v in self.casesBateaux.values() :
                cc = self.casesTouchees & set(v)
                for c in cc :
                    for lc, lid in self.lignesCasesBateaux.items() :
                        if set(lc) == set((case, c)) :
                            self.plateau.itemconfigure(lid,
                                                       fill=':bateau_touche')


    def coule(self, cases) :
        '''
        Crée (ou transforme si existantes) les cases spécifiées de la grille en
        cases coulées.
        @param cases : liste ou tuple d'entiers
        '''
        if type(cases) not in (list, tuple) :
            raise ValueError('paramètre « cases » doit être une liste ou un'
                             ' tuple contenant des entiers')
        for case in cases :
            try :
                self.plateau.itemconfigure(self.cases[case],
                                           fill=':bateau_coule')
            except KeyError :
                self._creerCase(case, ':bateau_coule')

            self.casesCoulees.add(case)
            try :
                self.casesTouchees.remove(case)
            except KeyError :
                continue
        # Transformation des lignes de liaison
        i = 0
        while i < len(cases) - 1 :
            ti = (cases[i], cases[i+1])
            for lc, lid in self.lignesCasesBateaux.items() :
                if set(ti) == set(lc) :
                    self.plateau.itemconfigure(lid, fill=':bateau_coule')
            i += 1

    def manque(self, *cases) :
        '''
        Crée la case ou les cases spécifiées de la grille en case(s) manquée(s)
        @param cases : entier(s)
        '''
        if not cases :
            raise ValueError('Aucune case à marquer comme manquée n\'a été'
                             ' spécifiée')
        for case in cases :
            self._creerCase(case, ':grille_case_eau')


    def devoiler(self) :
        '''
        Dévoile la position des cases bateaux non touchées/coulées
        '''
        exclusion = self.casesTouchees | self.casesCoulees
        for v in self.casesBateaux.values() :
            for case in set(v) - exclusion :
                self._creerCase(case, ':bateau')
                for lc, lid in self.lignesCasesBateaux.items() :
                    if case in lc :
                        self.plateau.itemconfigure(lid, fill=':bateau')
        # Liaisons des cases touchées
        for case in self.casesTouchees :
            for lc, lid in self.lignesCasesBateaux.items() :
                if case in lc :
                    self.plateau.itemconfigure(lid, fill=':bateau_touche')

