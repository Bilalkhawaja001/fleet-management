import sqlite3
con = sqlite3.connect('instance/fleet.db')
cur = con.execute('PRAGMA table_info(vehicles)')
print([r[1] for r in cur.fetchall()])
