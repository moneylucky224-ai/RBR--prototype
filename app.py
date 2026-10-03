import os, sqlite3, time, datetime as dt
from flask import Flask, request, redirect, session, g, render_template, flash
from jinja2 import DictLoader
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from templates_data import T, LOGO, GRAD, ICON, icon

app = Flask(__name__); app.secret_key = "rbr-secret"; app.jinja_loader = DictLoader(T)
UP = os.path.join(app.root_path, "static", "uploads"); DB = os.path.join(app.root_path, "rbr.db"); os.makedirs(UP, exist_ok=True)
CATS = ["Electrical Appliances", "Books", "Drafters", "Dresses", "Jewellery", "Handmade/Creative", "Other"]
CHECKS = ["Powers on properly", "No exposed wires / damage", "All functions work", "Plug & cable are safe"]
CAUTIONS = ["Meet in a public campus place (library, canteen).", "Test the item before taking it.", "Agree on days and return date in chat.",
            "Owner takes your photo at handover.", "Not returning = posted as suspect + campus police informed."]
SEED = {  # title, brand, bought, rent per day
"Electrical Appliances": [("Casio fx-991EX Calculator","Casio","2025-06-10",5),("HP Pavilion Laptop","HP","2024-08-20",120),("Laptop Adapter 65W","Dell","2025-01-15",15),("Steam Iron","Philips","2025-03-05",10),("Bluetooth Speaker","boAt","2025-02-12",20)],
"Books": [("Higher Engineering Mathematics","B.S. Grewal","2025-07-01",3),("Concepts of Physics","H.C. Verma","2024-12-10",3),("Let Us C","Y. Kanetkar","2025-08-02",3),("Engineering Drawing","N.D. Bhatt","2025-06-18",4),("Basic Electrical Engineering","V.K. Mehta","2025-07-22",3)],
"Drafters": [("Mini Drafter","Omega","2025-06-12",8),("Geometry Box","Camlin","2025-07-03",4),("T-Square 60cm","Faber-Castell","2025-06-20",5),("Drawing Board A3","Classmate","2025-05-25",10),("Compass Set","Staedtler","2025-08-08",5)],
"Dresses": [("White Lab Coat","Raymond","2025-07-15",8),("Silk Saree","Fabindia","2024-11-02",40),("Kurta Set","Biba","2025-01-20",25),("Formal Blazer","Van Heusen","2025-02-14",35),("Sherwani","Manyavar","2024-10-12",80)],
"Jewellery": [("Jhumka Earrings","Zaveri Pearls","2025-01-09",15),("Pearl Necklace","Giva","2024-12-22",25),("Bangle Set","Voylla","2025-03-17",15),("Maang Tikka","Tanishq","2024-09-30",30),("Oxidised Silver Set","Voylla","2025-04-04",20)],
"Handmade/Creative": [("Hand-painted Canvas","Handmade","2025-08-01",15),("Crochet Bag","Handmade","2025-07-11",10),("Resin Keychain Set","Handmade","2025-06-27",5),("Scented Candle Set","Handmade","2025-08-19",8),("Macrame Wall Hanging","Handmade","2025-05-30",12)],
"Other": [("Cricket Bat","SG","2025-02-01",15),("Trekking Backpack","Wildcraft","2025-01-12",20),("Badminton Racket","Yonex","2025-03-09",10),("Yoga Mat","Decathlon","2025-04-15",5),("Camping Tent","Quechua","2024-11-25",50)]}

def db():
    if "db" not in g: g.db = sqlite3.connect(DB); g.db.row_factory = sqlite3.Row
    return g.db
@app.teardown_appcontext
def close(e):
    d = g.pop("db", None)
    if d: d.close()
def q(sql, a=(), one=False):
    c = db().execute(sql, a); db().commit(); r = c.fetchall()
    return (r[0] if r else None) if one else r
def save(f):
    if not f or not f.filename: return ""
    n = f"{int(time.time()*1000)}_{secure_filename(f.filename)}"; f.save(os.path.join(UP, n)); return n
def me(): return q("select * from users where id=?", (session.get("uid"),), True) if "uid" in session else None
def dd(rows):
    t = dt.date.today(); out = []
    for r in rows:
        d = dict(r); d["left"] = (dt.date.fromisoformat(d["due"]) - t).days if d.get("due") else None; out.append(d)
    return out
