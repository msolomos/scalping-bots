from flask import Flask, jsonify, request

app = Flask(__name__)

# Η τιμή που θα δίνεται ως απόκριση
mock_price = 1500  # Μπορείς να αλλάξεις την τιμή αυτή όποτε θέλεις

@app.route('/price', methods=['GET'])
def get_price():
    return jsonify({'price': mock_price})

# Endpoint για να αλλάξεις την τιμή χειροκίνητα
@app.route('/set_price', methods=['POST'])
def set_price():
    global mock_price
    new_price = request.json.get('price')
    if new_price is not None:
        mock_price = new_price
        return jsonify({'message': 'Price updated', 'new_price': mock_price}), 200
    return jsonify({'message': 'Invalid price'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5015)
