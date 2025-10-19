import pandas as pd
import re
import io

def parse_log_by_play(log_data):
    """
    Processa o log do jogo linha por linha, criando uma entrada para cada
    ação ou evento (ação do jogador/bot, cartas da mesa).
    
    Esta versão corrige o bug de leitura das linhas de análise.
    """
    
    all_plays_data = []

    # --- Variáveis de "Estado" ---
    current_hand_id = 0
    play_id_in_hand = 0
    current_player_cards = None
    current_bot_cards = None
    current_board = None
    current_street = None
    
    vencedor_da_mao = None
    jogador_mao_final = None
    bot_mao_final = None
    
    # --- (CORREÇÃO) Buffer para linhas de análise ---
    # Armazena temporariamente as métricas até encontrarmos a terceira
    temp_mc = None
    temp_analise = None
    # ------------------------------------------------

    # --- Expressões Regulares (Regex) ---
    player_start_pattern = re.compile(r"\( (\d+\.\d+) \) jogador: (\[.*?\])")
    bot_start_pattern = re.compile(r"\( (\d+\.\d+) \) bot: (\[.*?\])")
    board_pattern = re.compile(r"mesa: (\[.*?\])")
    action_pattern = re.compile(r"^(Voce|Bot) (.*?)\.?(\s*\(.+?\))?$")
    
    analysis_mc_pattern = re.compile(r"Chance do MC: (\d+\.\d+)%")
    analysis_jogo_pattern = re.compile(r"Anßlise do jogo: (-?\d+\.\d+)")
    analysis_valor_pattern = re.compile(r"Valor final de D Ú (-?\d+\.\d+)")
    
    hand_type_pattern = re.compile(r"^(jogador|bot) (.*?) com")
    perdedor_pattern = re.compile(r"perdedor (Voce|Bot)")
    empate_pattern = re.compile(r"EMPATE")
    
    lines = log_data.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 1. Detectar início de uma nova mão
        player_match = player_start_pattern.search(line)
        if player_match:
            current_hand_id += 1
            play_id_in_hand = 0
            current_player_cards = player_match.group(2)
            # Reseta o estado da mão
            current_bot_cards = None
            current_board = None
            current_street = 'Preflop'
            vencedor_da_mao = None
            jogador_mao_final = None
            bot_mao_final = None
            temp_mc = None # Reseta buffers
            temp_analise = None
            continue 

        # 2. Capturar cartas do Bot
        bot_match = bot_start_pattern.search(line)
        if bot_match:
            current_bot_cards = bot_match.group(2)
            continue

        # 3. Detectar Evento: Cartas da Mesa
        board_match = board_pattern.search(line)
        if board_match:
            play_id_in_hand += 1
            current_board = board_match.group(1)
            num_cards = current_board.count(',') + 1
            
            action_text = 'DEALT_UNKNOWN'
            if num_cards == 3:
                current_street = 'Flop'
                action_text = 'DEALT_FLOP'
            elif num_cards == 4:
                current_street = 'Turn'
                action_text = 'DEALT_TURN'
            elif num_cards == 5:
                current_street = 'River'
                action_text = 'DEALT_RIVER'
            
            temp_mc = None # Reseta buffers
            temp_analise = None

            play_row = {
                'Hand_ID': current_hand_id,
                'Play_ID_in_Hand': play_id_in_hand,
                'Street': current_street,
                'Actor': 'Mesa',
                'Action': action_text,
                'Jogador_Cartas': current_player_cards,
                'Bot_Cartas': current_bot_cards,
                'Board_Cards': current_board,
            }
            all_plays_data.append(play_row)
            continue 

        # 4. Detectar Evento: Ação do Jogador ou Bot
        action_match = action_pattern.search(line)
        if action_match:
            play_id_in_hand += 1
            actor = action_match.group(1).replace('Voce', 'Jogador')
            action_text = action_match.group(2).strip()
            action_detail = action_match.group(3).strip() if action_match.group(3) else ''
            full_action = f"{action_text} {action_detail}".strip()
            
            temp_mc = None # Reseta buffers
            temp_analise = None

            play_row = {
                'Hand_ID': current_hand_id,
                'Play_ID_in_Hand': play_id_in_hand,
                'Street': current_street,
                'Actor': actor,
                'Action': full_action,
                'Jogador_Cartas': current_player_cards,
                'Bot_Cartas': current_bot_cards,
                'Board_Cards': current_board,
            }
            all_plays_data.append(play_row)
            continue

        # 5. (CORREÇÃO) Detectar linhas de Análise
        mc_match = analysis_mc_pattern.search(line)
        if mc_match:
            temp_mc = mc_match.group(1)
            continue

        jogo_match = analysis_jogo_pattern.search(line)
        if jogo_match:
            temp_analise = jogo_match.group(1)
            continue

        # Se encontrarmos a 3ª linha (Valor final) E tivermos as outras 2 no buffer
        # E houver uma jogada anterior para anexar...
        valor_match = analysis_valor_pattern.search(line)
        if valor_match and all_plays_data and temp_mc is not None and temp_analise is not None:
            try:
                # Anexa as métricas à *última* jogada/evento registrado
                all_plays_data[-1]['Chance_MC'] = float(temp_mc)
                all_plays_data[-1]['Analise_Jogo'] = float(temp_analise)
                all_plays_data[-1]['Valor_Final_D_U'] = float(valor_match.group(1))
            except Exception as e:
                print(f"Erro ao converter análise: {e} | {temp_mc}, {temp_analise}, {valor_match.group(1)}")
            
            # Reseta os buffers
            temp_mc = None
            temp_analise = None
            continue
            
        # 6. Detectar tipo da mão final
        hand_type_match = hand_type_pattern.search(line)
        if hand_type_match:
            who = hand_type_match.group(1)
            hand_name = hand_type_match.group(2).strip()
            if who == 'jogador':
                jogador_mao_final = hand_name
            elif who == 'bot':
                bot_mao_final = hand_name
            continue

        # 7. Detectar Resultado da Mão (Perdedor ou Empate)
        perdedor_match = perdedor_pattern.search(line)
        empate_match = empate_pattern.search(line)
        
        if perdedor_match or empate_match:
            if empate_match:
                vencedor_da_mao = 'Empate'
            elif perdedor_match.group(1) == 'Voce':
                vencedor_da_mao = 'Bot'
            elif perdedor_match.group(1) == 'Bot':
                vencedor_da_mao = 'Jogador'

            # Preenche o resultado em todas as linhas dessa mão
            for i in range(len(all_plays_data) - 1, -1, -1):
                if all_plays_data[i]['Hand_ID'] == current_hand_id:
                    all_plays_data[i]['Vencedor_da_Mao'] = vencedor_da_mao
                    all_plays_data[i]['Jogador_Mao_Final'] = jogador_mao_final
                    all_plays_data[i]['Bot_Mao_Final'] = bot_mao_final
                else:
                    break
            continue

    # --- Fim do Loop ---
    
    # 8. Criar o DataFrame
    df = pd.DataFrame(all_plays_data)
    
    # 9. Definir a ordem final das colunas
    columns_order = [
        'Hand_ID',
        'Play_ID_in_Hand',
        'Street',
        'Actor',
        'Action',
        'Jogador_Cartas',
        'Bot_Cartas',
        'Board_Cards',
        'Chance_MC',
        'Analise_Jogo',
        'Valor_Final_D_U',
        'Jogador_Mao_Final',
        'Bot_Mao_Final',
        'Vencedor_da_Mao'
    ]
    
    # Adiciona colunas que possam estar faltando (inicializando com None)
    for col in columns_order:
        if col not in df.columns:
            df[col] = None
            
    df = df[columns_order]
    
    return df

