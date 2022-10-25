import tkinter, tkinter.filedialog as fd    

def main_window():
    address = ''

    window = tkinter.Tk()
    window.geometry('640x480')
    mainmenu = tkinter.Menu()
    window.config(menu=mainmenu)

    def open_db():
        global address
        address = fd.askopenfilename()
        label['text'] = f'Выбрана база данных {address}'

    def create_db():
        global address
        address = fd.asksaveasfilename(defaultextension = '.db')
        label['text'] = f'Выбрана база данных {address}'

    def exit():
        window.destroy()

    label = tkinter.Label(text='')
    label.grid(row=0,column=0)

    dbmenu = tkinter.Menu(mainmenu,tearoff=0)
    dbmenu.add_command(label='Открыть базу данных',command = open_db)
    dbmenu.add_command(label='Создать базу данных',command = create_db)
    dbmenu.add_separator()
    dbmenu.add_command(label='Выйти',command=exit)

    helpmenu = tkinter.Menu(mainmenu,tearoff=0)
    helpmenu.add_command(label='Руководство пользователя')
    helpmenu.add_command(label='О программе')

    mainmenu.add_cascade(label='Работа с конкордансом',menu=dbmenu)
    mainmenu.add_cascade(label='Справка',menu=helpmenu)
    
    window.mainloop()

main_window()
