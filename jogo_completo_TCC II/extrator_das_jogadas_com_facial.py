import pandas as pd
import re
import io

def parse_log_by_play_v5(log_data):
    """
    Processa o log do jogo linha por linha (V5).
    
    CORRIGE os padrões de regex para 'Análise' e 'Valor final'
    para funcionar com o novo formato de log ('An├ílise' e 'D ├®').
    """
    
    all_plays_data = []

    # --- Variáveis de "Estado" ---
    current_hand_id = 0
    play_id_in_hand = 0
    current_player_cards = None
    current_bot_cards = None
    current_board = None
    current_street = None
    
    # --- Buffers de Análise e Resultado ---
    temp_emocao_nome, temp_emocao_pct, temp_emocao_impacto = None, None, None
    temp_mc, temp_analise, temp_valor = None, None, None
    vencedor_da_mao, jogador_mao_final, bot_mao_final = None, None, None

    # --- Expressões Regulares (Regex) ---
    player_start_pattern = re.compile(r"\( (\d+\.\d+) \) jogador: (\[.*?\])")
    bot_start_pattern = re.compile(r"\( (\d+\.\d+) \) bot: (\[.*?\])")
    board_pattern = re.compile(r"mesa: (\[.*?\])")
    action_pattern = re.compile(r"^(Voce|Bot) (.*?)\.?(\s*\(.+?\))?$")
    
    emotion_pattern = re.compile(r"L\(f\): (.*?) - ([\d\.]+)% \(Impacto: (-?[\d\.]+)\)")
    
    # --- (CORREÇÃO 2) Regex de Análise (mais flexível) ---
    # Captura 'Anßlise', 'An├ílise', etc.
    analysis_jogo_pattern = re.compile(r"An.*?lise do jogo: (-?[\d\.]+)")
    
    analysis_mc_pattern = re.compile(r"Chance do MC: (\d+\.\d+)%")
    
    # --- (CORREÇÃO 3) Regex do Valor Final (mais flexível) ---
    # Captura 'D Ú', 'D -', 'D ├®', etc.
    analysis_valor_pattern = re.compile(r"Valor final de D .*?(-?[\d\.]+)$")
    
    hand_type_pattern = re.compile(r"^(jogador|bot) (.*?) com")
    perdedor_pattern = re.compile(r"perdedor (Voce|Bot)")
    empate_pattern = re.compile(r"EMPATE")
    
    lines = log_data.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # --- Lógica de atribuição de Análise Pendente ---
        is_analysis_line = (emotion_pattern.search(line) or 
                            analysis_mc_pattern.search(line) or 
                            analysis_jogo_pattern.search(line) or 
                            analysis_valor_pattern.search(line))

        if temp_valor is not None and not is_analysis_line:
            if all_plays_data: 
                all_plays_data[-1]['Emocao_Detectada'] = temp_emocao_nome
                all_plays_data[-1]['Emocao_Porcentagem'] = temp_emocao_pct
                all_plays_data[-1]['Emocao_Impacto'] = temp_emocao_impacto
                all_plays_data[-1]['Chance_MC'] = temp_mc
                all_plays_data[-1]['Analise_Jogo'] = temp_analise
                all_plays_data[-1]['Valor_Final_D_U'] = temp_valor
            
            temp_emocao_nome, temp_emocao_pct, temp_emocao_impacto = None, None, None
            temp_mc, temp_analise, temp_valor = None, None, None

        # --- Lógica de atribuição de Resultado Pendente ---
        if vencedor_da_mao is not None and player_start_pattern.search(line):
            for i in range(len(all_plays_data) - 1, -1, -1):
                if all_plays_data[i]['Hand_ID'] == current_hand_id:
                    all_plays_data[i]['Vencedor_da_Mao'] = vencedor_da_mao
                    all_plays_data[i]['Jogador_Mao_Final'] = jogador_mao_final
                    all_plays_data[i]['Bot_Mao_Final'] = bot_mao_final
                else:
                    break 
            vencedor_da_mao, jogador_mao_final, bot_mao_final = None, None, None

        # 1. Detectar início de uma nova mão
        player_match = player_start_pattern.search(line)
        if player_match:
            current_hand_id += 1
            play_id_in_hand = 0
            current_player_cards = player_match.group(2)
            current_bot_cards, current_board, current_street = None, None, 'Preflop'
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
            if num_cards == 3: current_street, action_text = 'Flop', 'DEALT_FLOP'
            elif num_cards == 4: current_street, action_text = 'Turn', 'DEALT_TURN'
            elif num_cards == 5: current_street, action_text = 'River', 'DEALT_RIVER'
            else: action_text = 'DEALT_UNKNOWN'

            play_row = {'Hand_ID': current_hand_id, 'Play_ID_in_Hand': play_id_in_hand,
                        'Street': current_street, 'Actor': 'Mesa', 'Action': action_text,
                        'Jogador_Cartas': current_player_cards, 'Bot_Cartas': current_bot_cards,
                        'Board_Cards': current_board }
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

            play_row = {'Hand_ID': current_hand_id, 'Play_ID_in_Hand': play_id_in_hand,
                        'Street': current_street, 'Actor': actor, 'Action': full_action,
                        'Jogador_Cartas': current_player_cards, 'Bot_Cartas': current_bot_cards,
                        'Board_Cards': current_board }
            all_plays_data.append(play_row)
            continue

        # 5. Detectar linhas de Emoção e Análise (armazena em buffer)
        emotion_match = emotion_pattern.search(line)
        if emotion_match:
            temp_emocao_nome = emotion_match.group(1).strip()
            temp_emocao_pct = float(emotion_match.group(2))
            temp_emocao_impacto = float(emotion_match.group(3))
            continue
            
        mc_match = analysis_mc_pattern.search(line)
        if mc_match:
            temp_mc = float(mc_match.group(1))
            continue

        jogo_match = analysis_jogo_pattern.search(line)
        if jogo_match:
            temp_analise = float(jogo_match.group(1))
            continue

        valor_match = analysis_valor_pattern.search(line)
        if valor_match:
            temp_valor = float(valor_match.group(1))
            continue
            
        # 6. Detectar tipo da mão final (armazena em buffer)
        hand_type_match = hand_type_pattern.search(line)
        if hand_type_match:
            who, hand_name = hand_type_match.group(1), hand_type_match.group(2).strip()
            if who == 'jogador': jogador_mao_final = hand_name
            elif who == 'bot': bot_mao_final = hand_name
            continue

        # 7. Detectar Resultado da Mão (armazena em buffer)
        perdedor_match = perdedor_pattern.search(line)
        if perdedor_match:
            if perdedor_match.group(1) == 'Voce': vencedor_da_mao = 'Bot'
            elif perdedor_match.group(1) == 'Bot': vencedor_da_mao = 'Jogador'
            continue
            
        if empate_pattern.search(line):
            vencedor_da_mao = 'Empate'
            continue

    # --- Fim do Loop ---
    
    # --- Aplicação Final (para a última mão/ação do log) ---
    if temp_valor is not None and all_plays_data:
        all_plays_data[-1]['Emocao_Detectada'] = temp_emocao_nome
        all_plays_data[-1]['Emocao_Porcentagem'] = temp_emocao_pct
        all_plays_data[-1]['Emocao_Impacto'] = temp_emocao_impacto
        all_plays_data[-1]['Chance_MC'] = temp_mc
        all_plays_data[-1]['Analise_Jogo'] = temp_analise
        all_plays_data[-1]['Valor_Final_D_U'] = temp_valor

    if vencedor_da_mao is not None:
        for i in range(len(all_plays_data) - 1, -1, -1):
            if all_plays_data[i]['Hand_ID'] == current_hand_id:
                all_plays_data[i]['Vencedor_da_Mao'] = vencedor_da_mao
                all_plays_data[i]['Jogador_Mao_Final'] = jogador_mao_final
                all_plays_data[i]['Bot_Mao_Final'] = bot_mao_final
            else:
                break
    
    df = pd.DataFrame(all_plays_data)
    
    columns_order = [
        'Hand_ID', 'Play_ID_in_Hand', 'Street', 'Actor', 'Action',
        'Jogador_Cartas', 'Bot_Cartas', 'Board_Cards',
        'Emocao_Detectada', 'Emocao_Porcentagem', 'Emocao_Impacto', 
        'Chance_MC', 'Analise_Jogo', 'Valor_Final_D_U',
        'Jogador_Mao_Final', 'Bot_Mao_Final', 'Vencedor_da_Mao'
    ]
    
    for col in columns_order:
        if col not in df.columns:
            df[col] = None
    df = df[columns_order]
    
    df.fillna(value=pd.NA, inplace=True)
    
    return df

