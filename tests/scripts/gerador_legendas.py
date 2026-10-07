import os
from datetime import timedelta

# Frases complexas, cobrindo gírias, pontuação, jargão técnico e perguntas.
base_sentences = {
    "Frances": [
        "L'intelligence artificielle transforme notre façon d'interagir avec le monde numérique.",
        "C'est ouf! Je n'arrive pas à y croire, franchement.",
        "Avez-vous déjà pensé à l'impact des algorithmes sur la société moderne?",
        "Le système a signalé une erreur fatale dans le module de mémoire centrale.",
        "On se capte demain aprem' pour en discuter autour d'un café, d'accord?",
        "La physique quantique défie notre compréhension intuitive de la réalité.",
        "Quoi qu'il en soit, il faut qu'on trouve une solution pérenne avant la deadline.",
        "Il pleut des cordes, je crois que je vais annuler mon vol pour Paris."
    ],
    "Alemao": [
        "Künstliche Intelligenz verändert die Art und Weise, wie wir mit der digitalen Welt interagieren.",
        "Das ist krass! Ich kann es ehrlich gesagt nicht glauben.",
        "Haben Sie schon einmal über die Auswirkungen von Algorithmen auf die moderne Gesellschaft nachgedacht?",
        "Das System hat einen fatalen Fehler im Hauptspeichermodul gemeldet.",
        "Wir treffen uns morgen Nachmittag auf einen Kaffee, um das zu besprechen, okay?",
        "Die Quantenphysik widersetzt sich unserem intuitiven Verständnis der Realität.",
        "Wie dem auch sei, wir müssen vor der Deadline eine dauerhafte Lösung finden.",
        "Es schüttet wie aus Eimern, ich glaube, ich storniere meinen Flug nach Paris."
    ],
    "Russo": [
        "Искусственный интеллект меняет то, как мы взаимодействуем с цифровым миром.",
        "Это жесть! Честно говоря, поверить не могу.",
        "Вы когда-нибудь задумывались о влиянии алгоритмов на современное общество?",
        "Система сообщила о критической ошибке в модуле основной памяти.",
        "Пересечемся завтра после обеда за кофе и обсудим, договорились?",
        "Квантовая физика бросает вызов нашему интуитивному пониманию реальности.",
        "Как бы то ни было, нам нужно найти долгосрочное решение до дедлайна.",
        "Льет как из ведра, думаю, я отменю свой рейс в Париж."
    ],
    "Japones": [
        "人工知能は私たちがデジタル世界と対話する方法を変革しています。",
        "マジでヤバい！正直信じられないよ。",
        "アルゴリズムが現代社会に与える影響について考えたことはありますか？",
        "システムはメインメモリモジュールで致命的なエラーを報告しました。",
        "明日の午後、コーヒーでも飲みながら話し合おう、いい？",
        "量子物理学は、私たちの現実に対する直感的な理解に挑戦しています。",
        "とにかく、締め切りまでに永続的な解決策を見つけなければなりません。",
        "土砂降りだから、パリへのフライトはキャンセルすると思う。"
    ],
    "Chines": [
        "人工智能正在改变我们与数字世界互动的方式。",
        "太疯狂了！老实说，我简直不敢相信。",
        "您是否想过算法对现代社会的影响？",
        "系统报告主内存模块出现致命错误。",
        "我们明天下午喝杯咖啡聊聊这个，好吗？",
        "量子物理学挑战了我们对现实的直觉理解。",
        "无论如何，我们必须在截止日期前找到一个长期的解决方案。",
        "倾盆大雨，我想我要取消去巴黎的航班了。"
    ],
    "Coreano": [
        "인공 지능은 우리가 디지털 세계와 상호 작용하는 방식을 변화시키고 있습니다.",
        "대박! 솔직히 믿을 수가 없네요.",
        "알고리즘이 현대 사회에 미치는 영향에 대해 생각해 본 적이 있습니까?",
        "시스템이 주 메모리 모듈에서 치명적인 오류를 보고했습니다.",
        "내일 오후에 커피 마시면서 얘기 좀 할까, 어때?",
        "양자 물리학은 현실에 대한 우리의 직관적인 이해에 도전합니다.",
        "어쨌든 마감일 전에 영구적인 해결책을 찾아야 합니다.",
        "비가 억수같이 쏟아져서 파리행 비행기를 취소해야 할 것 같아요."
    ],
    "Ingles": [
        "Artificial intelligence is transforming the way we interact with the digital world.",
        "That's wild! I honestly can't believe it.",
        "Have you ever thought about the impact of algorithms on modern society?",
        "The system reported a fatal error in the core memory module.",
        "Let's catch up tomorrow afternoon over coffee to discuss it, alright?",
        "Quantum physics defies our intuitive understanding of reality.",
        "Anyway, we need to find a sustainable solution before the deadline.",
        "It's raining cats and dogs, I think I'll cancel my flight to Paris."
    ],
    "Portugues": [
        "A inteligência artificial está transformando a forma como interagimos com o mundo digital.",
        "Que loucura! Sinceramente, mal consigo acreditar.",
        "Você já parou para pensar no impacto dos algoritmos na sociedade moderna?",
        "O sistema reportou um erro fatal no módulo de memória central.",
        "Vamos nos bater amanhã de tarde para tomar um café e discutir isso, beleza?",
        "A física quântica desafia nossa compreensão intuitiva da realidade.",
        "De qualquer forma, precisamos encontrar uma solução definitiva antes do prazo.",
        "Tá chovendo canivete, acho que vou cancelar meu voo para Paris."
    ]
}

def format_timestamp(seconds):
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def generate_srt(idioma, sentences, output_dir):
    filepath = os.path.join(output_dir, f"complex_{idioma}.srt")
    
    # 30 minutos = 1800 segundos.
    # Vamos gerar falas de 3 segundos com 1 segundo de intervalo.
    # Cada ciclo (fala + intervalo) = 4 segundos.
    # 1800 / 4 = 450 linhas.
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for i in range(450):
            start_sec = i * 4.0
            end_sec = start_sec + 3.0
            
            start_ts = format_timestamp(start_sec)
            end_ts = format_timestamp(end_sec)
            
            sentence = sentences[i % len(sentences)]
            
            f.write(f"{i + 1}\n")
            f.write(f"{start_ts} --> {end_ts}\n")
            f.write(f"{sentence} (Linha {i+1})\n\n")
            
    print(f"Gerado: {filepath} (450 falas, ~30 minutos)")

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "legendas")
    os.makedirs(output_dir, exist_ok=True)
    print("Gerando arquivos SRT massivos de 30 minutos...")
    for idioma, frases in base_sentences.items():
        generate_srt(idioma, frases, output_dir)
    print("Concluído!")
