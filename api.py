from flask import Flask,request,jsonify
from flask_cors import CORS
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask_caching import Cache

app=Flask(__name__)
CORS(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Use the credentials to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(credentials)
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1vqC1sqEkoEqdTcu1UBwtOxN-vizwMMxD2aXYUPh4H_4/edit?usp=sharing"
spreadsheet = client.open_by_url(spreadsheet_url)

def is_present(text, pattern):
  pattern_length = len(pattern)
  offset_table = {}
  for i in range(pattern_length - 1):
    offset_table[pattern[i]] = pattern_length - 1 - i
  text_index = pattern_length - 1
  while text_index < len(text):
    pattern_index = pattern_length - 1
    while pattern_index >= 0 and text[text_index] == pattern[pattern_index]:
      text_index -= 1
      pattern_index -= 1
    if pattern_index == -1:
      return True
    else:
      text_index += max(offset_table.get(text[text_index], pattern_length), pattern_index - offset_table.get(pattern[pattern_index], 0))
  return False

@cache.cached(timeout=3600)
def get_data_from_sheet():
    sheet = spreadsheet.sheet1
    data = sheet.get_all_values()
    return data

@app.route('/',methods=['GET'])
def get_data():
    return 'Hello World !'

@app.route('/subjects', methods=['GET'])
def get_subjects():
    data = get_data_from_sheet()
    subjects = set()
    counter=0
    for row in data:
        if counter==0:
            counter=1
            continue
        subjects.add(row[3])
    return jsonify(list(subjects))

@app.route('/data',methods=['POST'])
def show_data():
    global dict_search
    data = get_data_from_sheet()
    incoming_data=request.get_json()
    PageNo =incoming_data.get('page')
    BookAccNo = incoming_data.get('accNo')
    BookName = incoming_data.get('title')
    BookAuthor = incoming_data.get('author')
    BookSubject = incoming_data.get('subjectType')
    BooksList = []
    limst_1=[]
    limst_2=[]
    limst_3=[]
    iter=1
    if not BookAccNo and not BookName and not BookAuthor:
        lunt=0
        for iter in data:
            if lunt==0:
                lunt=1
                continue
            acc=iter[0]
            bookname=iter[1]
            bookauthor=iter[2]
            booksubject=iter[3]
            json_output = {'accNo':acc,'title':bookname,'author':bookauthor,'subjectType':booksubject}
            if BookSubject:
                if booksubject.lower()==BookSubject.lower():
                    BooksList.append(json_output)
            else:
                BooksList.append(json_output)
    else:
        while(iter < len(data)):
            counter=0
            acc=data[iter][0]
            bookname=data[iter][1]
            bookauthor=data[iter][2]
            booksubject=data[iter][3]
            json_output = {'accNo':acc,'title':bookname,'author':bookauthor,'subjectType':booksubject}
            if BookAccNo==acc and BookAccNo and acc!=None:
                counter=counter+1
            if is_present(bookname.lower(),BookName.lower()) and BookName and bookname!=None:
                counter=counter+1
            if is_present(bookauthor.lower(),BookAuthor.lower()) and BookAuthor and bookauthor!=None:
                counter=counter+1
            iter+=1
            if counter>=3:
                if BookSubject:
                    if booksubject.lower()==BookSubject.lower():
                        limst_3.append(json_output)
                else:
                    limst_3.append(json_output)
            elif counter==2:
                if BookSubject:
                    if booksubject.lower()==BookSubject.lower():
                        limst_2.append(json_output)
                else:
                    limst_2.append(json_output)
            elif counter==1:
                if BookSubject:
                    if booksubject.lower()==BookSubject.lower():
                        limst_1.append(json_output)
                else:
                    limst_1.append(json_output)
        BooksList=limst_3+limst_2+limst_1

    PageNo=int(PageNo)
    iter = (PageNo-1)*20
    limit = PageNo*20
    TotalPages=len(BooksList)
    BooksFinalList=[]
    while(iter<limit and iter<TotalPages):
        BooksFinalList.append(BooksList[iter])
        iter+=1
    return [{'MaxPage':int(TotalPages/20)+(TotalPages%20!=0)},{'BookList':BooksFinalList}]

if __name__ == '__main__':
    app.run(debug=True,port=5000)