class Responsable:
        def __init__(self, NoAllee, Nom):
                self.NoAllee = NoAllee
                self.Nom = Nom
                
 
class Miam:
        def __init__(self, NomAlien, Aliment):
                self.NomAlien = NomAlien
                self.Aliment = Aliment
                
 
class Agent:
        def __init__(self, Nom, Ville):
                self.Nom = Nom
                self.Ville = Ville
                
 
class Gardien:
        def __init__(self, Nom, NoCabine):
                self.Nom = Nom
                self.NoCabine = NoCabine
                
 
class Alien:
        def __init__(self, Nom, Sexe, Planete, NoCabine):
                self.Nom = Nom
                self.Sexe = Sexe
                self.Planete = Planete
                self.NoCabine = NoCabine
                
 
class Cabine:
        def __init__(self, NoCabine, NoAllee):
                self.NoCabine = NoCabine
                self.NoAllee = NoAllee
                
 
BaseResponsables = { Responsable('1', 'Seldon'), Responsable('2', 'Pelorat') }
 
BaseMiams = { Miam('Zorglub', 'Bortsch'), Miam('Blorx', 'Bortsch'), Miam('Urxiz', 'Zoumise'), Miam('Zbleurdite', 'Bortsch'), Miam('Darneurane', 'Schwanstucke'), Miam('Mulzo', 'Kashpir'), Miam('Zzzzzz', 'Kashpir'), Miam('Arghh', 'Zoumise'), Miam('Joranum', 'Bortsch') }
 
BaseAgents = { Agent('Branno', 'Terminus'), Agent('Darell', 'Terminus'), Agent('Demerzel', 'Uco'), Agent('Seldon', 'Terminus'), Agent('Dornick', 'Kalgan'), Agent('Hardin', 'Terminus'), Agent('Trevize', 'Hesperos'), Agent('Pelorat', 'Kalgan'), Agent('Riose', 'Terminus') }
 
BaseGardiens = { Gardien('Branno', '1'), Gardien('Darell', '2'), Gardien('Demerzel', '3'), Gardien('Seldon', '4'), Gardien('Dornick', '5'), Gardien('Hardin', '6'), Gardien('Trevize', '7'), Gardien('Pelorat', '8'), Gardien('Riose', '9') }
 
BaseAliens = { Alien('Zorglub', 'M', 'Trantor', '1'), Alien('Blorx', 'M', 'Euterpe', '2'), Alien('Urxiz', 'M', 'Aurora', '3'), Alien('Zbleurdite', 'F', 'Trantor', '4'), Alien('Darneurane', 'M', 'Trantor', '4'), Alien('Mulzo', 'M', 'Helicon', '6'), Alien('Zzzzzz', 'F', 'Aurora', '7'), Alien('Arghh', 'M', 'Nexon', '8'), Alien('Joranum', 'F', 'Euterpe', '9') }
 

BaseCabines = { Cabine('1', '1'), Cabine('2', '1'), Cabine('3', '1'), Cabine('4', '1'), Cabine('5', '1'), Cabine('6', '2'), Cabine('7', '2'), Cabine('8', '2'), Cabine('9', '2') }

from MaBase_MIB import *

### Question 1 :
les_gardiens = {g.Nom for g in BaseGardiens}
print("1) Les noms des gardiens sont : ", les_gardiens)

### Question 2 :
les_villes_agent = {agent.Ville for agent in BaseAgents}
print("2) Les villes des agents sont : ", les_villes_agent)

### Question 3 :
triples = { (alien.NoCabine, alien.Nom, gardien.Nom) for alien in BaseAliens  for gardien in BaseGardiens if gardien.NoCabine == alien.NoCabine}
print("3) Le numéro de cabine et l'alien de chaque gardiens sont : ", triples)


### Question 4 :
allée_alien = {(Alien.Nom, Cabine.NoAllee) for Alien in BaseAliens for Cabine in BaseCabines if Alien.NoCabine == Cabine.NoCabine}
print("4) Les allées correspondants aux aliens sont : ", allée_alien)

### Question 5 :
allée2 = {(Alien.Nom) for Alien in BaseAliens for Cabine in BaseCabines if Alien.NoCabine == Cabine.NoCabine if Cabine.NoAllee == '2'}
print ("5) Les aliens dans l'allée 2 sont : ", allée2)

### Question 6 :
planetepair = {(Alien.Planete) for Alien in BaseAliens if Alien.NoCabine == '2' or '4' or '6' or '8'}
print ("6) Voici les planètes où les aliens sont dans une pair : ", planetepair)

