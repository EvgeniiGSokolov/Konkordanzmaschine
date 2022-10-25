import tkinter

def q():
    aaa = tkinter.Tk()
    qqq = tkinter.Frame(aaa)
    rrr = tkinter.Label(qqq, text = 'Чупка!')
    rrr.pack()
    qqq.pack()
    tkinter.mainloop()

class GUI:

    def __init__(self):
        self.main = tkinter.Tk()
        self.frame_a = tkinter.Frame(self.main)
        self.label_a = tkinter.Label(self.frame_a, text = 'Пепяка')
        self.button_a = tkinter.Button(self.frame_a, text = 'Магия?', command = q)
        self.label_a.pack()
        self.button_a.pack()
        self.frame_a.pack()
        tkinter.mainloop()
GUI()
