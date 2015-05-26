import sys
import os
import math
import socket
from flask import Flask, render_template, request, json

# How to Use
if len(sys.argv) != 2:
    print ("How To Use:")
    print ("python hnefatafl.py board_file") #<servidor> <porta> <player>")
    sys.exit(1)

#------------------------------------------------------------------------------
# Global Variables
neighbors     = ( (-1,0), (0,-1), (1,0), (0,1) )
throne        = (6,6)
king_pos      = (6,6) 
attacker_turn = True
board         = []
corners       = ( (1,1), (1,11), (11,1), (11,11) )
adj_corners = ( (1,2), (2,1), (1,10), (2,11), (10,1), 
                (10,2), (11,10), (10,11) )

# Pieces
KING       = 'K'
SOLDIER    = 's'
KNIGHT     = 'k'
COMMANDER  = 'c'
RAIDER     = 'r'
EMPTY      = '_' 
HOSTILE_SQ = '+'

#------------------------------------------------------------------------------
# Web 
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello!\nAdd "/hnefatafl" on the URL to play Hnefatafl'
    
@app.route('/hnefatafl')
def hnefatafl():
    return render_template('board.html')

@app.route('/send_move', methods=['POST'])
def sendMove():
    data = request.get_json()

    # Somewhere on the code I swapped x and y. Gotta invert here to work
    # TODO: Fix this bullshit

    y = data["x"]
    x = data["y"]
    new_y = data["new_x"]
    new_x = data["new_y"]
    board = data["board"]

    print("received:(%d,%d) (%d,%d)" % ( x, y, new_x, new_y ) )

    print_board(board, 11, 11)

    if attacker_turn:
        print("Attackers turn:")
    else:
        print("Defenders turn:")

    add_padding(board)

    if not valid_move(board, x, y, new_x, new_y):
        print("Please enter a valid move")
        return json.dumps( { 'status':"INV_MOVE" } )

    update_board(board, x, y, new_x, new_y)

    remove_padding(board)
   
    print_board(board, 11, 11)

    attacker_turn = not attacker_turn;

    return json.dumps( { 'status':'OK', 'board':board } )

@app.route('/start', methods=['GET'])
def start():
    print ('Start Game: Sending initial board')

    f = open(sys.argv[1], "r")
    board = [ ln.strip().split() for ln in f ]

    lines = len(board)
    columns = len(board[0])

    corners = ( (1,1), (1,columns), (lines,1), (lines, columns) )

    adj_corners = ( (1,2), (2,1), (1,columns-1), (2,columns), (lines-1,1), 
                    (lines,2), (lines,columns-1), (lines-1,columns) )

    throne = ( int(math.ceil(0.5*lines)), int(math.ceil(0.5*columns)) )

    king_pos = ( throne[0], throne[1] )

    # Differentiate corners
    for i,j in ( (0, 0), (0, columns-1), (lines-1, 0), (lines-1, columns-1) ):
        board[i][j] = '+'

    print_board(board, 11, 11)

    return json.dumps(board)

#-------------------------------------------------------------------------------
# Extend Matrix on all directions by one so that edge checking is not needed
def add_padding(board):

    for i in range(0,11):
        board[i].insert(0,'_')
        board[i].insert(len(board[i]),'_')
    
    padding = ['_','_','_','_','_','_','_','_','_','_','_','_','_']
    
    board.insert(0,padding)
    
    board.insert(len(board),padding)

#-------------------------------------------------------------------------------
def remove_padding(board):
  
    board.pop()
    board.pop(0)
    
    for i in range(0,11):
        board[i].pop()
        board[i].pop(0)

#-------------------------------------------------------------------------------
def print_board(board, n, m):

    sys.stdout.write('  \t')

    for i in range(0,n):

        sys.stdout.write(str(i) + ' ')

    sys.stdout.write('\n')

    for i in range(0,m):

        sys.stdout.write(str(i) + '\t')

        for j in range(0,n):

            sys.stdout.write (board[i][j] + ' ')

        sys.stdout.write('\n')

#-------------------------------------------------------------------------------
def valid_coordinate(coordinate):

    if ( ( len(coordinate) != 2) or 
            (coordinate[0] < 1) or (coordinate[0] > 11) or 
            (coordinate[1] < 1) or (coordinate[1] > 11) ):
        
        return False
   
    return True

#-------------------------------------------------------------------------------
# TODO: Make sure that invalid inputs do not make the game crash

def get_coordinates():

    coordinate =  [ int(i) for i in input().split() ]

    while not valid_coordinate(coordinate):

        sys.stdout.write("Input Invalid\n" + 
                "Enter 2 integers between 1 and 11 separated by space\n")

        coordinate =  [ int(i) for i in input("Coordinates(X Y):").split() ]

    return coordinate

