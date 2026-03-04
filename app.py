from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({"message": "Hello from Flask!", "status": "success"})


@app.route("/health") 
def health():
    return jsonify({"status": "healthy"})
 #hello my name is kalcus

if __name__ == "__main__":
    app.run(debug=True)