app.jinja_env.globals.update(me=me, CATS=CATS, ICON=ICON, GRAD=GRAD, icon=icon, LOGO=LOGO, CHECKS=CHECKS, CAUTIONS=CAUTIONS)

def init():
    c = sqlite3.connect(DB)
    c.executescript("""
create table if not exists users(id integer primary key, name,phone,email unique,pw,gender,year,location,id_file,id_status,photo);
create table if not exists items(id integer primary key, owner int,title,cat,brand,bought_on,cond,price int,avail,descr,video,available int default 1,created);
create table if not exists reqs(id integer primary key, item int,client int,mode,status default 'pending',days int,due,handover_photo,received_at,closed int default 0,review_prompt int default 0,created);
create table if not exists msgs(id integer primary key, req int,sender int,body,ts);
create table if not exists reviews(id integer primary key, req int,rating int,text);
create table if not exists complaints(id integer primary key, req int,text,ts);
create table if not exists missing(id integer primary key, user int,title,descr,place,photo,ts);""")
    if not c.execute("select count(*) from items").fetchone()[0]:   # sample data
        pw = generate_password_hash("demo123"); today = time.strftime("%Y-%m-%d")
        for n, nm in enumerate(["Aarav", "Diya", "Kiran", "Meena"], 1):
            c.execute("insert into users(name,phone,email,pw,gender,year,id_status) values(?,?,?,?,?,?,?)", (nm + " (demo)", "90000000%02d" % n, f"demo{n}@rbr.in", pw, "-", "2nd year", "Demo user"))
        k = 0
        for cat, rows in SEED.items():
            for j, (t, b, d, p) in enumerate(rows):
                o = k % 4 + 1; av = ["both", "both", "rent", "both", "borrow"][j]
                cur = c.execute("insert into items(owner,title,cat,brand,bought_on,cond,price,avail,descr,created) values(?,?,?,?,?,?,?,?,?,?)", (o, t, cat, b, d, "Used (2nd hand)" if j % 2 else "Like new", p, av, f"Well-maintained {t}. Please handle with care and return on time.", today))
                iid = cur.lastrowid
                for u in [x for x in range(1, 5) if x != o][:(k * 5 + 2) % 4]:
                    c.execute("insert into reqs(item,client,mode,created) values(?,?,?,?)", (iid, u, "borrow" if av == "borrow" else "rent", today))
                k += 1
    c.commit(); c.close()
init()

@app.before_request
def gate():
    if request.endpoint in ("login", "register", "static"): return
    if not me(): return redirect("/login")
@app.context_processor
def ctx():
    u = me()
    if not u: return {}
    rem = [r for r in dd(q("select r.*,i.title,o.name oname from reqs r join items i on i.id=r.item join users o on o.id=i.owner where r.client=? and r.status='active'", (u["id"],))) if r["left"] <= 1]
    rev = q("select r.id,i.title from reqs r join items i on i.id=r.item where r.client=? and r.closed=1 and r.review_prompt=1 limit 1", (u["id"],), True)
    return dict(rem=rem, rev=rev)

def ocr_id(path):
    try:
        import pytesseract; from PIL import Image
        t = pytesseract.image_to_string(Image.open(path)).lower()
        return "Verified: college ID detected" if any(k in t for k in ["college", "university", "student", "institute", "id card", "roll"]) else "Rejected: not a college ID"
    except Exception: return "Pending: admin review (OCR not installed)"

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form; idf = save(request.files.get("idproof"))
        if not idf: flash("College ID upload is required."); return redirect("/register")
        try:
            q("insert into users(name,phone,email,pw,gender,year,location,id_file,id_status) values(?,?,?,?,?,?,?,?,?)", (f["name"], f["phone"], f["email"], generate_password_hash(f["pw"]), f["gender"], f["year"], f.get("location", ""), idf, ocr_id(os.path.join(UP, idf))))
        except sqlite3.IntegrityError: flash("Email already registered."); return redirect("/register")
        u = q("select * from users where email=?", (f["email"],), True)
        if u["id_status"].startswith("Rejected"): flash("This is not a college ID. Upload a clear college ID."); return redirect("/register")
        session["uid"] = u["id"]; flash("Welcome to RBR, " + u["name"] + "!"); return redirect("/")
    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = q("select * from users where email=?", (request.form["email"],), True)
        if u and check_password_hash(u["pw"], request.form["pw"]): session["uid"] = u["id"]; return redirect("/")
        flash("Wrong email or password.")
    return render_template("login.html")
