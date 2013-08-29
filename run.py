from flask import Flask, request, redirect
import twilio.twiml
import re

app = Flask(__name__)

team_names = {}

# Enter the answer to the puzzle. No whitespace allowed
answers = {
    "1": "helloworld",
    "2": "foobar"
}

# Enter the flavor text given for a correct answer
flavor_text = {
    "1": "Your mom",
    "2": "Foobaz"
}

stock_messages = {
    "Empty": "You sent an empty text!",
    "Help": "Text [PUZZLE NUMBER] [SOLUTION] and we'll let you know if you are correct!",
    "Parse Error": "I'm sorry, I cannot parse your text '{text}'. Text 'help' for help.",
    "Problem Not Exists": "I'm sorry, {puzzle_number} is not a problem in this mystery hunt.",
    "Correct": "Congratulations, your answer to problem {puzzle_number}, {answer}, is correct! {flavor_text}",
    "Incorrect": "I'm sorry, your answer to problem {puzzle_number}, {answer}, is incorrect."
}

parse_length = len(stock_messages["Parse Error"].format(text=""))
reDigits = re.compile(r"^\d+$")

def parse_error(command):
    if len(command) + parse_length < 160:
        return stock_messages["Parse Error"].format(text=command)
    else:
        return stock_messages["Parse Error"].format(text=command[:160-parse_length-4]) + " ..."

@app.route("/", methods=['GET', 'POST'])
def hello_monkey():
    """Respond and greet the caller by name."""
    
    from_number = request.values.get('From', None)
    command = request.values.get('Body', None)
    
    tokens = command.upper().split(None, 1)
    
    if len(tokens) == 2:
        root,leaf = tokens
        if reDigits.search(root) != None:
            if root in answers:
                if leaf == answers[root]:
                    message = stock_messages["Correct"].format(puzzle_number=root, answer=leaf, flavor_text=flavor_text[puzzle_number])
                else:
                    message = stock_messages["Incorrect"].format(puzzle_number=root, answer=leaf)
            else:
                message = stock_messages["Problem Not Exists"].format(puzzle_number=root)
        else:
            message = parse_error(command)
    elif len(tokens) == 1:
        if root == "HELP":
            message = stock_messages["Help"]
        else:
            message = parse_error(command)
    else:
        message = stock_messages["Empty"]
    
    resp = twilio.twiml.Response()
    resp.sms(message)
    
    return str(resp)

if __name__ == "__main__":
    for puzzle_number, answer in answers.items():
        print(puzzle_number, len(stock_messages["Correct"].format(puzzle_number=puzzle_number, answer=answer, flavor_text=flavor_text[puzzle_number])))
        
    app.run(host='0.0.0.0')