#-------------------------------------------------------------------------------
def get_move(board):

    sys.stdout.write("Type the coordinate of the piece you will move:")
    x, y = get_coordinates()
    
    sys.stdout.write("Type the new coordinate:")
    new_x, new_y = get_coordinates()

    while not valid_move(board, x, y, new_x, new_y):

        print("Please enter a valid move")

        sys.stdout.write("Type the coordinate of the piece you will move:")
        x, y = get_coordinates()
        
        sys.stdout.write("Type the new coordinate:")
        new_x, new_y = get_coordinates()

    return  ( x, y, new_x, new_y )

#-------------------------------------------------------------------------------
def king_fled(board):

    for i,j in corners:
        if board[i][j] == KING:
            return True

    return False

#-------------------------------------------------------------------------------
def king_in_throne():

    if king_pos == throne:
            return True

    return False	

#-------------------------------------------------------------------------------
def king_near_throne():

    for i,j in neighbors:

        if king_pos == ( throne[0]+i, throne[1]+j ):
            return True

    return False	

#-------------------------------------------------------------------------------
def king_near_corner():

    for c in adj_corners:
        if king_pos == c:
            return True

    return False    

#-------------------------------------------------------------------------------
def king_captured(board):

    adj = 0
    
    vert_commanders = 0
    hor_commanders  = 0

    for i,j in neighbors:

        if board[king_pos[0]+i][king_pos[1]+j] == RAIDER:
            adj+=1
    
        elif ((board[king_pos[0]+i][king_pos[1]+j] == COMMANDER) or 
                (board[king_pos[0]+i][king_pos[1]+j] == HOSTILE_SQ)):

            adj+=1

            if not( (king_pos[0]+i == throne[0]) and ([king_pos[1]+j == throne[1]]) ):

                if i == 0:
                    hor_commanders+=1
                else:
                    vert_commanders+=1

    if (adj==4):
        return True
        
    if (hor_commanders==2) or (vert_commanders==2):
        return True

    return False

#-------------------------------------------------------------------------------
def valid_move(board, x, y, new_x, new_y):

    if (x < new_x):
        x_begin = x
        x_end = new_x
    else:
        x_begin = new_x
        x_end = x
   
    if (y < new_y):
        y_begin = y
        y_end = new_y
    
    else:
        y_begin = new_y
        y_end = y
        

    if board[x][y] == EMPTY:
        print("There is no piece on the given coordinates")
        return False

    if board[new_x][new_y] != EMPTY:
        print("There is already a piece there")
        return False

    if (board[new_x][new_y] == HOSTILE_SQ) and (board[x][y] != KING):
        print("Only the King can stand on the corners!")  
        return False

    if (new_x == throne[0]) and (new_y == throne[1]) and (board[x][y] != KING):
        print("Only the King may occupy the Throne")
        return False

    if attacker_turn:
        if (board[x][y] == KING) or (board[x][y] == SOLDIER) or (board[x][y] == KNIGHT):
            print("You cannot move enemy pieces!")
            return False
    
    elif (board[x][y] == RAIDER) or (board[x][y] == COMMANDER):
        print("You cannot move enemy pieces!")
        return False

    if new_x == x:

        enemy = board[x][int( 0.5*(y+new_y) )]

        if abs(y - new_y) == 2:
            if board[x][y] == COMMANDER:
                if enemy == SOLDIER:
                    return True

            elif (board[x][y] == KNIGHT):
                if enemy == RAIDER:
                    board[x][int( 0.5*(y+new_y) )] = EMPTY
                    return True

            elif (board[x][y] == KING):
                if enemy == RAIDER and (king_in_throne() or 
                        (board[new_x][new_y] == HOSTILE_SQ) ):

                    return True

        for i in range(y_begin+1, y_end):
            if board[new_x][i] != EMPTY:
                print("There is a piece on the way")
                return False

    elif new_y == y:

        enemy = board[int( 0.5*(x+new_x) )][y]

        if abs(x - new_x) == 2:
            if board[x][y] == COMMANDER:
                if enemy == SOLDIER:
                    return True

            elif (board[x][y] == KNIGHT):
                if enemy == RAIDER:
                    board[y][int(0.5*(x+new_x) )] = EMPTY
                    return True

            elif ((board[x][y] == KING)):
                if enemy == RAIDER and (king_in_throne() or 
                        (board[new_x][new_y] == HOSTILE_SQ) ):

                    return True

        for i in range(x_begin+1, x_end):
            if board[i][new_y] != EMPTY:
                print("There are pieces on the way")
                return False

    else:
        print("The piece cannot move to this position")
        print ("Pieces move like Towers in chess")
        return False

    return True

#-------------------------------------------------------------------------------
def can_capture(board, x, y):

    for n in neighbors:
        
        i = x + n[0]
        j = y + n[1]

        while (i<12) and (i>0) and (j<12) and (j>0) and (board[i][j] == EMPTY):

            if capture(board, i, j, captured):                         
                return True

            if board[x][y] == KING:    
                for c,d in corners:
                    if (i == c) and (j == d):
                        return True

            i += n[0]
            j += n[1]

    return False
                
