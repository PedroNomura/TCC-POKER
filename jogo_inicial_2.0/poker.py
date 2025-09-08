import pygame
import sys
import random
from pokerlib.enums import Rank, Suit
from pokerlib import HandParser
import cv2
import time
from deepface import DeepFace
import numpy as np

# TODO arrumar os logs pra ficar melhor
# TODO fazer alguns bangs visuais
# TODO implementar a bomba da IA (SOON)
    # pro monte carlo - jogador.cartas + cartas_mesa + bot.cartas (pro monte carlo vai passar as cartas do player? tipo não é justo)
# TODO revisar codigo/bugs (VERY SOON)

hertz = 144 # TODO esse valor tem que ser a taxa de atualização do seu monitor (hertz)
velocidade = 500 # velocidade das animações 

# variaveis do bot
BOT_RECONHER = True # ativar o reconhecimento (SOON) 
ITERACOES_MONTE_CARLO = 10000
VALOR_MINIMO_D = 50
PESOS_EMOCAO = {
    "happy": 2,
    "sad": 1.5,
    "angry": 1.5,
    "fear": 1,
    "disgust": 1,
    "surprise": 1
}

# pré-carrega modelo de emoção
preload_frame = np.zeros((100, 100, 3), dtype=np.uint8)
DeepFace.analyze(preload_frame, actions=["emotion"], enforce_detection=False)

# pra estilo
DISTANCIA_MESA_D_USUARIO = 10 # distancia dos detalhes 
grade = False # ativar grade pra ajustar os desenhos
FUNDO = "img/cards/closed.png" 
mensagens_log = []
MAX_MENSAGENS = 6  # máximo de mensagens visíveis
mostra_bot = False

espera_jogador = False
acao = ""
valor = 0
# tela de vitoria
# mostra_vencedor = False
# duracao_vitoria = 4000
# tela_vitoria_ini = 0


def log_mensagem(texto):
    if len(mensagens_log) >= MAX_MENSAGENS:
        mensagens_log.pop(0)  # remove a mais antiga
    mensagens_log.append(texto)


# variaveis do jogo
FICHAS = 10000 # numeros de fichas
BIG_BLIND = 100 # valor do big blind
SMALL_BLIND = 50 # valor do small blind

# Tamanho da tela
WIDTH, HEIGHT = 1500, 760 # TODO ver se ta bom # Mudei 1700, 860 
#WIDTH, HEIGHT = 1920, 1080 # (1920x1080 pra tela cheia)

# botoes e caixa de texto
botao_check = pygame.Rect(DISTANCIA_MESA_D_USUARIO, HEIGHT - 80, 200, 60)
botao_call = pygame.Rect(DISTANCIA_MESA_D_USUARIO, HEIGHT - 80, 200, 60)
botao_fold = pygame.Rect(200 + DISTANCIA_MESA_D_USUARIO * 2, HEIGHT - 80, 200, 60)
botao_bet = pygame.Rect(400 + DISTANCIA_MESA_D_USUARIO * 3, HEIGHT -80, 200, 60) 

input_ativo = False
input_texto = ""
input_rect = pygame.Rect(botao_bet.x, botao_bet.y - botao_bet.height - 10, 200, 60)
cor_inativa = (150, 150, 150)
cor_ativa = (255, 255, 255)
cor_input = cor_inativa

# não mexer sem conhecimento
cartas_mesa = []
cartas_deck = ["AC","AD","AH","AS",
"2C","2D","2H","2S",
"3C","3D","3H","3S",
"4C","4D","4H","4S",
"5C","5D","5H","5S",
"6C","6D","6H","6S",
"7C","7D","7H","7S",
"8C","8D","8H","8S",
"9C","9D","9H","9S",
"10C","10D","10H","10S",
"JC","JD","JH","JS",
"QC","QD","QH","QS",
"KC","KD","KH","KS",]
fim_de_jogo = False
img_cartas_jogador = []
img_cartas_bot = []
imgs_mesa = []
fase = "inicio"
pote = 0
pote_aux = 0
e_pre_flop = True
aposta_minima = 0

# classe Player, tanto para jogador e bot
class Player:
    def __init__(self,fichas,blind,cartas,e_bot):
        self.nome = "Voce" if not e_bot else "Bot" 
        self.fichas = fichas
        self.blind = blind
        self.cartas = cartas
        self.e_bot = e_bot
        self.aposta = 0

    def set_cartas(self,cartas):
        self.cartas = cartas

    def paga(self,bet):
        if (bet > self.fichas):
            self.aposta = self.fichas
            self.fichas = 0
            return self.fichas
        self.fichas = self.fichas - bet
        self.aposta = bet
        return bet

    def devolve_cartas(self):
        cartas_d = self.cartas
        self.cartas = None
        return cartas_d

# Player("quantas fichas tem", "SB ou BB", "Cartas", "booleana do bot")
jogador = Player(FICHAS/2,SMALL_BLIND,None, False) # info do jogador 
bot = Player(FICHAS/2,BIG_BLIND,None, True) # info do bot

