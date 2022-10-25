print("(C) Евгений Геннадьевич Соколов, ИЛИ РАН, СПб, 2022 г.")

import re, sqlite3, docx, tkinter, tkinter.messagebox, os, pymystem3
import tkinter.filedialog as fd
from collections import defaultdict
from nltk import sent_tokenize as st, word_tokenize as wt
from PySimpleGUI import one_line_progress_meter as progress

morph = pymystem3.Mystem()

# (1.2.а) В .docx:
def docx_asker():
    result = fd.asksaveasfilename(defaultextension = '.docx')
    return result

# (1.2.б) В .txt:
def txt_asker():
    result = fd.asksaveasfilename(defaultextension = '.txt')
    return result

# Графический интерфейс
def main_window():

    cur = None

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


    def lemmatize(file):                                                               #НАЧАЛО БОЛЬШОЙ ФУНКЦИИ ЛЕММАТИЗАЦИИ
        name = name_extractor(file)                                                    #Извлекаем имя файла
        text = text_extractor(file)                                                    #Извлекаем текст файла
        text = text.replace('\n',' ')                                                  #Заменяем в текста знаки новой строки на пробелы
        sents = dict(enumerate(st(text)))                                              #Делим текст на предложения и нумеруем словарём
        new_sents = [f'{sents[num]} NUMIN{num}NUMOUT' for num in sents]                #Добавляем к предложениям NUMINномерNUMOUT
        new_text = re.sub('''([*.,:;?!()"«»“„_—>'])''','', ' '.join(new_sents))        #Избавляем текст от лишних знаков препинания
        new_text = new_text.replace('\n',' ')                                          #Заменяем в тексте знаки новой строки на пробелы
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

    def core(files,address):                                                            #ЦЕНТРАЛЬНАЯ ФУНКЦИЯ
        global cur
        con = sqlite3.connect(rf'{address}')                                            #СОЗДАЁМ БАЗУ ДАННЫХ
        cur = con.cursor()
        cur.execute('PRAGMA synchronous = OFF')
        cur.execute('PRAGMA temp_store = MEMORY')
        cur.execute('CREATE TABLE IF NOT EXISTS entries(token TEXT, lemma TEXT, grammar TEXT, sentence TEXT, length TEXT, textname TEXT)')
        all_entries = [lemmatize(file) for file in files]
        all_entries = [sextet for entry in all_entries for sextet in entry]
        #insertion = [cur.execute('INSERT INTO entries VALUES(?,?,?,?,?,?)', sextet) for sextet in all_entries]
        insertion = [cur.execute('INSERT INTO entries VALUES(?,?,?,?,?,?)', sextet) for sextet in all_entries if sextet[1] != 'None']
        show_prog(insertion, 'Заполнение таблицы')
        con.commit()
        label['text'] = f'База данных {address} создана'
        proc_button['text'] = f'Обработать эту базу'
        proc_button['command'] = whats_next

    def concordance_maker():
        text_body.delete(1.0, tkinter.END)
        global address
        con = sqlite3.connect(rf'{address}')
        cur = con.cursor()
        cur.execute('PRAGMA synchronous = OFF')
        cur.execute('PRAGMA temp_store = MEMORY')
        instances = dict(enumerate(cur.execute(f'SELECT lemma,sentence,textname FROM entries')))
        show_prog(instances, 'Составление списка примеров')
        lemmata = sorted(set(tuple(instances[instance][0] for instance in instances if instances[instance][0] != None)))
        show_prog(lemmata, 'Составление списка лемм')
        examples = defaultdict()
        def compare(lemma,instance):
            if lemma not in examples:
                examples[lemma] = []
            elif lemma in examples:
                if lemma == instance[0] and instance[0] != None:
                    examples[lemma].append((instance[1],instance[2]))
                else:
                    pass
        [compare(lemma,instances[instance]) for lemma in lemmata for instance in instances if lemma != None]
        show_prog(examples, 'Составление конкорданса')
        #Конец выделенного фрагмента. ЧТО-ТО С ЭТИМ СДЕЛАТЬ. ПРОГРАММА ЛОЖИТСЯ НАМЕРТВО!
        #instances.reverse()
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
            
