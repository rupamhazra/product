import pandas as pd
import pymysql

data = pd.read_csv('excel_inputs/email.csv',encoding ='latin1')  
#df = pd.DataFrame(data, columns= ['Personnel','Email'])
#print(df)

conn = pymysql.connect("localhost","root","admin@123","ssil" )
print(conn)
cur = conn.cursor()

skipHeader = True

for i,row in data.iterrows():
	if skipHeader:
		skipHeader = False
		continue
	print(row,type(row))
	cur.execute("INSERT INTO demo_email(Personnel, Email) VALUES('{0}', '{1}')".format(row['Personnel'],row['Email']))
	
conn.commit()

