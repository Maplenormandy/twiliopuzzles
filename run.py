from flask import Flask, request, redirect
import twilio.twiml

app = Flask(__name__)

team_names = {}

answers = {
    "1": "helloworld",
    "2": "foobar"
}

flavor_text = {
    "1": "Your mom",
    "2": "Foobaz"
}

stock_messages = {
    "Empty": "You sent an empty text!",
    "Help": "Text [PUZZLE NUMBER] [SOLUTION] and we'll let you know if you are correct!",
    "Parse Error": "I'm sorry, I cannot parse your text. Text 'help' for help.",
    "Problem Not Exists": "I'm sorry, {puzzle_number} is not a problem in this mystery hunt.",
    "Correct": "Congratulations, your answer to problem {puzzle_number}, {answer}, is correct! {flavor_text}",
    "Incorrect": "I'm sorry, your answer to problem {puzzle_number}, {answer}, is incorrect."
}

@app.route("/", methods=['GET', 'POST'])
def hello_monkey():
    """Respond and greet the caller by name."""
    
    command = request.values.get('body', None)
    print command
    
    # resp = twilio.twiml.Response()
    # resp.sms(message)
    
    # return str(resp)

if __name__ == "__main__":
    for puzzle_number, answer in answers.items():
        print(puzzle_number, stock_messages["Correct"].format(puzzle_number=puzzle_number, answer=answer, flavor_text=flavor_text[puzzle_number]).__len__())
        
    app.run(host='0.0.0.0')
