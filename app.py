from flask import Flask

app = Flask(_name_)

@app.route("/")
def home():
  return "GMT AI QA is running"

if _name_ == "_main_":
  app.run()
