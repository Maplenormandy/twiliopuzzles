from flask import Flask, request, redirect, Response
from pymongo import MongoClient
import twilio.twiml
import re

app = Flask(__name__)

team_names = {}

# Enter the answer to the puzzle. No whitespace allowed
answers = {
    "1": "DCCOMICS",
    "2": "MUSTERED",
    "3": "PRETTIER",
    "4": "HEADACHE",
    "5": "DECANTER",
    "6": "RANCHERO",
    "7": "CANISTER",
    "8": "CAVALIER",
    "META": "FLATLAND"
}

# Enter the flavor text given for a correct answer
storyline = (
    "Someone in customer support taped HYDRANTS to their back.",
    "For some reason, the customer kept ranting on about UPDRAFTS.",
    "The customer said someone shouted DIABOLIC right before he left.",
    "Afterwards customer mentioned MENORAHS... don't know how that got out.",
    "Someone told this one how to mess with the GRAVITON.",
    "Seems like someone intentially tampered with the TELEPATHS in this case.",
    "Suspicious though... That UPDRAFTS shouldn't happen under normal circumstances."
)

client = MongoClient()
db = client.parallelPuzzle
teams = db.teams

stock_messages = {
    "Welcome": "Welcome to the pfthi customer support team, {team_name}! Start texting us with answers [CUSTOMER NO.] [SOLUTION], like '1 wombat'",
    "Help": "Text [CUSTOMER NO.] [SOLUTION], like '1 wombat', and we'll let you know if you are correct! If you need more help, find a staff member wearing a hat",
    "Name Already Taken": "Sorry, the name '{team_name_new}' is already taken. Text 'yes' to accept the name '{team_name_temp}' or text to create a new one",
    "Name Already Taken First": "Sorry, the name '{team_name_new}' is already taken. Text to create a new one",
    "Name Too Long": "Sorry, please keep your name under 30 characters. Text 'yes' to accept the name '{team_name_temp}' or text to create a new one",
    "Name Too Long First": "Sorry, please keep your name under 30 characters. Text to create a new one",
    "Confirm Name": "Text 'yes' to accept the name '{team_name_temp}' or text to create a new one",
    "Parse Error": "I'm sorry, we didn't understand '{text}'. Please ",
    "Problem Not Exists": "We don't have a customer no. {puzzle_number}...",
    "Correct": "Thanks! With your answer {answer} we rescued customer no. {puzzle_number}! {storyline}",
    "Incorrect": "Sorry, your answer {answer} for customer no. {puzzle_number} was incorrect. Please try again.",
    "Already Answered": "We've already rescued customer no. {puzzle_number}",
    "Final Puzzle": "Hi, it's you, customer no. {puzzle_number}. {answer} was correct. Quickly, chase down a staff member with a hat and ask them for a flash drive.",
    "Meta Correct": "Congratulations, {answer} was correct! You've stopped the company's evil plot! Quickly, chase down a staff member with a hat to tell them of your success.",
    "Meta Answered": "You've already stopped the evil plot! Chase down a staff member with a hat!",
    "Meta Incorrect": "No, {answer} was wrong! Please try again."
}

special_messages = {
    "4": {
        "NINTENDO": "Sorry, NINTENDO is close but not quite right. Look at the puzzle again."
    },
    "2": {
        "MUSTARD": "Sorry, MUSTARD is close but not quite right. Look at the puzzle again."
    }
}

parse_length = len(stock_messages["Parse Error"].format(text=""))
name_length = len(stock_messages["Welcome"].format(team_name=""))
reDigits = re.compile(r"^\d+$")
reEndWhitespace = re.compile(r"\s+$")
reBeginWhitespace = re.compile(r"^\s+")
reWhitespace = re.compile(r"\s+")

def parse_error(command):
    if len(command) + parse_length < 160:
        return stock_messages["Parse Error"].format(text=command)
    else:
        return stock_messages["Parse Error"].format(text=(command[:160-parse_length-4] + " ..."))
        
