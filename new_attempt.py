print('(C) Евгений Геннадьевич Соколов, ИЛИ РАН, СПб, 2022 г.')

import re, sqlite3, docx, tkinter, tkinter.messagebox, os, pymystem3
import tkinter.filedialog as fd, tkinter.ttk as ttk
from math import fabs
from sys import exit
from collections import defaultdict
from nltk import sent_tokenize as st, word_tokenize as wt
from PySimpleGUI import one_line_progress_meter as progress

morph = pymystem3.Mystem()

def docx_asker():
    result = fd.asksaveasfilename(defaultextension = '.docx')
    return result

def txt_asker():
    result = fd.asksaveasfilename(defaultextension = '.txt')
    return result

def show_prog(fragment, title):
    span = int(len(fragment)/50)+1
    elts = [elt for elt in range(0,len(fragment), span)]
    elts.append(len(fragment))
    [progress(f'{title}', n, len(fragment), f'Элемент {n}') for n in elts]

def get_all_files():
    directory = fd.askdirectory()
    files = tuple(rf'{os.path.join(dirpath, filename)}' \
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

def main_window():                                      #ГЛАВНОЕ ОКНО

    def whats_next():
        next_window = tkinter.Tk()
        init_label = tkinter.Label(next_window, text = 'Выберите действие над базой данных', font = 'Arial 15')
        init_label.grid(row=0,column=0)
        concord_button = tkinter.Button(next_window, text = 'Составить конкорданс', font = 'Arial 15', command=concordance_maker)
        concord_button.grid(row=1,column=0)
        init_button = tkinter.Button(next_window, text = 'Поиск слов и словосочетаний', font = 'Arial 15', command=int_search)
        init_button.grid(row=2,column=0)
        exit_button = tkinter.Button(next_window, text = 'Выйти', font = 'Arial 15', command=next_window.destroy)
        exit_button.grid(row=3,column=0)
        next_window.mainloop()

    def lemmatize(file):                                                               #НАЧАЛО БОЛЬШОЙ ФУНКЦИИ ЛЕММАТИЗАЦИИ
        name = name_extractor(file)                                                    #Извлекаем имя файла
        text = text_extractor(file)                                                    #Извлекаем текст файла
        text = text.replace('\n',' ')                                                  #Заменяем в текста знаки новой строки на пробелы
        sents = dict(enumerate(st(text)))                                              #Делим текст на предложения и нумеруем словарём
        new_sents = [f'{sents[num]} NUMIN{num}NUMOUT' for num in sents]                #Добавляем к предложениям NUMINномерNUMOUT
        new_text = re.sub('''([*.,:;?!()"«»“„_—>'])''','', ' '.join(new_sents))        #Избавляем текст от лишних знаков препинания
        new_text = new_text.replace('\n',' ')                                          #Заменяем в тексте знаки новой строки на пробелы
        analyzed = morph.analyze(new_text)                                           #Получаем словарь грамматического анализа Mystem
        lemmatized = morph.lemmatize(new_text)                                       #Получаем список лемматизированных предложений
        

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

            
        transformed = [transform(item) for item in analyzed]                          #Получаем список линеаризованных вхождений из грамм. словаря         
        linearized = ''.join(transformed)                                               #Соединяем вхождения в линейную последовательность
        linear_lemm = ''.join(lemmatized)                                               # Тут линейно соединяем леммматизированные предложения
        num_sents = (re.split('NUMIN', sent) for sent in re.split('NUMOUT',linearized)) #Делим анализированные предложения на предложение и номер
        num_lemm = (item for item in (re.split('NUMIN',sent) for sent in re.split('NUMOUT',linear_lemm)) if len(item)>1) #То же для леммат. предлож.
        num_lemm = {int(item[1]):item[0] for item in num_lemm}
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

        def make_septet(entry):       #Эта функция нужна, чтобы из линейных грамм. данных с номером предложения получить список грамм. данных и текст предложения
            quint = re.split('##', entry)                   #Делим линейные грамм. данные по разделителю на токен, лемму, вес, грамм. хар-ку и номер предложения
            if len(quint) == 5:                                                                 #Проверяем, что наша упорядоченная пятёрка действительно пятёрка
                sent_num = quint[3]                                                                            #Присваиваем имя переменной -- номеру предложения
                len_sent = quint[4]
                lemm_sent = num_lemm[int(sent_num)]
                orig_sent = sents[int(sent_num)]                                           #Получаем по номеру из списка оригинальных предложений соотв. предложение
                return quint[0],quint[1],quint[2],lemm_sent,orig_sent, len_sent, f'[{name}]'      #Возвращаем семерку: (токен, лемма, грамм. хар-ка, предл-е, ориг. предл-е, длина, название)
            else:                                                                       #Если пятёрка оказалась не пятёркой, 
                return 'None'                                                           #возвращаем None

        septets = [make_septet(entry) for entry in entries]                       #Применяем make_septet к entries
        septets = [septet for septet in septets if len(septet) == 7]     #Отбраковываем те семерки, для которых make_septet выдала None
        return septets                                                   #Возвращаем семерки. КОНЕЦ БОЛЬШОЙ ФУНКЦИИ ЛЕММАТИЗАЦИИ

    def core(files,address):                                             #ЦЕНТРАЛЬНАЯ ФУНКЦИЯ, В НЕЁ ВЛОЖЕНА ФУНКЦИЯ ЛЕММАТИЗАЦИИ
        global cur
        con = sqlite3.connect(rf'{address}')
        cur = con.cursor()
        cur.execute('PRAGMA synchronous = OFF')
        cur.execute('PRAGMA temp_store = MEMORY')
        cur.execute('CREATE TABLE IF NOT EXISTS entries(token TEXT, lemma TEXT, grammar TEXT, sent_lemmata TEXT, sentence TEXT, length TEXT, textname TEXT)')
        all_entries = [lemmatize(file) for file in files]
        all_entries = [septet for entry in all_entries for septet in entry]
        insertion = [cur.execute('INSERT INTO entries VALUES(?,?,?,?,?,?,?)', septet) for septet in all_entries if septet[1] != 'None']
        show_prog(insertion, 'Заполнение таблицы')
        con.commit()
        label['text'] = f'База данных {address} создана'
        proc_button['text'] = f'Обработать эту базу'
        proc_button['command'] = whats_next

    def concordance_maker():                             #ФУНКЦИЯ ДЛЯ СОСТАВЛЕНИЯ КОНКОРДАНСОВ НА ОСНОВЕ СОЗДАННОЙ ИЛИ ОТКРЫТОЙ БД
        text_body.delete(1.0, tkinter.END)
        global address
        con = sqlite3.connect(rf'{address}')
        cur = con.cursor()
        cur.execute('PRAGMA synchronous = OFF')
        cur.execute('PRAGMA temp_store = MEMORY')
        instances = dict(enumerate(cur.execute(f'SELECT lemma,sentence,textname FROM entries')))
        show_prog(instances, 'Составление списка примеров')
        examples = defaultdict()
        instances = dict(enumerate(cur.execute(f'SELECT lemma,sentence,textname FROM entries')))
        def compare(item):
            if item[0] not in examples:
                examples[item[0]] = [(item[1],item[2])]
            elif item[0] in examples:
                examples[item[0]].append((item[1],item[2]))
        [compare(instances[instance]) for instance in instances]
        examples = dict(sorted(examples.items()))
        show_prog(examples, 'Составление конкорданса')
        overall_length = list(cur.execute('SELECT length FROM entries GROUP BY sentence'))
        print(overall_length)
        overall_length = sum([int(x[0]) for x in overall_length])
        overall_string = ''
        def string_adder(instance):
            example_string = ''
            number = len(examples[instance])
            example_string += f'#{instance}=, '.upper()
            example_string += f'число употреблений == {number}, ipm = {(number/overall_length)*10**6}\n\n'
            for pair in examples[instance]:
                sentence = pair[0]
                textname = pair[1]
                example_string += f'{sentence} {textname} \n\n'
            return example_string
        overall_string = list(map(string_adder,examples))
        overall_string = ''.join(overall_string)

        def next_step(overall_string):
            def txt_writedown():
                result = txt_asker()
                txt = open(rf'{result}', 'w', encoding = 'UTF-8')
                txt.write(f'{overall_string}')
                txt.close()
                tkinter.messagebox.showinfo(title = 'Успех!', message = f'Файл сохранён по адресу {result}')

            def docx_writedown():
                result = docx_asker()
                doc = docx.Document()
                doc.add_paragraph(overall_string)
                doc.save(rf'{result}')
                tkinter.messagebox.showinfo(title = 'Успех!', message = f'Файл сохранён по адресу {result}')    
                
            next_window = tkinter.Tk()
            next_window.title('Вывод результатов')
            next_window.geometry('450x300')
            next_frame = tkinter.Frame(next_window)
            next_label = tkinter.Label(next_frame, text = 'Как отобразить результат?', font = 'Arial 15')
            scr_button = tkinter.Button(next_frame, text = 'Вывести на экран', font = 'Arial 15', command = lambda: text_body.insert(1.0, f'{overall_string}'))
            txt_button = tkinter.Button(next_frame, text = 'Вывести в файл .txt', font = 'Arial 15', command = txt_writedown)
            docx_button = tkinter.Button(next_frame, text = 'Вывести в файл .docx', font = 'Arial 15', command = docx_writedown)
            ext_button = tkinter.Button(next_frame, text = 'Выйти', font = 'Arial 15', command = lambda: next_window.destroy())
            next_label.pack()
            scr_button.pack()
            txt_button.pack()
            docx_button.pack()
            ext_button.pack()
            next_frame.pack()
            next_window.mainloop()
        next_step(overall_string)
        
    def old_int_search():
        def do_search():
            word = entry_a.get().lower()
            text_body.delete(1.0, tkinter.END)
            global address
            con = sqlite3.connect(rf'{address}')
            cur = con.cursor()
            to_check = [list(cur.execute(f'SELECT sent_lemmata, sentence, textname FROM entries WHERE lemma = "{word}"'))][0]
            to_check = [(elt[0].strip().split(' '),elt[1],elt[2]) for elt in to_check]
            print(to_check)

        query_window = tkinter.Tk()
        query_window.geometry('450x300')
        frame_a = tkinter.Frame(query_window)
        entry_a = tkinter.Entry(frame_a, width = '30')
        button_b = tkinter.Button(frame_a, command = do_search, text = 'Обработка', font = 'Arial 15', bg = 'cyan')
        entry_a.pack()
        button_b.pack()
        frame_a.pack()
        query_window.mainloop()

    def int_search():
        query = []
        def add_query():
            word = entry_no1.get().lower()
            distance = dist.get()
            query.append(word)
            query.append(distance)
            label_no4b['text'] = query
            return query

        def do_search():
            global address
            if query == []:
                tkinter.messagebox.showinfo(title = 'Ошибка!', message = 'Запрос пуст!')
            #elif 'None' in query and query.index('None') != -1:
            #    tkinter.messagebox.showinfo(title = 'Ошибка!', message = 'Расстояние между словами не бывает пустым ("None")!')
            elif len(query) == 2 and query[-1] == 'None':
                word = query[0]
                con = sqlite3.connect(rf'{address}')
                cur = con.cursor()
                to_check = [list(cur.execute(f'SELECT sent_lemmata, sentence, textname FROM entries WHERE lemma = "{word}"'))][0]
                print(to_check)
            elif len(query) >= 2 and query[-1] != 'None':
                tkinter.messagebox.showinfo(title = 'Ошибка!', message = 'Неверно составленный запрос!')
            elif len(query) >= 3:
                query.pop(-1) #Поскольку последний элемент в правильно составленном запросе всегда None, удалим его
                dists = [elt for elt in query if query.index(elt)%2 != 0] #Нечетные элементы -- расстояния. Выделим их
                words = [elt for elt in query if query.index(elt)%2 == 0] #Чётные элементы -- лексемы.
                word_pairs = [(words[num], words[num+1]) for num in range(0,(len(dists)))]
                print(word_pairs)
                # Поскольку пар у нас столько, сколько чисел, обозначающих расстояния, собираем пары по этому принципу
                pairs_and_dists = [(word_pairs[n], dists[n]) for n in range(0,(len(dists)))]
                #Объединили пары и расстояния в виде [((слово 1, слово 2), расстояние) ...]
                print(pairs_and_dists)
                con = sqlite3.connect(rf'{address}')
                cur = con.cursor()
                to_check = [list(cur.execute(f'SELECT sent_lemmata, sentence, textname FROM entries WHERE lemma = "{word}"')) for word in words][0]
                to_check = [(elt[0].strip().split(' '),elt[1],elt[2]) for elt in to_check]
                def check(entry): #Тут проверяем, все ли пары на нужном расстоянии в предложении на проверку
                    sentence = entry[0]
                    def check_elt(elt):
                        word_1 = elt[0][0]
                        word_2 = elt[0][1]
                        distance = elt[1]
                        # Если разница номеров слов в предложении равна нужному расстоянию плюс 1, то всё сходится
                        if word_1 in sentence and word_2 in sentence:
                            if sentence.index(word_2) - sentence.index(word_1) == int(distance) + 1:
                                return True
                            else: #Иначе не сходится
                                return False
                        else:
                            return False
                    result = [check_elt(elt) for elt in pairs_and_dists]
                    print(result)
                    return result
                # В список подходящих предложений входят только те, у которых все сравнения дали True
                what_fits = [f'{entry[1]} {entry[2]}' for entry in to_check if False not in check(entry)]
                example_num = len(what_fits) #Количество подходящих примеров
                print(what_fits)

        def clear():
            query.clear()
            label_no4b['text'] = query
            return query

        query_window = tkinter.Tk()
        query_window.geometry('450x300')
        frame_no1 = tkinter.Frame(query_window)
        frame_no2 = tkinter.Frame(query_window)
        frame_no3 = tkinter.Frame(query_window)
        frame_no4 = tkinter.Frame(query_window)
        frame_no5 = tkinter.Frame(query_window)
        label_no1 = tkinter.Label(frame_no1, text = 'Выберите лексему...', font = 'Arial 15')
        entry_no1 = tkinter.Entry(frame_no1, width = '30')
        label_no2 = tkinter.Label(frame_no2, text = '...и расстояние до следующей словоформы', font = 'Arial 15')
        dist = ttk.Combobox(frame_no2, values = [None,0,1,2,3,4,5,6,7,8,9,10])
        button_no1 = tkinter.Button(frame_no3, command = add_query, text = 'Добавить', font = 'Arial 15', bg = 'cyan')
        label_no4a = tkinter.Label(frame_no4, text = 'Структура запроса:', font = 'Arial 15')
        label_no4b = tkinter.Label(frame_no4, text = '', font = 'Times 15', bg = 'white')
        button_no2 = tkinter.Button(frame_no5, command = do_search, text = 'Обработка', font = 'Arial 15', bg = 'cyan')
        button_no3 = tkinter.Button(frame_no5, command = clear, text = 'Очистить запрос', font = 'Arial 15', bg = 'cyan')
        label_no1.pack(side = 'top')
        entry_no1.pack(side = 'bottom')
        label_no2.pack(side = 'top')
        dist.pack(side = 'bottom')
        button_no1.pack(side = 'bottom')
        label_no4a.pack(side = 'top')
        label_no4b.pack(side = 'bottom')
        button_no2.pack(side = 'bottom')
        button_no3.pack(side = 'bottom')
        frame_no1.pack()
        frame_no2.pack()
        frame_no3.pack()
        frame_no4.pack()
        frame_no5.pack()
        query_window.mainloop()

    def open_db():
        
        global address
        address = fd.askopenfilename()
        if address.endswith('.db'):
            label['text'] = f'Выбрана база данных {address}'
            proc_button['text'] = 'Обработать базу данных'
            proc_button['command'] = whats_next
        else:
            tkinter.messagebox.showinfo(title = 'Ошибка!', message = 'Вы выбрали файл не в формате базы данных!')

    def create_db():
        global address
        address = fd.asksaveasfilename(defaultextension = '.db')
        label['text'] = f'Будет создана база данных {address}'
        proc_button['text'] = 'Составить базу данных'
        proc_button['command'] = processing

    def processing():        
        global address
        files = get_several_files()
        core(files, address)

    def initial_search():
        global address

    def warning():
        tkinter.messagebox.showinfo(title='Не выбрано действие', message='Откройте меню "Работа с конкордансом"')    
    
    cur,address = None, ''

    window = tkinter.Tk()
    window.title('Составление и обработка конкордансов')
    window.geometry('600x600')
    mainmenu = tkinter.Menu()
    window.config(menu=mainmenu)

    frame_a = tkinter.Frame(window)
    label = tkinter.Label(frame_a,text='Выберите или создайте базу данных', font = 'Arial 15', anchor = 'center')
    label.pack()

    proc_button = tkinter.Button(frame_a,text='Выберите действие',command=warning, font = 'Arial 15')
    proc_button.pack()
    frame_a.pack()


    frame_b = tkinter.Frame(window)
    scrollbar = tkinter.Scrollbar(frame_b)
    text_body = tkinter.Text(frame_b, width = '100', height = '100',yscrollcommand=scrollbar.set)
    scrollbar.config(command=text_body.yview)
    scrollbar.pack(side = 'right', fill='y')
    text_body.pack()
    frame_b.pack()


    
    dbmenu = tkinter.Menu(mainmenu,tearoff=0)
    dbmenu.add_command(label='Открыть базу данных',command = open_db, font = 'Arial 15')
    dbmenu.add_command(label='Создать базу данных',command = create_db, font = 'Arial 15')
    dbmenu.add_separator()
    dbmenu.add_command(label='Выйти',command=exit, font = 'Arial 15')

    helpmenu = tkinter.Menu(mainmenu,tearoff=0)
    helpmenu.add_command(label='Руководство пользователя', font = 'Arial 15')
    helpmenu.add_command(label='О программе', font = 'Arial 15')

    mainmenu.add_cascade(label='Работа с конкордансом',menu=dbmenu, font = 'Arial 15')
    mainmenu.add_cascade(label='Справка',menu=helpmenu, font = 'Arial 15')
    
    window.mainloop()

main_window()    

