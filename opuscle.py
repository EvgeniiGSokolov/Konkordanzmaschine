print("(C) Евгений Геннадьевич Соколов, ИЛИ РАН, СПб, 2022 г.")

import re, sqlite3, docx, tkinter, tkinter.messagebox, os, pymystem3
import tkinter.filedialog as fd
from nltk import sent_tokenize as st, word_tokenize as wt
from PySimpleGUI import one_line_progress_meter as progress

morph = pymystem3.Mystem()


def show_prog(fragment, title):
    span = int(len(fragment)/50)+1
    elts = [elt for elt in range(0,len(fragment), span)]
    elts.append(len(fragment))
    [progress(f'{title}', n, len(fragment), f'ЭЛЕМЕНТ {n}') for n in elts]
    
def get_all_files():
    directory = fd.askdirectory()
    files = tuple(rf'{os.path.join(dirpath, filename)}'\
             for dirpath, dirnames, filenames in os.walk(rf'{directory}')\
             for filename in filenames)
    show_prog(files, 'Обработка')
    return files

def get_several_files():
    file_names = fd.askopenfilenames()
    show_prog(file_names, 'Добавляется файл')
    return file_names
    
def text_extractor(file):
    if file.endswith('.txt'):
        text = open(rf'{file}', 'r', encoding = 'UTF-8')
        text_body = text.read()
        text.close()
        return text_body
    elif file.endswith('.docx'):
        doc = docx.Document(rf'{file}')
        text = (paragraph.text for paragraph in doc.paragraphs)
        text_body = '\n'.join(text)
        return text_body
    else:
        print('Неподдерживаемый формат!')
        pass
        
def name_extractor(file):
    try:
        name = file.split('\\')[1]
    except:
        name = file.split('/')[-1]
    return name

def old_spelling_changer(word):
    word = word.replace('І', 'И').replace('і', 'и')\
           .replace('Ѣ', 'Е').replace('ѣ', 'е')\
           .replace('Ѵ', 'И').replace('ѵ', 'и')\
           .replace('Ѳ', 'Ф').replace('ѳ', 'ф')\
           .strip('-')
    if word.endswith('ъ'):
        word = word.replace('ъ', '')
    if word.endswith('ъся'):
        word = word.replace('ъся', 'ся')
    if word.endswith('ия'):
        word = word.replace('ия', 'ие')
    if word.endswith('ияся'):
        word = word.replace('ияся', 'иеся')
    if word.endswith('ыя'):
        word = word.replace('ыя', 'ые')
    if word.endswith('ыяся'):
        word = word.replace('ыяся', 'ыеся')
    if word.endswith('яго'):
        word = word.replace('яго', 'его')
    if word.endswith('ягося'):
        word = word.replace('ягося', 'егося')
    if word.endswith('аго'):
        word = word.replace('аго', 'ого')
    if word.endswith('агося'):
        word = word.replace('агося', 'огося')
    if word == 'однѣ':
        word = word.replace('ѣ', 'и')
    if word == 'однѣх':
        word = word.replace('ѣх', 'их')
    if word == 'однѣм':
        word = word.replace('ѣм', 'им')
    if word == 'однѣми':
        word = word.replace('ѣми', 'ими')
    if word.endswith('иих'):
        word = word.replace('иих', 'иях')
    if 'ъ-' in word:
        word = word.replace('ъ-', '-')
    return word