def parse_puzzle_answers(team,from_number,root,leaf):
    if root in answers:
        if root in team[u'Correct']:
            return stock_messages["Already Answered"].format(puzzle_number=root)
        elif leaf == answers[root].upper():
            teams.update({"Number":from_number},{"$push":{"Correct":root}})
        
            if len(team[u'Correct']) >= 7:
                return stock_messages["Final Puzzle"].format(puzzle_number=root, answer=leaf)
            else:
                return stock_messages["Correct"].format(puzzle_number=root, answer=leaf, storyline=storyline[len(team[u'Correct'])])
        elif root in special_messages and leaf in special_messages[root]:
            return special_messages[root][leaf]
        else:
            return stock_messages["Incorrect"].format(puzzle_number=root, answer=leaf)
    else:
        return stock_messages["Problem Not Exists"].format(puzzle_number=root)

@app.route("/solved_puzzles.txt")
def show_stats():
    total_solved = [0]*10
    puzzles_solved = [0]*9
    for team in teams.find():
        for i in range(10):
            if len(team[u'Correct']) == i:
                total_solved[i] += 1
        for i in range(8):
            if str(i+1) in team[u'Correct']:
                puzzles_solved[i] += 1
        if "META" in team[u'Correct']:
            puzzles_solved[8] += 1
    
    ret = "# of Teams by total # of problems solved:\r\n"
    for i in range(10):
        ret += str(i) + ": " + str(total_solved[i]) + "\r\n"
        
    ret += "\r\n# of puzzle solves by puzzle:\r\n"
    for i in range(8):
        ret += str(i) + ": " + str(puzzles_solved[i]) + "\r\n"
        
    ret += "META: " + str(puzzles_solved[8])
    
    return Response(ret, mimetype='text/plain')

@app.route("/allteams.txt")
def show_teams():
    ret = ""
    for team in teams.find():
        ret += '"' + team[u'TempName'] + '",' + str(len(team[u'Correct'])) + "\r\n"
    return Response(ret, mimetype='text/plain')

@app.route("/", methods=['GET', 'POST'])
def hello_monkey():
    
    from_number = request.values.get('From', None)
    command = reBeginWhitespace.sub('', reEndWhitespace.sub('', request.values.get('Body', None)))
    
    tokens = command.split(None, 1)
    
    team = teams.find_one({"Number":from_number})
    
    message = parse_error(command)
    
    if team == None:
        if len(command) < 31:
            if teams.find_one({"$or":[{"Name":command}, {"TempName":command}]}) == None:
                message = stock_messages["Confirm Name"].format(team_name_temp=command)
                teams.insert({"Number":from_number,"TempName":command,"Correct":list()})
            else:
                message = stock_messages["Name Already Taken First"].format(team_name_new=command)
        else:
            message = stock_messages["Name Too Long First"]
    elif "Name" not in team:
        if tokens[0].upper() == 'YES':
            teams.update({"Number":from_number},{"$set":{"Name":team[u'TempName']}})
            message = stock_messages["Welcome"].format(team_name=team[u'TempName'])
        elif len(command) < 31:
            if teams.find_one({"$or":[{"Name":command}, {"TempName":command}]}) == None:
                teams.update({"Number":from_number},{"$set":{"TempName":command}})
                message = stock_messages["Confirm Name"].format(team_name_temp=command)
            else:
                message = stock_messages["Name Already Taken"].format(team_name_new=command,team_name_temp=team[u'TempName'])
        else:
            message = stock_messages["Name Too Long"].format(team_name_temp=team[u'TempName'])
    elif len(tokens) == 2:
        root,leaf = tokens
        if reDigits.search(root) != None:
            message = parse_puzzle_answers(team, from_number, root, reWhitespace.sub('',leaf).upper())
        elif root.upper() == "META":
            if "META" in team[u'Correct']:
                message = stock_messages["Meta Answered"]
            else:
                if reWhitespace.sub('',leaf).upper() == answers["META"].upper():
                    message = stock_messages["Meta Correct"].format(answer=reWhitespace.sub('',leaf).upper())
                    teams.update({"Number":from_number},{"$push":{"Correct":root.upper()}})
                else:
                    message = stock_messages["Meta Incorrect"].format(answer=reWhitespace.sub('',leaf).upper())
        elif root.upper() == "PENCIL-REMOVE-TEAM":
            teams.remove({"Name":leaf})
            message = "Removed " + leaf
            
    elif len(tokens) == 1:
        root = tokens[0]
        if root.upper() == "?":
            message = stock_messages["Help"]
    
    resp = twilio.twiml.Response()
    resp.sms(message)
        
    return str(resp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

    
    
    
    