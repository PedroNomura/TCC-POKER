# Versão do poker em python rodando no terminal, sem bot, com jogadores jogando entre si

import requests
from itertools import combinations
from pokerlib.enums import Rank, Suit
from pokerlib import HandParser

salas = []
valores = {
            '2': 2, '3': 3, '4': 4, '5': 5,
            '6': 6, '7': 7, '8': 8, '9': 9,
            'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }

class Player:
    def __init__(self, nome, chips):
        self.nome = nome
        self.fichas = chips
        self.cards = []
        self.indice_sala = -1
        self.estado = -1 # 0 = "na rodada mas não jogou", 1 = "na rodada e ja jogou", -1 = "fora da rodada"
        self.e_bb = False # atributo novo que diz se é bb
        self.e_sb = False # atributo novo que diz se é bb
        self.aposta = 0 # atributo novo

    def criar_sala(self, nome_sala, small_blind, big_blind):
        nova_sala = PokerRoom(nome_sala, 4,small_blind, big_blind)
        salas.append(nova_sala)
        self.indice_sala = len(salas) - 1 
        nova_sala.players.append(self) 
        return nova_sala

    def entrar_sala(self, nome_sala):
        for sala in salas:
            if len(sala.players) < sala.seats and sala.nome == nome_sala:
                self.indice_sala = salas.index(sala)
                sala.players.append(self)
                return True
        return False

    def coletar_cartas(self, deck_id):
        url = f"https://deckofcardsapi.com/api/deck/{deck_id}/draw/?count=2"
        self.cards = requests.get(url).json()['cards']

    # função nova
    def print_cartas(self):
        for card in self.cards:
            print(card['code'], end = " ")
        print()

    # função modificada
    def realizar_acao(self, acao, valor=None):
        sala = salas[self.indice_sala]
        if acao == 'BET':
            self.estado = 1
            self.aposta += valor
        
        elif acao == 'CALL':
            self.estado = 1
            self.aposta = valor
        
        elif acao == 'FOLD':
            self.estado = -1
            self.fichas -= self.aposta
            sala.pot += self.aposta 
            self.aposta = 0

        elif acao == 'CHECK':
            self.estado = 1
            self.aposta = 0
        
        return True

    # função nova
    def aposta_pot(self):
        sala = salas[self.indice_sala]
        self.fichas -= self.aposta
        sala.pot += self.aposta
        self.aposta = 0
# ---------------------------------------------------------------------------------------------------------------------------------------------
class PokerRoom:
    def __init__(self, nome, seats, small_blind, big_blind):
        self.nome = nome
        self.seats = seats
        self.big_blind = big_blind
        self.small_blind = small_blind
        self.players = []


        self.deck = requests.get("https://deckofcardsapi.com/api/deck/new/shuffle/?deck_count=1").json()['deck_id']
        self.pot = 0
        self.flop = []
        self.turn = []
        self.river = []

    def adicionar_jogador(self, player):
        if len(self.players) < self.seats:
            self.players.append(player)
            player.coletar_cartas(self.deck)

    def print_flop(self):
        for card in self.flop:
            print(card['code'], end = " ")
        print()

    def print_turn(self):
        print(self.turn[0]['code'])

    def print_river(self):
        print(self.river[0]['code'])

    def print_fichas(self):
        print(f"pot: {self.pot}")
        for player in self.players:
            print(f"{player.nome} ficou {player.fichas}")
        print("\n\n")


    def verificar_ganhadores(self):
        biblis = {
            'A': Rank.ACE, '2': Rank.TWO, '3': Rank.THREE, 
            '4': Rank.FOUR, '5': Rank.FIVE, '6': Rank.SIX,
            '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE,
            '0': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN,
            'K': Rank.KING, 'S': Suit.SPADE, 'C':Suit.CLUB, 'H': Suit.HEART, 'D' : Suit.DIAMOND
        }
        cartas_mesa = self.flop + self.turn + self.river
        vetor_resposta = []

        for idx,player in enumerate(self.players):
            all_cards = player.cards + cartas_mesa
            card_strings = [card['code'] for card in all_cards]
            cartas_jogador = HandParser([])
            for card in card_strings:
                carta = [(biblis[card[0]],biblis[card[1]])]
                cartas_jogador += carta
            vetor_resposta.append((cartas_jogador, player))
        vetor_resposta = sorted(vetor_resposta, reverse=True)
        vencedores = []
        vencedores.append(vetor_resposta[0])
        i = 1
        while vetor_resposta[0][0] == vetor_resposta[i][0]:
            vencedores.append(vetor_resposta[i][0])
            i += 1
        return vencedores

    # função nova
    def verifica_unico_jogador(self):
        jogadores_ativos = [player for player in self.players if player.estado != -1]
        if len(jogadores_ativos) == 1:
            return jogadores_ativos[0]
        return None

    # função nova 
    def rodada_aposta(self,maior,inicial =False):
        while any(player.estado == 0 for player in self.players):
            for player in self.players:
                if player.estado == 0:
                    acao = "" 
                    print(f"\n\njogador {player.nome} -- ", end="")
                    while acao not in ["CALL", "BET", "FOLD", "CHECK"]:
                        acao = input("ação: ").upper()
                        
                        if acao == "BET":
                            valor = int(input("valor: "))
                            player.realizar_acao("BET",valor)
                            maior += valor

                            # teste (parece correto)
                            aux = maior
                            if player.e_bb and inicial:
                                aux = maior - self.big_blind
                            if player.e_sb and inicial:
                                aux = maior - self.small_blind
                            player.realizar_acao("CALL",aux)
                            # fim de teste

                            for p in self.players:
                                if p != player and p.estado != -1:
                                    p.estado = 0
                        elif acao == "CALL":
                            aux = maior
                            if player.e_bb and inicial:
                                aux = maior - self.big_blind
                            if player.e_sb and inicial:
                                aux = maior - self.small_blind
                            player.realizar_acao("CALL",aux)
                        elif acao == "FOLD":
                            player.realizar_acao("FOLD")
                        elif acao == "CHECK":
                            player.realizar_acao("CHECK")

        for player in self.players:
            player.aposta_pot()
            if player.estado != -1:
                player.estado = 0

    def iniciar_rodada(self):
        # Verifica se há 2 ou mais jogadores (TESTE)
        if len(self.players) < 2 or any(player.fichas == 0 for player in self.players):
            return None

        # distribui as cartas para cada player e atribui o estado 0 que indica "a jogar"
        for p in range(len(self.players)):
            self.players[p].estado = 0
            self.players[p].coletar_cartas(self.deck)
            self.players[p].print_cartas() 
            
            # define que o ultimo é o BB
            if p == len(self.players) - 1:
                self.players[p].fichas -= self.big_blind
                self.players[p].e_bb = True 
                self.pot += self.big_blind
                print(f"BB: {self.players[p].nome}\n\n")

            # define que o penultimo é o SB
            elif p == len(self.players) - 2:
                self.players[p].fichas -= self.small_blind
                self.players[p].e_sb = True
                self.pot += self.small_blind
                print(f"SB: {self.players[p].nome}\n\n")
            


        # aqui pega no front ação de cada player
        # site que eu vi legal pra "roubar o css" == https://www.247freepoker.com/ (◠‿◠)

        # PRE-FLOP
        self.print_fichas()
        self.rodada_aposta(self.big_blind,True)
        self.print_fichas()

        vencedor = self.verifica_unico_jogador()
        if vencedor is not None:
            print(f"O vencedor é {vencedor.nome}!")
            return vencedor

        # FLOP
        self.flop = requests.get(f"https://deckofcardsapi.com/api/deck/{self.deck}/draw/?count=3").json()['cards']
        print("FLOP: ")
        self.print_flop()
        print()


        self.rodada_aposta(0)
        self.print_fichas()

        vencedor = self.verifica_unico_jogador()
        if vencedor is not None:
            print(f"O vencedor é {vencedor.nome}!")
            return vencedor

        # TURN
        self.turn = requests.get(f"https://deckofcardsapi.com/api/deck/{self.deck}/draw/?count=1").json()['cards']
        print("TURN: ")
        self.print_turn()
        print()

        self.rodada_aposta(0)
        self.print_fichas()

        vencedor = self.verifica_unico_jogador()
        if vencedor is not None:
            print(f"O vencedor é {vencedor.nome}!")
            return vencedor

        # RIVER
        self.river = requests.get(f"https://deckofcardsapi.com/api/deck/{self.deck}/draw/?count=1").json()['cards']
        print("RIVER: ")
        self.print_river()
        print()

        self.rodada_aposta(0)
        self.print_fichas()

        vencedor = self.verifica_unico_jogador()
        if vencedor is not None:
            print(f"O vencedor é {vencedor.nome}!")
            return vencedor

        # Após o river, verificar o vencedor (tem que ver a parada do empate)
        vencedores = self.verificar_ganhadores()

        # imprime o que o(s) vencedor(es) tem
        lib = {0 : "HIGHCARD", 1: "ONEPAIR", 2:"TWOPAIR",3: "THREEOFAKIND", 4 : "STRAIGHT", 5: "FLUSH", 6: "FULLHOUSE", 7: "FOUROFAKIND", 8: "STRAIGHTFLUSH"}
        for winner in vencedores:
            print(f"VENCEDOR FOI {winner[1].nome} tendo {lib[winner[0].handenum]}\n\n")

        # da pra o vitorioso o pot, considerando que não temos empate
        vencedores[0][1].fichas += self.pot
        self.pot = 0
        self.print_fichas()

        # troca o BB e SB
        BB = self.players.pop(0)
        self.players.append(BB)

        # retorna as cartas para o deck
        requests.get(f"https://deckofcardsapi.com/api/deck/{self.deck}/return/")
        requests.get(f"https://deckofcardsapi.com/api/deck/{self.deck}/shuffle/") 

        # coloquei so pra ficar em looping
        self.iniciar_rodada()
        
        return vencedores

# ------------------------------------------------------------------------------------------------------------------------------------------------
def listar_partidas():
    if not salas:
        print("Nenhuma partida disponível no momento.")
        return []
    else:
        print("Partidas disponíveis:")
        for idx, sala in enumerate(salas):
            print(f"{idx}. Nome: {sala.nome}, Cadeiras: {sala.seats}, Blinds: {sala.big_blind}/{sala.small_blind}, Jogadores: {len(sala.players)}")
        return salas


def iniciar_partida(indice_sala):
    try:
        sala = salas[indice_sala]
        if len(sala.players) > 1:
            sala.start()
            print(f"Partida '{sala.nome}' iniciada com sucesso!")
            return True
        else:
            print(f"Partida '{sala.nome}' não iniciada! Precisa de mais jogadores.")
            return False
    except IndexError:
        print(f"Erro: Não existe uma partida no índice {indice_sala}.")
        return False

jogador = Player('victor', 5000)
jogador2 = Player('joao',5000)
sala_jogador = jogador.criar_sala('sala1',5,10)
jogador2.entrar_sala("sala1")
sala_jogador.iniciar_rodada()
