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
    "Not Registered": "Register with us first by texting 'name [your team name]'.",
    "Name Already Taken": "Sorry, the name {team_name} was already taken!",
    "Cannot Rename": "Sorry, you can't rename your team.",
    "Parse Error": "I'm sorry, I didn't understand '{text}'. Text 'help' for help.",
    "Problem Not Exists": "We don't have a customer no. {puzzle_number}...",
    "Correct": "Thanks! With your answer {answer} we rescued customer no. {puzzle_number}! {storyline}",
    "Incorrect": "Sorry, your answer {answer} for customer no. {puzzle_number} was incorrect.",
    "Already Answered": "We've already rescued customer no. {puzzle_number}",
    "Final Puzzle": "Hi, it's you, customer no. {puzzle_number}. {answer} was correct. Find a person with a top hat and ask them for a flash drive. The final key is PARALLEL.",
    "Meta Correct": "Congratulations, {answer} was correct! You've stopped the company's evil plot! Hurry and find a person with a top hat to tell them of your victory.",
    "Meta Answered": "You've already stopped the evil plot! Hurry and find a person with a top hat!",
    "Meta Incorrect": "No, {answer} was wrong! It wasn't enough to stop the company's evil plot!"
}

parse_length = len(stock_messages["Parse Error"].format(text=""))
name_length = len(stock_messages["Welcome"].format(team_name=""))
taken_length = len(stock_messages["Name Already Taken"].format(team_name=""))
reDigits = re.compile(r"^\d+$")

def parse_error(command):
    if len(command) + parse_length < 160:
        return stock_messages["Parse Error"].format(text=command)
    else:
        return stock_messages["Parse Error"].format(text=(command[:160-parse_length-4] + " ..."))
def parse_name(name):
    if len(name) + name_length < 160:
        return stock_messages["Welcome"].format(team_name=name)
    else:
        return stock_messages["Welcome"].format(team_name=(name[:160-name_length-4] + " ..."))
def taken_name(name):
    if len(name) + taken_length < 160:
        return stock_messages["Name Already Taken"].format(team_name=name)
    else:
        return stock_messages["Name Already Taken"].format(team_name=(name[:160-taken_length-4] + " ..."))

@app.route("/", methods=['GET', 'POST'])
def hello_monkey():
    
    from_number = request.values.get('From', None)
    command = request.values.get('Body', None)
    
    tokens = command.split(None, 1)
    
    print "1"
    
    if len(tokens) == 2:
        root,leaf = tokens
        if reDigits.search(root) != None:
            team = teams.find_one({"Number":from_number})
            
            if team != None:
                if root in answers:
                    if root in team[u'Correct']:
                        message = stock_messages["Already Answered"].format(puzzle_number=root)
                    elif leaf.upper() == answers[root].upper():
                        if len(team[u'Correct']) >= 7:
                            message = stock_messages["Final Puzzle"].format(puzzle_number=root, answer=leaf.upper())
                        else:
                            message = stock_messages["Correct"].format(puzzle_number=root, answer=leaf.upper(), storyline=storyline[len(team[u'correct'])])
                        
                        teams.update({"Number":from_number},{"$push":{"Correct":root}})
                    else:
                        message = stock_messages["Incorrect"].format(puzzle_number=root, answer=leaf.upper())
                else:
                    message = stock_messages["Problem Not Exists"].format(puzzle_number=root)
            else:
                message = stock_messages["Not Registered"]
        elif root.upper() == "META":
            team = teams.find_one({"Number":from_number})
            
            if team != None:
                if "META" in team[u'Correct']:
                    message = stock_messages["Meta Answered"]   
                else:
                    if leaf.upper() == answers["META"].upper():
                        message = stock_messages["Meta Correct"].format(answer=leaf.upper())
                        teams.update({"Number":from_number},{"$push":{"Correct":root}})
                    else:
                        message = stock_messages["Meta Incorrect"].format(answer=leaf.upper())
            else:
                message = parse_error(command)
        elif root.upper() == "NAME":
            if teams.find_one({"Number":from_number}) == None:
                if teams.find_one({"Name":leaf}) == None:
                    teams.insert({"Number":from_number,"Name":leaf,"Correct":list()})
                    message = parse_name(leaf)
                else:
                    message = taken_name(leaf)
            else:
                message = stock_messages["Cannot Rename"]
        else:
            message = parse_error(command)
    else:
        message = parse_error(command)
    
    resp = twilio.twiml.Response()
    
    if message:
        resp.sms(message)
        
    return str(resp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

    
    
    
    