@app.route("/logout")
def logout(): session.clear(); return redirect("/login")
@app.route("/help")
def help_(): return render_template("help.html")

@app.route("/")
def home():
    s, c = request.args.get("q", ""), request.args.get("cat", "")
    items = q("select i.*,u.name oname,(select count(distinct client) from reqs where item=i.id) rc from items i join users u on u.id=i.owner where i.available=1 and (i.title like ? or i.brand like ? or i.descr like ?) and (?='' or i.cat=?) order by i.id desc", (f"%{s}%", f"%{s}%", f"%{s}%", c, c))
    return render_template("home.html", items=items, s=s, c=c)
@app.route("/item/<int:i>")
def item(i):
    it = q("select i.*,u.name oname from items i join users u on u.id=i.owner where i.id=?", (i,), True)
    if not it: return redirect("/")
    rc = q("select count(distinct client) c from reqs where item=?", (i,), True)["c"]
    rv = q("select avg(rv.rating) a,count(*) n from reviews rv join reqs r on r.id=rv.req where r.item=?", (i,), True)
    return render_template("item.html", it=it, rc=rc, rv=rv)
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        f = request.form
        if f["cat"] == "Electrical Appliances" and len(f.getlist("chk")) < len(CHECKS): flash("Electrical items must pass ALL working checks before listing."); return redirect("/add")
        q("insert into items(owner,title,cat,brand,bought_on,cond,price,avail,descr,video,created) values(?,?,?,?,?,?,?,?,?,?,?)", (me()["id"], f["title"], f["cat"], f["brand"], f["bought_on"], f["cond"], f["price"], f["avail"], f["descr"], save(request.files.get("video")), time.strftime("%Y-%m-%d")))
        flash("Item published on RBR!"); return redirect("/")
    return render_template("add.html")
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        p = save(request.files.get("photo"))
        if p: q("update users set photo=? where id=?", (p, me()["id"]))
        return redirect("/profile")
    return render_template("profile.html", mine=q("select * from items where owner=? order by id desc", (me()["id"],)))

@app.route("/request/<int:i>", methods=["POST"])
def make_req(i):
    it = q("select * from items where id=?", (i,), True); m = request.form["mode"]; u = me()["id"]
    if not it or it["owner"] == u or not it["available"] or it["avail"] not in ("both", m): return redirect("/")
    if q("select 1 from reqs where item=? and client=? and status in ('pending','accepted','active')", (i, u), True): flash("You already have a request for this item."); return redirect(f"/item/{i}")
    q("insert into reqs(item,client,mode,created) values(?,?,?,?)", (i, u, m, time.strftime("%Y-%m-%d"))); flash(f"{m.title()} request sent!"); return redirect(f"/dash/{m}")
@app.route("/dash/<mode>")
def dash(mode):
    if mode not in ("rent", "borrow"): return redirect("/")
    u = me()["id"]
    got = dd(q("select r.*,i.title,i.price,c.name cname from reqs r join items i on i.id=r.item join users c on c.id=r.client where i.owner=? and r.mode=? order by r.id desc", (u, mode)))
    mine = dd(q("select r.*,i.title,i.brand,i.price,o.name oname from reqs r join items i on i.id=r.item join users o on o.id=i.owner where r.client=? and r.mode=? order by r.id desc", (u, mode)))
    return render_template("dash.html", mode=mode, got=got, mine=mine)
def owned(r): return q("select r.*,i.owner,i.title from reqs r join items i on i.id=r.item where r.id=?", (r,), True)
@app.route("/accept/<int:r>", methods=["POST"])
def accept(r):
    rq = owned(r)
    if rq and rq["owner"] == me()["id"] and rq["status"] == "pending": q("update reqs set status='accepted' where id=?", (r,)); flash("Accepted! The client must now enter the number of days.")
    return redirect(f"/dash/{rq['mode']}")
@app.route("/decline/<int:r>", methods=["POST"])
def decline(r):
    rq = owned(r)
    if rq and rq["owner"] == me()["id"] and rq["status"] == "pending": q("update reqs set status='declined' where id=?", (r,))
    return redirect(f"/dash/{rq['mode']}")