### Question 7 :
AGT = {(Alien.Nom) for Agent in BaseAgents for Gardien in BaseGardiens for Alien in BaseAliens if Agent.Ville == 'Terminus' if Agent.Nom == Gardien.Nom if Gardien.NoCabine == Alien.NoCabine}
print ("7) Les aliens surveillés par les agents venant de Terminus sont : ", AGT)

### Question 8 :
GAB = {(Gardien.Nom) for Miam in BaseMiams for Alien in BaseAliens for Gardien in BaseGardiens if Miam.Aliment == 'Bortsch' if Miam.NomAlien == Alien.Nom if Alien.Sexe == 'F' if Alien.NoCabine == Gardien.NoCabine}
print ("8) Voici les gardiens des aliens féminines mangeant du Bortsch : ", GAB)

### Question 9 :
# cgt = cabine où les gardiens viennent de Terminus
# caf = cabine d'alien féminines
CGT = {(Gardien.NoCabine) for Agent in BaseAgents for Gardien in BaseGardiens if Agent.Ville == 'Terminus' if Agent.Nom == Gardien.Nom}
CAF = {(Alien.NoCabine) for Alien in BaseAliens if Alien.Sexe == 'F'}
print ("9) Les cabines dont les gardiens viennent de Terminus sont : ", CGT, "et les cabines dont les aliens sont des filles sont : ", CAF)

### Question 10 :
# la = lettre aliment
la = {(Miam.Aliment, Gardien.Nom, Alien.Nom) for Alien in BaseAliens for Gardien in BaseGardiens for Miam in BaseMiams if Miam.NomAlien == Alien.Nom if Alien.NoCabine == Gardien.NoCabine if Gardien.Nom[0] == Miam.Aliment[0]}
print ("10) Voici la liste des aliments qui commencent par la même lettre que le nom du gardien qui surveille l'alien qui les manges : ", la)

### Question 11 :
# ae = alien originaire d'Euterpe
ae ={(Alien.Nom, Alien.Planete) for Alien in BaseAliens if Alien.Planete == 'Euterpe'}
print ("11) Voici la liste des aliens originaires d'Euterpe : ", ae)

### Question 12 :
# xna = si il y a un x dans tout les noms des aliens
xna = {(Alien.Nom) for Alien in BaseAliens if 'x' in Alien.Nom}
an = 'Alien.Nom'
k = an.count('x')
if (k==9):
    print ("12) Tous ces aliens ont des x dans leurs noms : ", xna)
else:
    print ("12) Tous les aliens n'ont pas de x dans leurs noms, voici ceux qui en ont : ", xna)

### Question 13 :
# agt = aliens qui ont un x dans leur nom et dont le gardien viens de Terminus
agt = {(Alien.Nom, Agent.Nom) for Alien in BaseAliens for Gardien in BaseGardiens for Agent in BaseAgents if 'x' in Alien.Nom if Agent.Ville == 'Terminus' if Agent.Nom == Gardien.Nom if Gardien.NoCabine == Alien.NoCabine}
if (xna == agt):
    print ("13) Tous ces aliens qui ont un x dans leur nom ont des gardiens qui viennent de Terminus : ", agt)
else:
    print ("13) Tous les aliens qui ont un x dans leur nom n'ont pas de gardien venant de Terminus, les voici : ", agt)

### Question 14 :
# zy = alien masculin originaire de Trantor qui mange du bortsch
# zz = alien masculin originaire de Trantor qui a un gardien venant de Terminus
zy = {(Alien.Nom) for Alien in BaseAliens for Miam in BaseMiams if Alien.Sexe == 'M' if Alien.Planete == 'Trantor' if Alien.Nom == Miam.NomAlien if Miam.Aliment == 'Bortsch'}
zz = {(Alien.Nom) for Alien in BaseAliens for Gardien in BaseGardiens for Agent in BaseAgents if Alien.Sexe == 'M' if Alien.Planete == 'Trantor' if Alien.NoCabine == Gardien.NoCabine if Gardien.Nom == Agent.Nom if Agent.Ville == 'Terminus'}
if (zy == zz):
    print ("14) Il(s) existe(s) un alien(s) masculin originaire de Trantor qui mange du Bortsch ou dont le gardien vient de Terminus, les ou les voici : ", zz)
else:
    print ("14) Il existe un alien masculin originaire de Trantor qui mange du Bortsch ou dont le gardien vient de Terminus, le voici : ", zy, zz)