def lemmatize(file):                                                               #НАЧАЛО БОЛЬШОЙ ФУНКЦИИ ЛЕММАТИЗАЦИИ
    name = name_extractor(file)                                                    #Извлекаем имя файла
    text = text_extractor(file)                                                    #Извлекаем текст файла
    text = text.replace('\n',' ')                                                  #Заменяем в текста знаки новой строки на пробелы
    sents = dict(enumerate(st(text)))                                              #Делим текст на предложения и нумеруем словарём
    new_sents = [f'{sents[num]} NUMIN{num}NUMOUT' for num in sents]                #Добавляем к предложениям NUMINномерNUMOUT
    new_text = re.sub('''([*.,:;?!()"«»“„_—>'])''','', ' '.join(new_sents))        #Избавляем текст от лишних знаков препинания
    new_text = new_text.replace('\n',' ')                                          #Заменяем в тексте знаки новой строки на пробелы
    wt_new_text = wt(new_text)
    new_spell = list(map(old_spelling_changer,wt_new_text))
    new_text = ' '.join(new_spell)
    lemmatized = morph.analyze(new_text)                                           #Получаем словарь грамматического анализа Mystem

    #Функция для линеаризации данных каждого вхождения из словаря грамматического анализа
    def transform(item):     
        if len(item) == 1:
            if item["text"].isdigit():
                return f'{item["text"]}##None##None'
            else:
                return item["text"]
        elif len(item) > 1 and item["analysis"] == []:
            return f'{item["text"]}##None##None'
        elif len(item) > 1 and item["analysis"] != []:
            gram = item["analysis"][0]
            return f'{item["text"]}##{gram["lex"]}##{gram["gr"]}'

        
    transformed = [transform(item) for item in lemmatized]                          #Получаем список линеаризованных вхождений из грамм. словаря         
    linearized = ''.join(transformed)                                               #Соединяем вхождения в линейную последовательность
    num_sents = (re.split('NUMIN', sent) for sent in re.split('NUMOUT',linearized)) #Делим лемматизированные предложения на предложение и номер
    num_sents = [sent for sent in num_sents if len(sent) > 1]
    
    def make_item(sent):                                                            #Делим предложения на список вхождений лемм плюс номер
        sent_num = sent[1]
        sent_content = sent[0]
        items = re.split(' ', sent_content)
        word_items = [item for item in items if '##' in item]
        len_sent = len(word_items)
        return items, sent_num, len_sent                                            #Сначала идут вхождения лемм, потом номер предложения
    
    items = [make_item(sent) for sent in num_sents]
    entries = [f'{elt}##{item[1]}##{item[2]}' for item in items for elt in item[0] if '##' in elt] #Здесь добавляем номер предложения в том же формате, что и грамм. данные

    def make_sextet(entry):       #Эта функция нужна, чтобы из линейных грамм. данных с номером предложения получить список грамм. данных и текст предложения
        quint = re.split('##', entry)                   #Делим линейные грамм. данные по разделителю на токен, лемму, вес, грамм. хар-ку и номер предложения
        if len(quint) == 5:                                                                 #Проверяем, что наша упорядоченная пятёрка действительно пятёрка
            sent_num = quint[3]                                                                            #Присваиваем имя переменной -- номеру предложения
            len_sent = quint[4]
            orig_sent = sents[int(sent_num)]                                           #Получаем по номеру из списка оригинальных предложений соотв. предложение
            return quint[0],quint[1],quint[2],orig_sent, len_sent, f'[{name}]'      #Возвращаем шестерку: (токен, лемма, грамм. хар-ка, предл-е, длина, название)
        else:                                                                       #Если пятёрка оказалась не пятёркой, 
            return 'None'                                                           #возвращаем None

    sextets = [make_sextet(entry) for entry in entries]                       #Применяем make_sextet к entries
    sextets = [sextet for sextet in sextets if len(sextet) == 6]     #Отбраковываем те шестёрки, для которых make_sextet выдала None
    return sextets                                                   #Возвращаем шестёрки. КОНЕЦ БОЛЬШОЙ ФУНКЦИИ ЛЕММАТИЗАЦИИ

def core(files):                                                                    #ЦЕНТРАЛЬНАЯ ФУНКЦИЯ
    con = sqlite3.connect('Concordance.db')                                         #СОЗДАЁМ БАЗУ ДАННЫХ
    cur = con.cursor()
    cur.execute('PRAGMA synchronous = OFF')
    cur.execute('PRAGMA temp_store = MEMORY')
    cur.execute('CREATE TABLE IF NOT EXISTS entries(token TEXT, lemma TEXT, grammar TEXT, sentence TEXT, length TEXT, textname TEXT)')
    all_entries = [lemmatize(file) for file in files]
    all_entries = [sextet for entry in all_entries for sextet in entry]
    insertion = [cur.execute('INSERT INTO entries VALUES(?,?,?,?,?,?)', sextet) for sextet in all_entries]
    show_prog(insertion, 'Заполнение таблицы')
    con.commit()
    return cur

def print_result(cur):
    lemmata = {lemma[0]:1 for lemma in sorted(set(cur.execute('SELECT lemma FROM entries')))}
    show_prog(lemmata, 'Создание списка лемм')
    instances = {item:(item, list(cur.execute(f'SELECT token, grammar, sentence, length, textname FROM entries WHERE lemma = "{item}"'))) for item in lemmata}
    show_prog(instances, 'Создание списка вхождений')
    [print(instances[instance]) for instance in instances]

    
def do_several():
    files = get_several_files()
    cur = core(files)
    print_result(cur)

def do_all():
    files = get_all_files()
    cur = core(files)

do_several()