# --- Execução Principal ---
try:
    # (CORREÇÃO 1) Ler o arquivo 'saida_sem.txt'
    input_filename = 'saida_sem.txt' 
    with open(input_filename, 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    # Limpar os marcadores de fonte do texto para o parser
    cleaned_log = re.sub(r"\\s*", "", log_content)

    df_por_jogada = parse_log_by_play(cleaned_log)
    
    # Novos nomes de arquivo para a v2
    csv_filename = 'analise_poker_por_jogada_sem.csv'
    excel_filename = 'analise_poker_por_jogada_sem.xlsx'
    
    df_por_jogada.to_csv(csv_filename, index=False, sep=';', decimal=',')
    df_por_jogada.to_excel(excel_filename, index=False, engine='openpyxl')

    print(f"Script executado com sucesso.")
    print(f"Arquivos gerados: '{csv_filename}' e '{excel_filename}'")
    
    print("\n(CORREÇÃO 2) Amostra das primeiras 10 linhas (Hand_ID 1):")
    print(df_por_jogada.head(10).to_markdown(index=False, numalign="left", stralign="left"))
    
    print("\nAmostra da Hand_ID 5 (showdown) para verificar 'Jogador_Mao_Final':")
    # Filtra por uma mão que foi ao showdown (Hand 5)
    showdown_sample = df_por_jogada[df_por_jogada['Hand_ID'] == 5]
    print(showdown_sample.tail(5).to_markdown(index=False, numalign="left", stralign="left"))

except FileNotFoundError:
    print(f"ERRO: O arquivo '{input_filename}' não foi encontrado.")
except Exception as e:
    print(f"Ocorreu um erro ao processar o log: {e}")