# --- Execução Principal (Corrigida) ---
try:
    # O nome do arquivo que você especificou no seu código
    input_filename = 'joao_com.txt' 
    with open(input_filename, 'r', encoding='utf-8') as f:
        log_content = f.read()
    
    # (CORREÇÃO 1) Removida a linha 'cleaned_log' que quebrava o script.
    # Usamos o 'log_content' diretamente.

    df_por_jogada = parse_log_by_play_v5(log_content)
    
    # Novos nomes de arquivo
    csv_filename = 'analise_joao_com.csv'
    excel_filename = 'analise_joao_com.xlsx'
    
    # df_por_jogada.to_csv(csv_filename, index=False, sep=';', decimal=',')
    df_por_jogada.to_excel(excel_filename, index=False, engine='openpyxl')

    print(f"Script V5 (com Emoção) executado com sucesso.")
    print(f"Arquivos gerados: '{csv_filename}' e '{excel_filename}'")
    
    print("\nAmostra das primeiras 10 linhas (V5 - dados de emoção devem aparecer):")
    print(df_por_jogada.head(10).to_markdown(index=False, numalign="left", stralign="left"))

except FileNotFoundError:
    print(f"ERRO: O arquivo '{input_filename}' não foi encontrado.")
    print("Por favor, certifique-se de que o seu novo log (com emoções) está salvo como 'saida_com.txt' no mesmo diretório do script.")
except Exception as e:
    print(f"Ocorreu um erro ao processar o log (V5): {e}")