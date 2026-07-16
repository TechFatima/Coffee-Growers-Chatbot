from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)

# Store game state (for a single player demo)
game_state = {
    'target': random.randint(1, 10),
    'attempts': 0
}

@app.route('/')
def index():
    return render_template('index.html')  # This serves your beautiful UI

@app.route('/guess', methods=['POST'])
def handle_guess():
    data = request.get_json()
    guess = data.get('guess')

    # Validate input using Python
    if not isinstance(guess, int) or guess < 1 or guess > 10:
        return jsonify({'status': 'error', 'message': '⚠️ Enter a number between 1 and 10!'})

    # Python handles the game logic
    game_state['attempts'] += 1
    target = game_state['target']

    if guess == target:
        return jsonify({
            'status': 'win', 
            'message': f'🎉 WOWWW!!! Got it in {game_state["attempts"]} tries! 🎉',
            'attempts': game_state['attempts']
        })
    elif guess < target:
        return jsonify({'status': 'hint', 'message': '⬆️ Go higher...', 'attempts': game_state['attempts']})
    else:
        return jsonify({'status': 'hint', 'message': '⬇️ Go lower...', 'attempts': game_state['attempts']})

@app.route('/reset', methods=['POST'])
def reset_game():
    game_state['target'] = random.randint(1, 10)
    game_state['attempts'] = 0
    return jsonify({'status': 'reset'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
