import tkinter

main = tkinter.Tk()
mainmenu = tkinter.Menu(main)
main.config(menu=mainmenu)

def exit():
    main.destroy()

filemenu = tkinter.Menu(mainmenu,tearoff=0)
filemenu.add_command(label='Котоподобие')
filemenu.add_command(label='Слоноподобие')
filemenu.add_command(label='Пайти проч',command=exit)

helpmenu = tkinter.Menu(mainmenu,tearoff=0)
helpmenu.add_command(label='Помашшь')
helpmenu.add_command(label='Хто ета зделал')

mainmenu.add_cascade(label='Фаел',menu=filemenu)
mainmenu.add_cascade(label='Што ита такои',menu=helpmenu)
main.mainloop()