@app.route("/days/<int:r>", methods=["POST"])
def days(r):
    rq = owned(r); mx = 7 if rq["mode"] == "borrow" else 30
    if rq["client"] != me()["id"] or rq["status"] != "accepted": return redirect("/")
    n = max(1, min(mx, int(request.form["days"]))); due = (dt.date.today() + dt.timedelta(days=n)).isoformat()
    q("update reqs set days=?,due=?,status='active' where id=?", (n, due, r)); q("update items set available=0 where id=?", (rq["item"],))
    q("update reqs set status='declined' where item=? and status in ('pending','accepted') and id!=?", (rq["item"], r))
    q("insert into msgs(req,sender,body,ts) values(?,?,?,?)", (r, me()["id"], f"Hi! I will use {rq['title']} for {n} day(s). I will return it by {due}.", time.strftime("%H:%M")))
    flash("Chat opened. Return the item before the deadline!"); return redirect(f"/chat/{r}")
@app.route("/chat/<int:r>", methods=["GET", "POST"])
def chat(r):
    rq = q("select r.*,i.title,i.owner,o.name oname,c.name cname from reqs r join items i on i.id=r.item join users o on o.id=i.owner join users c on c.id=r.client where r.id=?", (r,), True)
    if not rq or me()["id"] not in (rq["owner"], rq["client"]) or rq["status"] not in ("active", "closed"): return redirect("/")
    if request.method == "POST" and not rq["closed"]:
        if request.form.get("body"): q("insert into msgs(req,sender,body,ts) values(?,?,?,?)", (r, me()["id"], request.form["body"], time.strftime("%H:%M")))
        p = save(request.files.get("handover"))
        if p and me()["id"] == rq["owner"]: q("update reqs set handover_photo=? where id=?", (p, r))
        return redirect(f"/chat/{r}")
    return render_template("chat.html", rq=rq, ms=q("select m.*,u.name from msgs m join users u on u.id=m.sender where req=? order by m.id", (r,)))
@app.route("/received/<int:r>", methods=["POST"])
def received(r):
    rq = owned(r)
    if rq and rq["owner"] == me()["id"] and rq["status"] == "active":
        q("update reqs set status='closed',closed=1,received_at=?,review_prompt=1 where id=?", (time.strftime("%Y-%m-%d %H:%M"), r)); q("update items set available=1 where id=?", (rq["item"],))
        flash("Item received - it is visible on RBR again. The renter will be asked for a review.")
    return redirect(f"/dash/{rq['mode']}")
@app.route("/review/<int:r>", methods=["POST"])
def review(r):
    q("insert into reviews(req,rating,text) values(?,?,?)", (r, request.form["rating"], request.form["text"])); q("update reqs set review_prompt=0 where id=? and client=?", (r, me()["id"])); flash("Thanks for your review!"); return redirect("/")
@app.route("/review/<int:r>/skip", methods=["POST"])
def skip(r): q("update reqs set review_prompt=0 where id=? and client=?", (r, me()["id"])); return redirect("/")

@app.route("/complaints", methods=["GET", "POST"])
def complaints():
    if request.method == "POST":
        q("insert into complaints(req,text,ts) values(?,?,?)", (request.form["req"], request.form["text"], time.strftime("%Y-%m-%d"))); flash("Posted publicly. Campus police station notified (demo)."); return redirect("/complaints")
    mine = q("select r.id,i.title from reqs r join items i on i.id=r.item where i.owner=? and r.status='active'", (me()["id"],))
    cs = q("select c.*,r.handover_photo,i.title,u.name suspect,u.phone from complaints c join reqs r on r.id=c.req join items i on i.id=r.item join users u on u.id=r.client order by c.id desc")
    return render_template("complaints.html", cs=cs, mine=mine)
@app.route("/missing", methods=["GET", "POST"])
def missing():
    if request.method == "POST":
        q("insert into missing(user,title,descr,place,photo,ts) values(?,?,?,?,?,?)", (me()["id"], request.form["title"], request.form["descr"], request.form["place"], save(request.files.get("photo")), time.strftime("%Y-%m-%d"))); return redirect("/missing")
    s = request.args.get("q", "")
    return render_template("missing.html", ms=q("select m.*,u.name,u.phone from missing m join users u on u.id=m.user where m.title like ? or m.descr like ? order by m.id desc", (f"%{s}%", f"%{s}%")), s=s)

if __name__ == "__main__": app.run(debug=True)
