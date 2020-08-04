import csv, pyodbc

def read_arbin(source_path, save_path, table_name):
    #table_name = 'Channel_Normal_Table'
    # set up some constants
    MDB = source_path
    DRV = '{Microsoft Access Driver (*.mdb)}'
    PWD = 'pw'

    # connect to db
    con = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(DRV,MDB,PWD))
    cur = con.cursor()
    header_row = []
    for r in cur.columns(table=table_name):
        header_row.append(r.column_name)
        
    # run a query and get the results 
    SQL = 'SELECT * FROM %s;'%(table_name) # your query goes here
    rows = cur.execute(SQL).fetchall()
    rows.insert(0, header_row)
    cur.close()
    con.close()

    with open(save_path, 'w', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerows(rows)

read_arbin('MnMn-B02-S01-A-E1.res', 'test.csv', 'Channel_Normal_Table')