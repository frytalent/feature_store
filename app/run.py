import flask

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    return "<h1>api home</h1>"

if __name__ == '__main__':
    app.run()
    #app.run(host="0.0.0.0", port=5000, debug=True)