#-------------------------------------------------------------------------------
def capture(board, x, y, captured):

    for n in neighbors:

        i = x + n[0]
        j = y + n[1]   

        k = i + n[0]
        l = j + n[1]
        

        if attacker_turn:

            if (board[i][j] == SOLDIER) or (board[i][j] == KNIGHT):
                if ( (board[k][l] == RAIDER) or 
                        (board[k][l] == COMMANDER) or 
                        (board[k][l] == HOSTILE_SQ) ):
                    
                    captured.append( ( i, j ) )
        
        else:
             if (board[i][j] == RAIDER) or (board[i][j] == COMMANDER):     
                if ( (board[k][l] == SOLDIER) or 
                        (board [k][l] == KNIGHT) or 
                        (board[k][l] == KING) or 
                        (board[k][l] == HOSTILE_SQ) ):
                    
                    captured.append( ( i, j ) )

    return captured

#-------------------------------------------------------------------------------
def update_board(board, x, y, new_x, new_y):

    board[new_x][new_y] = board[x][y]
    board[x][y] = EMPTY

    if board[new_x][new_y] == KING:
        king_pos = (new_x, new_y)

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------
#
# Read Board From File
# f = open(sys.argv[1], "r")
#
# board = [ ln.strip().split() for ln in f ]
#
# lines = len(board)
#
# columns = len(board[0])
#
#-------------------------------------------------------------------------------
# Find out corners, corner neighbors and throne coordinates for the given board
#
# corners = ( (1,1), (1,columns), (lines,1), (lines,columns) )
#
# adj_corners = ( (1,2), (2,1), (1,columns-1), (2,columns), (lines-1,1), 
#            (lines,2), (lines,columns-1), (lines-1,columns) )
#
# throne = ( int(math.ceil(0.5*lines)), int(math.ceil(0.5*columns)) )
#
# king_pos = ( throne[0], throne[1] )
#
#-------------------------------------------------------------------------------
# Extend Matrix on all directions by one so that edge checking is not needed
#
# for i in range(0,11):
#    board[i].insert(0,'_')
#    board[i].insert(len(board[i]),'_')
#
# padding = ['_','_','_','_','_','_','_','_','_','_','_','_','_']
#
# board.insert(0,padding)
#
# board.insert(len(board),padding)
#
#-------------------------------------------------------------------------------
# Differentiate corners
#
# for i,j in corners:
#     board[i][j] = '+'
#
#-------------------------------------------------------------------------------
# Print Header
#
# sys.stdout.write('\n')                
# print("BERSERK HNEFATAFL")
# print("K = KING")
# print("s = DEFENDER'S SOLDIERS")
# print("k = KNIGHT")
# print("r = RAIDERS")
# print("k = COMMANDERS")
#
#-------------------------------------------------------------------------------
# Game Loop
#
#attacker_turn = True 
#while True:
#
#    # Differentiate throne when the king is not there
#    if board[throne[0]] [throne[1]] == EMPTY:
#        board[throne[0]] [throne[1]] = '+'
#
#    # Print Board 
#    sys.stdout.write('\n')                
#    print_board(board)
#    sys.stdout.write('\n')                
#    
#    if attacker_turn:
#        print("Attackers turn:")
#    else:
#        print("Defenders turn:")
#
#    # Move Piece
#
#    x, y, new_x, new_y = get_move(board)

#    update_board(board, x, y, new_x, new_y)

#    # Captures
#    
#    captured = []
#    captured = capture(board, new_x, new_y, captured)
#
#    while captured:
#       
#        for c in captured: 
#            board[ c[0] ][ c[1] ] = EMPTY
#
#        print_board(board)    
#        
#        print("Piece Captured!")                
#       
#        # Berserk rule 
#
#        if can_capture(board, new_x, new_y):
#            again = input("Capture again with the same piece(y/n):")
#        
#            while (again != 'y') and (again != 'n'):
#                again = input("Capture again with the same piece(y/n):")
#
#            if again == 'y':
#
#                sys.stdout.write("New Coordinate:")
#
#                x = new_x
#                y = new_y
#
#                new_x, new_y = get_coordinates()
#
#                while not valid_move(board, x, y, new_x, new_y) or not captured:
#
#                    sys.stdout.write("Please enter a valid move\nCoordinate(X Y):")
#                    new_x, new_y = get_coordinates()
#
#                    update_board(board, x, y, new_x, new_y)
#
#                    captured = capture(board, new_x, new_y)
#                
#                    # Restore previous board state
#                    board[x][y] = board[new_x][new_y]
#                    board[new_x][new_y] = EMPTY
#
#                    if board[x][y] == KING:
#                        king_pos[0] = x
#                        king_pos[1] = y
#     
#                    if not captured: 
#                        print("Invalid Move! To play again you must capture")
#                
#                update_board(board, x, y, new_x, new_y)
#
#                captured = capture(board, new_x, new_y)
#
#            else:
#                break
#
#        else: 
#            break
#
#    # Victory Conditions
#    if king_fled(board):
#        print("King Fled! Defenders Win!")
#        sys.exit(0)	
#
#    if king_captured(board):
#        print("King Captured! Raiders Win!")
#        sys.exit(0)
#
#    attacker_turn = not attacker_turn

if __name__=="__main__":

    app.run()
