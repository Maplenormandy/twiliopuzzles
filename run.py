from flask import Flask, request, redirect
from pymongo import MongoClient
import twilio.twiml
import re

app = Flask(__name__)

team_names = {}

# Enter the answer to the puzzle. No whitespace allowed
answers = {
    "1": "DCCOMICS",
    "2": "MUSTERED",
    "3": "FORFEITS",
    "4": "HEADACHE",
    "5": "DECANTER",
    "6": "GARDENER",
    "7": "CANISTER",
    "8": "CAVALIER",
    "META": "FLATLAND"
}

# Enter the flavor text given for a correct answer
storyline = (
    "Someone in customer support taped STRAIGHT to their back.",
    "For some reason, the customer kept ranting on about MACHINES.",
    "The customer said someone shouted WORMHOLE right before he left.",
    "Afterwards customer mentioned DARKFLOW... don't know how that got out.",
    "Someone told this one how to mess with the ASSEMBLY.",
    "Seems like someone intentially tampered with the ANTIMASS in this case.",
    "Suspicious though... That SEGFAULT shouldn't happen under normal circumstances."
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
    "Parse Error": "I'm sorry, we didn't understand '{text}'. Text 'help' for help.",
    "Problem Not Exists": "We don't have a customer no. {puzzle_number}...",
    "Correct": "Thanks! With your answer {answer} we rescued customer no. {puzzle_number}! {storyline}",
    "Incorrect": "Sorry, your answer {answer} for customer no. {puzzle_number} was incorrect. Please try again.",
    "Already Answered": "We've already rescued customer no. {puzzle_number}",
    "Final Puzzle": "Hi, it's you, customer no. {puzzle_number}. {answer} was correct. Quickly, chase down a staff member with a hat and ask them for a flash drive. The final key is PARALLEL.",
    "Meta Correct": "Congratulations, {answer} was correct! You've stopped the company's evil plot! Quickly, chase down a staff member with a hat to tell them of your success.",
    "Meta Answered": "You've already stopped the evil plot! Chase down a staff member with a hat!",
    "Meta Incorrect": "No, {answer} was wrong! Please try again."
}

parse_length = len(stock_messages["Parse Error"].format(text=""))
name_length = len(stock_messages["Welcome"].format(team_name=""))
reDigits = re.compile(r"^\d+$")

def parse_error(command):
    if len(command) + parse_length < 160:
        return stock_messages["Parse Error"].format(text=command)
    else:
        return stock_messages["Parse Error"].format(text=(command[:160-parse_length-4] + " ..."))
        
def parse_puzzle_answers(root,leaf):
    if root in answers:
        if root in team[u'Correct']:
            return stock_messages["Already Answered"].format(puzzle_number=root)
        elif leaf.upper() == answers[root].upper():
            teams.update({"Number":from_number},{"$push":{"Correct":root}})
        
            if len(team[u'Correct']) >= 7:
                return stock_messages["Final Puzzle"].format(puzzle_number=root, answer=leaf.upper())
            else:
                return stock_messages["Correct"].format(puzzle_number=root, answer=leaf.upper(), storyline=storyline[len(team[u'Correct'])])
        else:
            return stock_messages["Incorrect"].format(puzzle_number=root, answer=leaf.upper())
    else:
        return stock_messages["Problem Not Exists"].format(puzzle_number=root)

@app.route("/", methods=['GET', 'POST'])
def hello_monkey():
    
    from_number = request.values.get('From', None)
    command = request.values.get('Body', None)
    
    tokens = command.split(None, 1)
    
    team = teams.find_one({"Number":from_number})
    
    if team == None:
        if len(command) < 31:
            if teams.find_one({"$or":{"Name":command, "TempName":command}}) == None:
                message = stock_messages["Confirm Name"].format(team_name_temp=command)
                teams.insert({"Number":from_number,"TempName":command,"Correct":list()})
            else:
                message = stock_messages["Name Already Taken First"].format(team_name_new=command)
        else:
            message = stock_messages["Name Too Long First"]
    elif "Name" not in team:
        if command.upper() == 'YES':
            teams.update({"Number":from_number},{"Name":team[u'TempName']})
            message = stock_messages["Welcome"].format(team_name=team[u'TempName'])
        elif len(command) < 31:
            if teams.find_one({"$or":{"Name":command, "TempName":command}}) == None:
                teams.update({"Number":from_number},{"TempName":command})
                message = stock_messages["Confirm Name"].format(team_name_temp=command)
            else:
                message = stock_messages["Name Already Taken"].format(team_name_new=command,team_name_temp=team[u'TempName'])
        else:
            message = stock_messages["Name Too Long"].format(team_name_temp=team[u'TempName'])
    elif len(tokens) == 2:
        root,leaf = tokens
        if reDigits.search(root) != None:
            message = parse_puzzle_answers(root, leaf)
        elif root.upper() == "META":
            if "META" in team[u'Correct']:
                message = stock_messages["Meta Answered"]   
            else:
                if leaf.upper() == answers["META"].upper():
                    message = stock_messages["Meta Correct"].format(answer=leaf.upper())
                    teams.update({"Number":from_number},{"$push":{"Correct":root}})
                else:
                    message = stock_messages["Meta Incorrect"].format(answer=leaf.upper())
        elif root.upper() == "PENCIL-REMOVE-TEAM":
            teams.remove({"Name":leaf})
            message = "Removed " + leaf
            
    elif len(tokens) == 1:
        root = tokens[0]
        if root.upper() == "HELP":
            message = stock_messages["Help"]
    
    if message == None:
        message = parse_error(command)
    
    resp = twilio.twiml.Response()
    resp.sms(message)
        
    return str(resp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

    
    
    
    