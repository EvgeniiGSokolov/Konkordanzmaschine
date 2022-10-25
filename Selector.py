import sqlite3, tkinter

con = sqlite3.connect('Concordance.db')
cur = con.cursor()
required = cur.execute('SELECT * FROM entries WHERE grammar like "PR%"')
print(list(required))