#*********************************************************************************************************************************************************************
    def pos_search():
        pos_tag = ''
        def noun():
            global pos_tag
            pos_tag = 'N'
        def verb():
            global pos_tag
            pos_tag = 'V'          
        def adjective():
            global pos_tag
            pos_tag = 'A'
        def preposition():
            global pos_tag
            pos_tag = 'PR'
        def selector():
            text_body.delete(1.0, tkinter.END)
            global pos_tag
            required = list(cur.execute(f'SELECT * FROM entries WHERE grammar LIKE "{pos_tag}%"'))
            example_string = ''
            for example in required:
                lemma = example[1]
                txt = example[3]
                textname = example[5]
                example_string += f'#{lemma.upper()}= \n\n {txt}[{textname}]\n\n'
            text_body.insert(1.0, example_string)
            #print(required)
            
        global address
        con = sqlite3.connect(rf'{address}')
        cur = con.cursor()
        pos_window = tkinter.Tk()
        pos_frame_1 = tkinter.Frame(pos_window)
        pos_label = tkinter.Label(pos_frame_1, text = 'Выберите часть речи', font = 'Arial 15')
        pos_label.pack()
        pos_frame_2 = tkinter.Frame(pos_window)
        noun_button = tkinter.Button(pos_frame_2, text = 'Существительное', font = 'Arial 15', command=noun)
        verb_button = tkinter.Button(pos_frame_2, text = 'Глагол', font = 'Arial 15', command=verb)
        adj_button = tkinter.Button(pos_frame_2, text = 'Прилагательное', font = 'Arial 15', command=adjective)
        prep_button = tkinter.Button(pos_frame_2, text = 'Предлог', font = 'Arial 15', command=preposition)
        select_button = tkinter.Button(pos_frame_2,text = 'Выбрать', font = 'Arial 15',command=selector)
        noun_button.pack()
        verb_button.pack()
        adj_button.pack()
        prep_button.pack()
        select_button.pack()
        pos_frame_1.pack()
        pos_frame_2.pack()
        pos_window.mainloop()
#*********************************************************************************************************************************************************************            

################################################################################################

    def int_search():
        def do_search():
            global address
            con = sqlite3.connect(rf'{address}')
            cur = con.cursor()
            lemmata = tuple(lemma[0] for lemma in sorted(set(cur.execute('SELECT lemma FROM entries'))))
            query = [item for item in re.split(' ', entry_b.get().lower()) if item != '']
            to_search = [lemma for string in query for lemma in lemmata if lemma.startswith(string)]
            results = [(item, list(cur.execute(f'SELECT sentence, length, textname FROM entries WHERE lemma = "{item}"'))) for item in to_search]
            overall_length = sum([int(item[0]) for item in list(cur.execute('SELECT length FROM entries GROUP BY sentence'))])
            overall_text = ''
            for entry in results:
                num = len(entry[1])
                entry_string = ''
                entry_string += f'{entry[0].upper()}, употреблений: {num}, ipm: {(num/overall_length)*10**6}\n\n'
                for triple in entry[1]:
                    sentence = triple[0]
                    textname = triple[2]
                    entry_string += f'{sentence} {textname}\n\n'
                overall_text += f'{entry_string}'
                
            def next_step(overall_string):
                text_body.delete(1.0, tkinter.END)
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
            next_step(overall_text)
            
        query_window = tkinter.Tk()
        query_window.geometry('450x200')
        frame_a = tkinter.Frame(query_window)
        label_a = tkinter.Label(frame_a, text = 'Введите через пробел интересующие Вас слова или части слов')
        frame_b = tkinter.Frame(query_window)
        entry_b = tkinter.Entry(frame_b, width = '100')
        button_b = tkinter.Button(frame_b, command = do_search, text = 'Обработка', font = 'Arial 15', bg = 'cyan')
        entry_b.pack()
        frame_a.pack()
        frame_b.pack()
        label_a.pack()
        button_b.pack()
        frame_b.pack()
        tkinter.mainloop()

#Выбор действия над составленной базой данных
    def whats_next():
        def exitium():
            next_window.destroy()
        next_window = tkinter.Tk()
        init_label = tkinter.Label(next_window, text = 'Выберите действие над базой данных', font = 'Arial 15')
        init_label.grid(row=0,column=0)
        concord_button = tkinter.Button(next_window, text = 'Составить конкорданс', font = 'Arial 15', command=concordance_maker)
        concord_button.grid(row=1,column=0)
        init_button = tkinter.Button(next_window, text = 'Поиск по слову', font = 'Arial 15', command=int_search)
        init_button.grid(row=2,column=0)
        gram_button = tkinter.Button(next_window, text = 'Частеречно-грамматический поиск', font = 'Arial 15', command=pos_search)
        gram_button.grid(row=3,column=0)
        exit_button = tkinter.Button(next_window, text = 'Выйти', font = 'Arial 15', command=exitium)
        exit_button.grid(row=4,column=0)
        next_window.mainloop()

#********************************************************************************************************************************************************************    

    address = ''

    window = tkinter.Tk()
    window.title('Составление и обработка конкордансов')
    window.geometry('600x600')
    mainmenu = tkinter.Menu()
    window.config(menu=mainmenu)

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

    def exit():
        window.destroy()

    def processing():        
        global address
        files = get_several_files()
        core(files, address)

    def initial_search():
        global address

    def warning():
        tkinter.messagebox.showinfo(title='Не выбрано действие', message='Откройте меню "Работа с конкордансом"')

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
