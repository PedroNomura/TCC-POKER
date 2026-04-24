# Decisão Estratégica no Pôquer com IA baseada em Expressões Faciais, Simulações de Monte Carlo e análise do jogo


Este projeto apresenta o desenvolvimento de uma Inteligência Artificial aplicada ao jogo de pôquer Texas Hold'em, focado na tomada de decisões em cenários de incerteza. O sistema integra cálculos probabilísticos avançados com algoritmos de visão computacional em tempo real, investigando o impacto da leitura do estado emocional do oponente na performance estratégica da IA.

O projeto foi desenvolvido como Trabalho de Conclusão de Curso (TCC) e demonstra a viabilidade de integrar percepção psicológica a motores de decisão matemáticos para criar um agente autônomo mais robusto.

## Arquitetura e Metodologia

O diferencial técnico do projeto reside na construção de um motor de decisão híbrido e modular, que processa duas fontes de dados distintas para determinar a ação do agente (bot):

### 1. Camada de Análise Probabilística (Monte Carlo)
A IA utiliza o algoritmo de Monte Carlo Clássico para estimar as chances de vitória com base nas cartas disponíveis (cartas do bot e cartas abertas na mesa). A cada tomada de decisão, o sistema realiza milhares de simulações aleatórias dos desfechos possíveis, calculando uma taxa de vitória estatística. Esta abordagem foi escolhida por sua eficiência em jogos com informações parciais e menor exigência computacional em comparação com árvores de decisão complexas.

### 2. Camada de Percepção Psicológica (Transfer Learning e DeepFace)
Para interpretar o estado emocional do oponente, o sistema emprega a biblioteca DeepFace, utilizando técnicas de Transfer Learning com modelos de redes neurais convolucionais (CNNs) pré-treinados. O pipeline de reconhecimento facial processa o feed da webcam em tempo real, executando:
* Detecção e alinhamento facial.
* Extração de características e classificação em 7 emoções básicas (Felicidade, Tristeza, Raiva, Medo, Aversão, Surpresa e Neutro).
* Aplicação de heurísticas baseadas no Modelo Circunplexo de Afeto de Russell (1980) para traduzir a emoção dominante em um modificador de valência (positiva ou negativa) que impacta a confiança do bot.

### 3. Motor de Decisão Consolidado
As variáveis probabilísticas e emocionais são integradas em uma fórmula de decisão, juntamente com fatores situacionais do jogo:

D = Pmc + L(f) + F(x)

Onde:
* Pmc: Probabilidade de vitória (Monte Carlo).
* L(f): Impacto numérico da Leitura Facial.
* F(x): Fatores situacionais (relação de fichas, risco financeiro e agressividade do oponente).

Os limites de decisão resultantes desta equação determinam se o bot fará Call, Fold, Bet ou Check.

## Resultados e Validação

O sistema foi submetido a um rigoroso processo de testes empíricos através de 120 partidas simuladas (60 com o módulo de reconhecimento facial ativo e 60 com o módulo inativo).

A análise comparativa de desempenho demonstrada no artigo validou a hipótese central: a integração do reconhecimento facial foi o fator determinante para a lucratividade da IA. Nos testes de controle (leitura facial desativada), a IA obteve uma taxa de vitória de 45% e encerrou a simulação com saldo negativo de fichas (prejuízo). Quando o módulo de reconhecimento emocional foi ativado, a taxa de vitória subiu para 50%, e a IA reverteu completamente o cenário, terminando com lucro contra os mesmos oponentes.

A análise qualitativa das decisões-chave comprovou que a variável L(f) permitiu à IA:
* Evitar perdas substanciais: Revertendo decisões de "Call" simuladas por Monte Carlo para "Fold" ao detectar expressões de felicidade ou surpresa no oponente (indicando mãos fortes reais).
* Capturar blefes: Revertendo decisões conservadoras para "Call" ou "Bet" agressivo ao detectar emoções de baixa confiança, como medo.

## Stack Tecnológica

* Linguagem: Python 3.10
* Visão Computacional e IA: DeepFace (Transfer Learning / CNNs), OpenCV
* Interface e Controle de Jogo: Pygame, PokerLib
* Processamento Numérico: NumPy, Math, Random

## Autores e Instituição

Desenvolvido por:
* João Pedro de Souza Costa Ferreira
* Pedro Nomura Picchioni
* Victor Vaglieri de Oliveira

Orientador: Alcides Teixeira Barboza Junior

Faculdade de Computação e Informática (FCI)
Universidade Presbiteriana Mackenzie – São Paulo, SP – Brasil