def restart():
    global jogador,bot,cartas_mesa,cartas_deck,fim_de_jogo,img_cartas_jogador,img_cartas_bot,imgs_mesa,fase,pote,pote_aux,e_pre_flop,aposta_minima
    jogador = Player(FICHAS/2,SMALL_BLIND,None, False) # info do jogador 
    bot = Player(FICHAS/2,BIG_BLIND,None, True) # info do bot
    cartas_mesa = []
    cartas_deck = ["AC","AD","AH","AS",
    "2C","2D","2H","2S",
    "3C","3D","3H","3S",
    "4C","4D","4H","4S",
    "5C","5D","5H","5S",
    "6C","6D","6H","6S",
    "7C","7D","7H","7S",
    "8C","8D","8H","8S",
    "9C","9D","9H","9S",
    "10C","10D","10H","10S",
    "JC","JD","JH","JS",
    "QC","QD","QH","QS",
    "KC","KD","KH","KS",]
    fim_de_jogo = False
    img_cartas_jogador = []
    img_cartas_bot = []
    imgs_mesa = []
    fase = "inicio"
    pote = 0
    pote_aux = 0
    e_pre_flop = True
    aposta_minima = 0

# Inicialização
pygame.init()
cap = cv2.VideoCapture(0)
time.sleep(0.5)

