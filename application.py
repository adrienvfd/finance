import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    return render_template("index.html")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method =="POST":

        id = session['user_id']

        #Query username
        username = str(db.execute("SELECT username FROM users WHERE id=:id;", id=id)[0]['username'])
        #Query user balance
        cash = int(db.execute("SELECT cash FROM users WHERE id=:id;", id=id)[0]['cash'])
        #Retrieve Share Symbol
        symbol = request.form.get("symbol")
        #Retrieve nb of share
        shares = int(request.form.get("shares"))
        #Lookup Share
        lookedup = lookup(symbol)
        #Retrieve int of share price
        share_price = int(lookedup["price"])
        #Compute Total Price
        total_price = share_price * shares

        if not symbol:
            return apology("must provide a stock symbol", 403)

        if not lookedup:
            return apology("this stock doesn't exist", 403)

        if (cash < (total_price)):
            return apology("you're too poor", 403)

        else: #BUY THE STOCK!!!

            buy_query = "INSERT INTO txs (user_id, tx_type, share_symbol, share_price, share_price) VALUES (?, ?, ?, ?, ?)"
            db.execute(buy_query, 1, id, 'B', symbol, share_price)

            update_cash_query = "UPDATE users SET CASH = :cash WHERE id = :id"
            db.execute(update_cash_query, cash = (cash-total_price), id = id)

            return render_template("/thankyou.html", moi = username, shares = shares, symbol = symbol, total_price = usd(total_price))
    else:
        return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method =="POST":
        getquote = request.form.get("symbol")
        if not getquote:
            return apology("must provide a stock name", 403)

        getquotedict = lookup(getquote)
        if not getquotedict:
            return apology("this stock doesn't exist", 403)
        else:
            return render_template("quoted.html", name=getquotedict["name"], price=usd(getquotedict["price"]), symbol=getquotedict["symbol"])

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method =="POST":
        #Ensure Username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)
        #Check if username is free:
        elif db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username")):
            return apology("username already exists", 403)
        # Ensure Password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        #Add new user in database
        else:
            passHash = generate_password_hash(request.form.get("password"))
            username = request.form.get("username")
            register_query = "INSERT INTO users (username, hash) VALUES (?, ?)"
            db.execute(register_query, username, passHash)
            return render_template("login.html")

    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
