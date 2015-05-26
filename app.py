import os
import sys 
from flask import Flask,render_template, request,json

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Welcome to Python Flask!'

@app.route('/hnefatafl')
def signUp():
    return render_template('board.html')

@app.route('/send_move', methods=['POST'])
def sendMove():
    data =  request.get_json()
    print(data)
   
    x = data["x"]
    y = data["y"]
    new_x = data["new_x"]
    new_y = data["new_y"]

    print ("x:%d y%d: new_x:%d new_y:%d" % (x, y, new_x, new_y) )

    return json.dumps({'status':'OK','x':x,'y':y});

@app.route('/start', methods=['GET'])
def start():
    print ("recebi")
    f = open(sys.argv[1], "r")
    board = [ ln.strip().split() for ln in f ]
    
    print(board)
    lines = len(board)
    columns = len(board[0])

    corners = ( (0,0), (0,columns-1), (lines-1,0), (lines-1,columns-1) )

    for i,j in corners:
        board[i][j] = '+'

    print(board)
    return json.dumps(board)

if __name__=="__main__":

    app.run()