# chat que vez mas para quebrar o texto (auxiliar e opcional)
def draw_multiline_text(text, color, rect, surface, line_height=30):
    lines = text.split('\n')
    for i, line in enumerate(lines):
        label = font.render(line, True, color)
        line_rect = label.get_rect(center=(rect.centerx, rect.centery + i * line_height - (len(lines) - 1) * line_height // 2))
        surface.blit(label, line_rect)



screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Mesa de Poker com IA | {'ON' if BOT_RECONHER else 'OFF'}") # titulo 

# Cores
GREEN = (34, 139, 34)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 69 ,0 )
BLUE = (50,50,50)
DEALER_COLOR = (200, 0, 0)
PLAYER_COLOR = (0, 100, 255)
BOT_COLOR = (139, 0, 139)
CARD_COLOR = (255, 255, 255)

# Fonte

# aceitavel pelo pygame 
# ['dejavuserif', 'urwbookman', 'dejavusansmono', 'liberationmono', 'dejavusans', 'nimbusmonops', 'notosansmono', 'p052', 
# 'nimbussans', 'liberationsans', 'nimbussansnarrow', 'c059', 'quicksandlight', 'z003', 'urwgothic', 'd050000l', 'liberationserif', 
# 'nimbusroman', 'cantarell', 'opensymbol', 'symbola', 'dejavumathtexgyre', 'droidsansfallback', 'quicksand', 'quicksandmedium', 
# 'standardsymbolsps', 'notomono', 'notocoloremoji']

font = pygame.font.SysFont("Arial", 20, bold=True) 

# Função para desenhar o texto centralizado
def draw_text(text, color, rect, surface):
    label = font.render(text, True, color)
    text_rect = label.get_rect(center=rect.center)
    surface.blit(label, text_rect)



# Loop principal
clock = pygame.time.Clock()
running = True

# Mesa
table_rect = pygame.Rect(WIDTH // 2 - 600, HEIGHT // 2 - 250, 1200, 500) # TODO ver tamanho porem se mexer fode logo cuidado

# Dealer
dealer_rect = pygame.Rect(WIDTH // 2 - 50, table_rect.bottom + DISTANCIA_MESA_D_USUARIO, 100, 50) # TODO ver tamanho

# Jogador
player_rect = pygame.Rect(table_rect.left - 120 - DISTANCIA_MESA_D_USUARIO, HEIGHT // 2 - 25, 120, 50) # TODO ver tamanho
player_chips_bet_rect = pygame.Rect(table_rect.midleft[0]  + DISTANCIA_MESA_D_USUARIO*2, player_rect.topright[1],100,50) # TODO ver tamanho

# Bot
bot_rect = pygame.Rect(table_rect.right , HEIGHT // 2 - 50, 200, 100) # TODO ver tamanho
bot_chips_bet_rect = pygame.Rect(table_rect.midright[0] - DISTANCIA_MESA_D_USUARIO*2 - 100, bot_rect.midleft[1]- 25,100,50) # TODO ver tamanho

# Pote
fichas_mesa = pygame.image.load("img/fichas.png")
fichas_mesa = pygame.transform.scale(fichas_mesa, (114,163)) # TODO ver tamanho
fichas_mesa_pos = (table_rect.centerx - 50,table_rect.centery + 40)
pote_rect = pygame.Rect(fichas_mesa_pos[0]+130,fichas_mesa_pos[1],100,50) # TODO ver tamanho

# Baralho
baralho = pygame.image.load(FUNDO).convert_alpha()
baralho = pygame.transform.scale(baralho, (114,163)) # TODO ver tamanho
baralho_pos = (table_rect.centerx + 100, dealer_rect.left - 200)

# Jarda TODO da pra por a camera (seria foda)
jarda = pygame.image.load("img/jarda.png").convert_alpha()
jarda = pygame.transform.scale(jarda, (150,150)) # TODO ver tamanho
jarda_pos = (player_rect.centerx - 75 - DISTANCIA_MESA_D_USUARIO, player_rect.centery - 150 + DISTANCIA_MESA_D_USUARIO)
partida = True

# Jogo
def pre_flop():
    global pote, e_pre_flop
    e_pre_flop = True
    # paga os SB e BB
    pote += jogador.paga(jogador.blind)
    pote += bot.paga(bot.blind)

    # embaralha o deck
    random.shuffle(cartas_deck)

    # jogador recebe as cartas
    jogador.set_cartas([cartas_deck.pop(),cartas_deck.pop()])

    # bot recebe as cartas
    bot.set_cartas([cartas_deck.pop(),cartas_deck.pop()])

    # salva as cartas do player no vetor img_cartas_jogador (esta aqui porque fica bugando em outros lugares)
    for nome in jogador.cartas:
        img = pygame.image.load(f"img/cards/{nome}.png")
        img = pygame.transform.scale(img, (114,163)) # TODO ver tamanho da carta
        img_cartas_jogador.append(img)
        img_cartas_bot.append(baralho)


    # salva o fundo das cartas no vetor imgs_mesa, por enquanto todas viradas pra baixo
    for i in range(5):
        imgs_mesa.insert(i,baralho)

    # print pro jogada via terminal
    print("(",jogador.fichas,") jogador:",jogador.cartas)
    print("(",bot.fichas,") bot:",bot.cartas,"\n")

    log_mensagem(f"Jogador ({int(jogador.fichas)}): {jogador.cartas}")
    if mostra_bot:
        log_mensagem(f"Bot ({int(bot.fichas)}): {bot.cartas}")



def flop():

    # da as cartas do flop
    cartas_mesa.insert(0,cartas_deck.pop())
    cartas_mesa.insert(1,cartas_deck.pop())
    cartas_mesa.insert(2,cartas_deck.pop())

    # modifica no vetor imgs_mesa as imagens das cartas do flop 
    for i in range(3):
        img = pygame.image.load(f"img/cards/{cartas_mesa[i]}.png")
        img = pygame.transform.scale(img,(114,163)) # TODO ver tamanho da carta
        imgs_mesa.insert(i,img)

    # print pro jogada via terminal
    print("(",jogador.fichas,") jogador:",jogador.cartas)
    print("(",bot.fichas,") bot:",bot.cartas)
    print("(",pote,") mesa:",cartas_mesa,"\n")


    # log_mensagem(f"Jogador ({int(jogador.fichas)}): {jogador.cartas}")
    # if mostra_bot:
    #     log_mensagem(f"Bot ({int(bot.fichas)}): {bot.cartas}")
    # log_mensagem(f"Mesa ({int(pote)}): {cartas_mesa}")


# posicao das cartas do bot pra animacao
carta_posicoes_bot = [pygame.Vector2(baralho_pos) for _ in range(2)]
cartas_bot_alvos = [
    pygame.Vector2(
        bot_rect.midbottom[0] - DISTANCIA_MESA_D_USUARIO - i*(114+DISTANCIA_MESA_D_USUARIO),
        bot_rect.bottom + DISTANCIA_MESA_D_USUARIO
    )
    for i in range(2)
]

def turn():
    # da a carta do turn 
    cartas_mesa.insert(3,cartas_deck.pop())

    # modifica a imagem no vetor imgs_mesa
    img = pygame.image.load(f"img/cards/{cartas_mesa[3]}.png")
    img = pygame.transform.scale(img,(114,163)) # TODO ver tamanho da carta
    imgs_mesa.insert(3,img)

    # print pro jogada via terminal
    print("(",jogador.fichas,") jogador:",jogador.cartas)
    print("(",bot.fichas,") bot:",bot.cartas)
    print("(",pote,") mesa:",cartas_mesa,"\n")

    # log_mensagem(f"Jogador ({int(jogador.fichas)}): {jogador.cartas}")
    # if mostra_bot:
    #     log_mensagem(f"Bot ({int(bot.fichas)}): {bot.cartas}")
    # log_mensagem(f"Mesa ({int(pote)}): {cartas_mesa}")


def river():
    # da a carta do river
    cartas_mesa.insert(4,cartas_deck.pop())

    # modifica a imagem no vetor imgs_mesa
    img = pygame.image.load(f"img/cards/{cartas_mesa[4]}.png")
    img = pygame.transform.scale(img, (114,163)) # TODO ver tamanho da carta
    imgs_mesa.insert(4,img)

    # print pro jogada via terminal
    print("(",jogador.fichas,") jogador:",jogador.cartas)
    print("(",bot.fichas,") bot:",bot.cartas)
    print("(",pote,") mesa:",cartas_mesa,"\n")

    # log_mensagem(f"Jogador ({int(jogador.fichas)}): {jogador.cartas}")
    # if mostra_bot:
    #     log_mensagem(f"Bot ({int(bot.fichas)}): {bot.cartas}")
    # log_mensagem(f"Mesa ({int(pote)}): {cartas_mesa}")


def verifica_perdedor():
    biblis = {
            'A': Rank.ACE, '2': Rank.TWO, '3': Rank.THREE, 
            '4': Rank.FOUR, '5': Rank.FIVE, '6': Rank.SIX,
            '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE,
            '10': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN,
            'K': Rank.KING, 'S': Suit.SPADE, 'C':Suit.CLUB, 'H': Suit.HEART, 'D' : Suit.DIAMOND
        }
    hand_jogador = HandParser([])
    hand_bot = HandParser([])
    for i in range(2):
        valor = jogador.cartas[i][:-1]
        naipe = jogador.cartas[i][-1]
        hand_jogador += [(biblis[valor],biblis[naipe])]
        valor = bot.cartas[i][:-1]
        naipe = bot.cartas[i][-1]
        hand_bot += [(biblis[valor],biblis[naipe])]

    for i in range(len(cartas_mesa)):
        valor = cartas_mesa[i][:-1]
        naipe = cartas_mesa[i][-1]
        hand_jogador += [(biblis[valor],biblis[naipe])]
        hand_bot += [(biblis[valor],biblis[naipe])]

    tipo_mao = {
    0: "HIGHCARD",
    1: "ONEPAIR",
    2: "TWOPAIR",
    3: "THREEOFAKIND",
    4: "STRAIGHT",
    5: "FLUSH",
    6: "FULLHOUSE",
    7: "FOUROFAKIND",
    8: "STRAIGHTFLUSH"
    }

    print(f"\n\njogador {tipo_mao[hand_jogador.handenum]} com {sorted(jogador.cartas+cartas_mesa)}\nbot {tipo_mao[hand_bot.handenum]} com {sorted(bot.cartas+cartas_mesa)}\n\n")
    log_mensagem(f"jogador {tipo_mao[hand_jogador.handenum]}")
    log_mensagem(f"bot {tipo_mao[hand_bot.handenum]}")
    
    if hand_jogador == hand_bot:
        return None
    elif hand_jogador > hand_bot:
        return bot 
    else:
        return jogador

# caso perdedor seja None indica que chegou ao showdown e precisa verificar quem ganha, se não perdedor foi quem deu fold
def fim_rodada(perdedor=None):
    global cartas_deck, cartas_mesa, pote, jogador, bot, pote_aux
    log_mensagem(f"Jogador ({int(jogador.fichas)}): {jogador.cartas}")
    log_mensagem(f"Bot ({int(bot.fichas)}): {bot.cartas}")
    log_mensagem(f"Mesa ({int(pote)}): {sorted(cartas_mesa)}")

    # caso venha None precisa verificar
    if perdedor == None:
        for i in range(2):
            img = pygame.image.load(f"img/cards/{bot.cartas[i]}.png")
            img = pygame.transform.scale(img, (114,163)) # TODO ver tamanho da carta
            img_cartas_bot.insert(i,img)
        perdedor = verifica_perdedor()

    # caso o verificador retornou None é empate e precisa dividir o pote
    if perdedor == None:
        bot.fichas = bot.fichas + int(pote/2)
        jogador.fichas = jogador.fichas + int(pote/2)

    # vitoria do bot
    elif perdedor != bot:
        bot.fichas = bot.fichas + pote

    # vitoria do jogador
    else:
        jogador.fichas = jogador.fichas + pote

    # zera o pote
    pote = 0
    pote_aux = 0
    if perdedor != None:
    # print pro jogada via terminal
        print(f"\nperdedor {perdedor.nome}\n")
        log_mensagem(f"{perdedor.nome.upper()} foi perdedor")
    else:
        print("\nEMPATE\n")
        log_mensagem("EMPATE")
    
    # TODO mensagem que mostra vencedor

    # troca categoria do blind (SB vira BB e BB vira SB)
    if jogador.blind == BIG_BLIND:
        jogador.blind = SMALL_BLIND
        bot.blind = BIG_BLIND
    else:
        jogador.blind = BIG_BLIND
        bot.blind = SMALL_BLIND

    # retorna as cartas ao deck e limpa as cartas da mesa
    cartas_deck += jogador.devolve_cartas() + bot.devolve_cartas() + cartas_mesa 
    cartas_mesa = []

    # limpa as cartas dos players
    jogador.set_cartas([None, None])
    bot.set_cartas([None, None])

    # serve pra limpar as animações (não mexer)
    img_cartas_jogador.clear()
    img_cartas_bot.clear()
    imgs_mesa.clear()
    carta_posicoes_bot[:] = [pygame.Vector2(baralho_pos) for _ in range(2)]
    cartas_bot_movendo[:] = [True, True]
    carta_posicoes_player[:] = [pygame.Vector2(baralho_pos) for _ in range(2)]
    cartas_player_movendo[:] = [True, True]
    carta_posicoes_mesa[:] = [pygame.Vector2(baralho_pos) for _ in range(5)]
    cartas_mesa_movendo[:] = [True,True,True,True,True]

    # print pro jogada via terminal
    # print(f"bot é {"BB" if bot.blind == BIG_BLIND else "SB"}")
    # print(f"jogador é {"BB" if jogador.blind == BIG_BLIND else "SB"}")


def pegar_probabilidades_webcam_tempo(cap, duracao=5, pesos=PESOS_EMOCAO):
    if not cap.isOpened():
        print("Erro: webcam não está aberta.")
        return None

    inicio = time.time()
    lista_probs = []
    frame_count = 0

    while time.time() - inicio < duracao:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            resultado = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=True)
            if isinstance(resultado, list):
                resultado = resultado[0]

            # Ignora o primeiro frame para evitar atraso inicial
            if frame_count > 0:
                # Remove "neutral" antes de armazenar
                emo_frame = {k: v for k, v in resultado["emotion"].items() if k != "neutral"}
                lista_probs.append(emo_frame)

            frame_count += 1

        except Exception as e:
            print("Erro em um frame:", e)

    if not lista_probs:
        return None

    # calcular média das probabilidades (ignorando "neutral")
    chaves = lista_probs[0].keys()
    medias = {chave: np.mean([d[chave] for d in lista_probs]) for chave in chaves}

    # aplicar pesos se fornecidos
    if pesos:
        for emo, peso in pesos.items():
            if emo in medias:
                medias[emo] *= peso

    return medias

def MC_verifica_perdedor(MC_cartas_jogador, MC_mesa):
    biblis = {
            'A': Rank.ACE, '2': Rank.TWO, '3': Rank.THREE, 
            '4': Rank.FOUR, '5': Rank.FIVE, '6': Rank.SIX,
            '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE,
            '10': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN,
            'K': Rank.KING, 'S': Suit.SPADE, 'C':Suit.CLUB, 'H': Suit.HEART, 'D' : Suit.DIAMOND
        }
    hand_jogador = HandParser([])
    hand_bot = HandParser([])
    for i in range(2):
        valor = MC_cartas_jogador[i][:-1]
        naipe = MC_cartas_jogador[i][-1]
        hand_jogador += [(biblis[valor],biblis[naipe])]
        valor = bot.cartas[i][:-1]
        naipe = bot.cartas[i][-1]
        hand_bot += [(biblis[valor],biblis[naipe])]

    for i in range(len(MC_mesa)):
        valor = MC_mesa[i][:-1]
        naipe = MC_mesa[i][-1]
        hand_jogador += [(biblis[valor],biblis[naipe])]
        hand_bot += [(biblis[valor],biblis[naipe])]
     
    if hand_jogador > hand_bot: 
        return 0 
    else:
        return 1


def monte_carlo():

    MC_vitorias_bot = 0

    for i in range(ITERACOES_MONTE_CARLO):
        MC_deck = cartas_deck.copy()
        random.shuffle(MC_deck)

        MC_cartas_jogador = [MC_deck.pop(), MC_deck.pop()]
        MC_mesa = cartas_mesa.copy()
        for j in range(5-len(MC_mesa)):
            MC_mesa.append(MC_deck.pop())
        MC_vitorias_bot += MC_verifica_perdedor(MC_cartas_jogador, MC_mesa)
        

    print("\n\nVITORIAS BOT: ", MC_vitorias_bot, "\n\n")
    return (MC_vitorias_bot/ITERACOES_MONTE_CARLO)


def calcula_aposta(): #TODO como o bot calcula a aposta
    return 100

def formula_d(): # TODO formula
    mt = monte_carlo()*100
    log_mensagem(f"Chance do bot vencer de {mt:.2f}%")
    if BOT_RECONHER:
        probs = pegar_probabilidades_webcam_tempo(cap, duracao=3, pesos=PESOS_EMOCAO)
        maior_emocao = max(probs, key=probs.get)
    else:
        maior_emocao = "neutral"
    log_mensagem(f"Jogador está {maior_emocao}")
    
    return mt

def acao_bot(houve_aposta): # TODO acho que esta certo
    d = formula_d()
    if houve_aposta and d <= VALOR_MINIMO_D:
        return ("fold",0)
    elif houve_aposta and d > VALOR_MINIMO_D:
        return ("call",jogador.aposta)
    elif not houve_aposta and d > VALOR_MINIMO_D:
        return ("bet",calcula_aposta())
    elif not houve_aposta and d <= VALOR_MINIMO_D:
        return ("check",0)

def desenhar_interface():
    screen.fill((0, 100, 0))

    # Mesa
    pygame.draw.ellipse(screen, GREEN, table_rect)

    # Linhas de orientação (se grade ativada)
    if grade:
        pygame.draw.line(screen, BLACK, (0, HEIGHT // 4), (WIDTH, HEIGHT // 4), 1)
        pygame.draw.line(screen, BLACK, (0, HEIGHT // 2), (WIDTH, HEIGHT // 2), 1)
        pygame.draw.line(screen, BLACK, (0, HEIGHT // 2 + HEIGHT // 4), (WIDTH, HEIGHT // 2 + HEIGHT // 4), 1)
        pygame.draw.line(screen, BLACK, (WIDTH // 4, 0), (WIDTH // 4, HEIGHT), 1)
        pygame.draw.line(screen, BLACK, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 1)
        pygame.draw.line(screen, BLACK, (WIDTH // 2 + WIDTH // 4, 0), (WIDTH // 2 + WIDTH // 4, HEIGHT), 1)

    # Dealer
    pygame.draw.rect(screen, DEALER_COLOR, dealer_rect)
    draw_text("DEALER", WHITE, dealer_rect, screen)

    # Jogador
    pygame.draw.rect(screen, PLAYER_COLOR, player_rect)
    screen.blit(jarda, jarda_pos)
    draw_multiline_text(f"{int(jogador.fichas)}\nAposta: {jogador.aposta}", WHITE, player_chips_bet_rect, screen)

    # Botões
    fonte_botao = pygame.font.SysFont("Arial", 20)

    # Call / Check botão
    if alerta_aposta:
        cor1 = GREEN if (alerta_aposta and botao_call.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]) else BLUE
        pygame.draw.rect(screen, cor1, botao_call)
        texto1 = fonte_botao.render("call", True, WHITE)
        screen.blit(texto1, (botao_call.x + 50, botao_call.y + 15))
    else:
        cor1 = GREEN if (not alerta_aposta and botao_check.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]) else BLUE
        pygame.draw.rect(screen, cor1, botao_check)
        texto1 = fonte_botao.render("check", True, WHITE)
        screen.blit(texto1, (botao_check.x + 50, botao_check.y + 15))
    
    # Fold botão
    cor2 = GREEN if botao_fold.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] else BLUE
    pygame.draw.rect(screen, cor2, botao_fold)
    texto2 = fonte_botao.render("fold", True, WHITE)
    screen.blit(texto2, (botao_fold.x + 50, botao_fold.y + 15))

    # Bet botão
    cor3 = GREEN if botao_bet.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] else BLUE
    pygame.draw.rect(screen, cor3, botao_bet)
    texto3 = fonte_botao.render("bet", True, WHITE)
    screen.blit(texto3, (botao_bet.x + 50, botao_bet.y + 15))

    # caixa input que só aceita numero
    pygame.draw.rect(screen, cor_input, input_rect, border_radius=5)
    texto_input = fonte_botao.render(input_texto, True, BLACK)
    screen.blit(texto_input, (input_rect.x + 5, input_rect.y + 10))

    # Bot (IA)
    pygame.draw.rect(screen, BOT_COLOR, bot_rect)
    text = "Bot " + ("com" if BOT_RECONHER else "sem") + "\nreconhecimento\nfacial"
    draw_multiline_text(text, WHITE, bot_rect, screen)
    draw_multiline_text(f"{int(bot.fichas)}\nAposta: {bot.aposta}", WHITE, bot_chips_bet_rect, screen)

    # Baralho
    
    for i in range(8):
        screen.blit(baralho, (table_rect.centerx + 100 + i, dealer_rect.left - 200 - i))
    screen.blit(baralho, baralho_pos)


    # Pote
    draw_text("Pote: "+str(pote), WHITE, pote_rect, screen)
    screen.blit(fichas_mesa, fichas_mesa_pos)

    # Cartas do jogador e mesa
    if img_cartas_jogador:
        sempre_cartas_mao()
    if imgs_mesa:
        sempre_flop()

    # Log do jogo
    desenha_log()

def processar_eventos():
    global acao, valor, espera_jogador, alerta_aposta
    global input_ativo, input_texto, cor_input

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            cap.release()
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN and espera_jogador:
            if botao_check.collidepoint(event.pos) and not alerta_aposta:
                acao = "check"
                valor = 0
                espera_jogador = False
                input_texto = ""

            elif botao_call.collidepoint(event.pos) and alerta_aposta:
                acao = "call"
                valor = 0
                espera_jogador = False
                input_texto = ""

            elif botao_fold.collidepoint(event.pos):
                acao = "fold"
                valor = 0
                espera_jogador = False
                input_texto = ""

            elif botao_bet.collidepoint(event.pos):
                try:
                    valor = int(input_texto)
                    while valor < aposta_minima:
                        input_texto = f"Min {aposta_minima}"
                        valor = int(input_texto)
                    acao = "bet"
                    espera_jogador = False
                    input_texto = "" if aposta_minima == 0 else f"Min {aposta_minima}"
                except:
                    print("Valor inválido")

            # Clique na caixa de texto
            if input_rect.collidepoint(event.pos):
                input_ativo = True
                cor_input = cor_ativa
            else:
                input_ativo = False
                cor_input = cor_inativa

        elif event.type == pygame.KEYDOWN and input_ativo:
            if event.key == pygame.K_RETURN:
                try: 
                    valor = int(input_texto)
                    acao = "bet"
                    espera_jogador = False
                    input_texto = ""
                except:
                    print("Valor inválido")
            elif event.key == pygame.K_BACKSPACE:
                input_texto = input_texto[:-1]
            elif event.unicode.isdigit():
                input_texto += event.unicode



def acao_jogador():
    global espera_jogador, arrastando
    espera_jogador = True
    while espera_jogador:
        processar_eventos()
        desenhar_interface()
        pygame.display.flip()
        clock.tick(hertz)
    return acao, valor


alerta_aposta = False


def jogadas(jogador1, jogador2):
    global pote, pote_aux, e_pre_flop, aposta_minima,alerta_aposta, acao, valor
    if e_pre_flop:
        aposta_minima = BIG_BLIND - SMALL_BLIND
    # Determinar ordem dos jogadores com base no SB
    if jogador1.blind == SMALL_BLIND:
        ordem = [jogador1, jogador2]
    else:
        ordem = [jogador2, jogador1]

    rodada_finalizada = False
    
    while not rodada_finalizada:

        for jogador_vez in ordem:
            # Exibir estado (para debug ou exibição futura)
            print(f"\n{jogador_vez.nome} ({'BOT' if jogador_vez.e_bot else 'JOGADOR'})")
            print(f"Fichas: {jogador_vez.fichas}, Aposta atual: {jogador_vez.aposta}, Pote: {pote}")

            # Determinar ação
            if jogador1.aposta != jogador2.aposta:
                alerta_aposta = True

            # all-in pass
            if jogador_vez.fichas == 0:
                acao = "call"

            elif jogador_vez.e_bot:
                acao, valor = acao_bot(alerta_aposta)
            else:
                acao, valor = acao_jogador()

            
            # Tratar ação
            if acao == "fold":
                print(f"{jogador_vez.nome} desistiu.")
                log_mensagem(f"{jogador_vez.nome} desistiu.")
                pote += pote_aux
                pote_aux = 0
                perdedor = jogador_vez
                return jogador_vez # fim da rodada

            elif acao == "check":
                # Só pode dar check se as apostas forem iguais
                maior_aposta = max(jogador1.aposta, jogador2.aposta)
                if jogador_vez.aposta == maior_aposta:
                    print(f"{jogador_vez.nome} deu check.")
                    log_mensagem(f"{jogador_vez.nome} passou a vez. (check)")
            
            elif acao == "call":
                maior_aposta = max(jogador1.aposta, jogador2.aposta)
                diferenca = maior_aposta - jogador_vez.aposta
                if diferenca > jogador_vez.fichas:
                    diferenca = jogador_vez.fichas  # all-in
                jogador_vez.fichas -= diferenca
                jogador_vez.aposta += diferenca
                pote_aux += diferenca
                print(f"{jogador_vez.nome} pagou {diferenca}. (call)")
                log_mensagem(f"{jogador_vez.nome} pagou {diferenca}. (call)")
                if e_pre_flop:
                    e_pre_flop = False
                    alerta_aposta = False
                    aposta_minima = 0
                else:
                    rodada_finalizada = True
                    break

            elif acao == "bet":
                if valor > jogador_vez.fichas:
                    valor = jogador_vez.fichas  # all-in
                jogador_vez.fichas -= valor
                jogador_vez.aposta += valor
                pote_aux += valor
                print(f"{jogador_vez.nome} apostou {valor}. (bet)")
                log_mensagem(f"{jogador_vez.nome} apostou {valor}. (bet)")

        # Condição de parada da rodada: apostas iguais e ninguém apostou de novo
        if jogador1.aposta == jogador2.aposta:
            rodada_finalizada = True

    # Zera as apostas da rodada
    for jogador in [jogador1, jogador2]:
        alerta_aposta = False
        jogador.aposta = 0
    log_mensagem("")
    log_mensagem("")
    
    # Ao fim da rodada, atualiza o pote
    pote += pote_aux
    pote_aux = 0


def desenha_log():
    largura = 400
    altura = font.get_height() * MAX_MENSAGENS + 20
    x = 20
    y = 20
    fundo_log = pygame.Rect(x, y, largura, altura)
    pygame.draw.rect(screen, (200,242,136), fundo_log)
    pygame.draw.rect(screen, BLACK, fundo_log, 2)

    for i, msg in enumerate(mensagens_log):
        linha = font.render(msg, True, BLACK)
        screen.blit(linha, (x + 10, y + 10 + i * font.get_height()))

# movimento das cartas do player
carta_posicoes_player = [pygame.Vector2(baralho_pos) for _ in range(2)]
cartas_player_alvos = [
    pygame.Vector2(
        player_rect.midbottom[0] + DISTANCIA_MESA_D_USUARIO - i*(114+DISTANCIA_MESA_D_USUARIO),
        bot_rect.bottom + DISTANCIA_MESA_D_USUARIO
    )
    for i in range(2)
]

# variaveis da animação, não mexer
cartas_bot_movendo = [True, True] 
cartas_player_movendo = [True, True]

# função de animaçao de dar as cartas com as cartas do bot fechada 
def ani_cartas_bot_fechado():
    # Bot
    for i in range(2):
        if cartas_bot_movendo[i]:
            direcao = cartas_bot_alvos[i] - carta_posicoes_bot[i]
            if direcao.length() < 1:
                cartas_bot_movendo[i] = False
                carta_posicoes_bot[i] = cartas_bot_alvos[i]
            else:
                direcao = direcao.normalize()
                carta_posicoes_bot[i] += direcao * velocidade * delta_time
        screen.blit(baralho, carta_posicoes_bot[i].xy)

    # Jogador
    for i in range(2):
        if cartas_player_movendo[i]:
            direcao = cartas_player_alvos[i] - carta_posicoes_player[i]
            if direcao.length() < 1:
                cartas_player_movendo[i] = False
                carta_posicoes_player[i] = cartas_player_alvos[i]
            else:
                direcao = direcao.normalize()
                carta_posicoes_player[i] += direcao * velocidade * delta_time
        screen.blit(img_cartas_jogador[i], carta_posicoes_player[i].xy)

carta_posicoes_mesa = [pygame.Vector2(baralho_pos) for i in range(5)]
cartas_mesa_alvos = [pygame.Vector2(table_rect.centerx - 2 * DISTANCIA_MESA_D_USUARIO - 114 * 2.5 + i * (114 +DISTANCIA_MESA_D_USUARIO), table_rect.centery - DISTANCIA_MESA_D_USUARIO - 163)for i in range(5)]
cartas_mesa_movendo = [True,True,True,True,True]

# função de dar as cartas 
def ani_cartas_mesa_flop():
    for i in range(5):
        if cartas_mesa_movendo[i]:
            direcao = cartas_mesa_alvos[i] - carta_posicoes_mesa[i]
            if direcao.length() < 1:
                cartas_mesa_movendo[i] = False
                carta_posicoes_mesa[i] = cartas_mesa_alvos[i]
            else:
                direcao = direcao.normalize()
                carta_posicoes_mesa[i] += direcao * velocidade * delta_time
        screen.blit(baralho, carta_posicoes_mesa[i].xy)

# precisa disso porque animação != ficar aparecendo
def sempre_cartas_mao():
    for i in range(2):
        screen.blit(img_cartas_jogador[i], carta_posicoes_player[i].xy)
        screen.blit(img_cartas_bot[i], carta_posicoes_bot[i].xy)

def sempre_flop():
    for i in range(5):
        screen.blit(imgs_mesa[i], carta_posicoes_mesa[i].xy)

def sempre_turn():
    screen.blit(imgs_mesa[3], carta_posicoes_mesa[3].xy)

def sempre_river():
    screen.blit(imgs_mesa[4], carta_posicoes_mesa[4].xy)

perdedor = None 

while running:
    processar_eventos()

    mouse_pos = pygame.mouse.get_pos()
    mouse_pressionado = pygame.mouse.get_pressed()[0]

    # distribui as cartas e o pote
    if fase == "inicio":
        if jogador.fichas == 0 or bot.fichas == 0: # TODO indica que houve allin e precisa de tela de vitoria avassaladora de alguem 
            log_mensagem("")
            log_mensagem("")
            log_mensagem("")
            log_mensagem("")
            log_mensagem("")
            restart()
        pre_flop()
        fase = "pre_flop_ani"

    # serve pra esperar a animação
    elif fase == "pre_flop_ani":
        ani_cartas_bot_fechado()
        if all(not movendo for movendo in cartas_bot_movendo + cartas_player_movendo):
            fase = "pre_flop"

    elif fase == "pre_flop":
        bundao = jogadas(jogador,bot)
        if bundao != None:
            fim_rodada(bundao)
            fase = "inicio"
        else:
            flop()
            fase = "flop_ani" 

    # serve pra esperar a animação
    elif fase == "flop_ani":
        ani_cartas_mesa_flop()
        if all(not movendo for movendo in cartas_mesa_movendo):
            fase = "flop"

    elif fase == "flop":
        bundao = jogadas(jogador,bot)
        if bundao != None:
            fim_rodada(bundao)
            fase = "inicio"
        else:
            turn()
            fase = "turn" 
        

    elif fase == "turn":
        bundao = jogadas(jogador,bot)
        if bundao != None:
            fim_rodada(bundao)
            fase = "inicio"
        else:
            river()
            fase = "river"
        

    elif fase == "river":
        bundao = jogadas(jogador,bot)
        fim_rodada(bundao)
        fase = "inicio"

    if img_cartas_jogador:
        sempre_cartas_mao()
    
    if imgs_mesa:
        sempre_flop()

    desenhar_interface()

    # Eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Atualizar tela
    pygame.display.flip()
    delta_time = clock.tick(hertz) / 1000
pygame.quit()
sys.exit()
