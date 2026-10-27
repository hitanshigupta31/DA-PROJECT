import os, secrets, string
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, extract
from sqlalchemy.orm import aliased
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
load_dotenv(HERE / ".env")
app = Flask(__name__, static_folder=None)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "development-only-change-me"),
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/fairshare_db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
    SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "false").lower() == "true",
)
db = SQLAlchemy(app)
CENT = Decimal("0.01")
CATEGORIES = {"Food","Transport","Accommodation","Shopping","Utilities","Entertainment","Other"}

class User(db.Model):
    __tablename__="users"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(255),unique=True,nullable=False,index=True)
    password_hash=db.Column(db.String(255),nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

class Group(db.Model):
    __tablename__="groups"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(120),nullable=False)
    description=db.Column(db.String(500))
    invite_code=db.Column(db.String(16),unique=True,nullable=False,index=True)
    created_by=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)

class GroupMember(db.Model):
    __tablename__="group_members"
    id=db.Column(db.Integer,primary_key=True)
    group_id=db.Column(db.Integer,db.ForeignKey("groups.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    role=db.Column(db.String(20),default="member",nullable=False)
    joined_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    __table_args__=(db.UniqueConstraint("group_id","user_id",name="uq_group_user"),)

class Expense(db.Model):
    __tablename__="expenses"
    id=db.Column(db.Integer,primary_key=True)
    group_id=db.Column(db.Integer,db.ForeignKey("groups.id",ondelete="CASCADE"),nullable=False)
    paid_by=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    title=db.Column(db.String(160),nullable=False)
    amount=db.Column(db.Numeric(12,2),nullable=False)
    category=db.Column(db.String(50),nullable=False,default="Other")
    expense_date=db.Column(db.Date,nullable=False,default=date.today)
    notes=db.Column(db.String(500))

class ExpenseSplit(db.Model):
    __tablename__="expense_splits"
    id=db.Column(db.Integer,primary_key=True)
    expense_id=db.Column(db.Integer,db.ForeignKey("expenses.id",ondelete="CASCADE"),nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    share_amount=db.Column(db.Numeric(12,2),nullable=False)
    __table_args__=(db.UniqueConstraint("expense_id","user_id",name="uq_expense_user"),)

class Settlement(db.Model):
    __tablename__="settlements"
    id=db.Column(db.Integer,primary_key=True)
    group_id=db.Column(db.Integer,db.ForeignKey("groups.id",ondelete="CASCADE"),nullable=False)
    paid_by=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    paid_to=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    amount=db.Column(db.Numeric(12,2),nullable=False)
    settlement_date=db.Column(db.Date,nullable=False,default=date.today)
    note=db.Column(db.String(300))

class GroupBudget(db.Model):
    __tablename__="group_budgets"
    id=db.Column(db.Integer,primary_key=True)
    group_id=db.Column(db.Integer,db.ForeignKey("groups.id",ondelete="CASCADE"),nullable=False,unique=True)
    monthly_limit=db.Column(db.Numeric(12,2),nullable=False)
    updated_by=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    updated_at=db.Column(db.DateTime,default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False)

class ActivityLog(db.Model):
    __tablename__="activity_logs"
    id=db.Column(db.Integer,primary_key=True)
    group_id=db.Column(db.Integer,db.ForeignKey("groups.id",ondelete="CASCADE"),nullable=False,index=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    action=db.Column(db.String(80),nullable=False)
    details=db.Column(db.String(500),nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow,nullable=False,index=True)

def log_activity(gid, uid, action, details):
    db.session.add(ActivityLog(group_id=gid,user_id=uid,action=action,details=details[:500]))

def dec(v): return Decimal(str(v)).quantize(CENT)
def m(v): return f"{dec(v):.2f}"
def err(message,status=400): return jsonify(error=message),status
def current(): return db.session.get(User,session.get("user_id")) if session.get("user_id") else None
def auth(fn):
    @wraps(fn)
    def wrapped(*a,**kw):
        if not session.get("user_id"): return err("Please log in to continue.",401)
        return fn(*a,**kw)
    return wrapped
def member(gid,uid): return GroupMember.query.filter_by(group_id=gid,user_id=uid).first()
def allowed(gid,uid): return db.session.get(Group,gid) if member(gid,uid) else None
def user_dict(u): return {"id":u.id,"name":u.name,"email":u.email}
def group_dict(g,count=None):
    d={"id":g.id,"name":g.name,"description":g.description or "","invite_code":g.invite_code,"created_by":g.created_by}
    if count is not None:d["member_count"]=count
    return d
def expense_dict(e,payer=None):
    splits=ExpenseSplit.query.filter_by(expense_id=e.id).all()
    return {"id":e.id,"group_id":e.group_id,"paid_by":e.paid_by,"payer_name":payer,"title":e.title,"amount":m(e.amount),"category":e.category,"expense_date":e.expense_date.isoformat(),"notes":e.notes or "","splits":[{"user_id":x.user_id,"share_amount":m(x.share_amount)} for x in splits]}
def balances_for(gid):
    vals={x.user_id:Decimal("0.00") for x in GroupMember.query.filter_by(group_id=gid).all()}
    for e in Expense.query.filter_by(group_id=gid).all():
        vals[e.paid_by]=vals.get(e.paid_by,Decimal("0.00"))+dec(e.amount)
        for s in ExpenseSplit.query.filter_by(expense_id=e.id).all():
            vals[s.user_id]=vals.get(s.user_id,Decimal("0.00"))-dec(s.share_amount)
    for s in Settlement.query.filter_by(group_id=gid).all():
        vals[s.paid_by]=vals.get(s.paid_by,Decimal("0.00"))+dec(s.amount)
        vals[s.paid_to]=vals.get(s.paid_to,Decimal("0.00"))-dec(s.amount)
    return vals
def suggestions(gid):
    vals=balances_for(gid)
    debtors=sorted([{"id":u,"v":-v} for u,v in vals.items() if v<0],key=lambda x:x["v"],reverse=True)
    creditors=sorted([{"id":u,"v":v} for u,v in vals.items() if v>0],key=lambda x:x["v"],reverse=True)
    out=[];i=j=0
    while i<len(debtors) and j<len(creditors):
        amt=min(debtors[i]["v"],creditors[j]["v"])
        out.append({"paid_by":debtors[i]["id"],"paid_to":creditors[j]["id"],"amount":m(amt)})
        debtors[i]["v"]-=amt;creditors[j]["v"]-=amt
        if debtors[i]["v"]==0:i+=1
        if creditors[j]["v"]==0:j+=1
    return out

@app.get("/")
def home(): return send_from_directory(ROOT/"frontend","index.html")
@app.get("/<path:path>")
def static(path):
    target=(ROOT/"frontend"/path).resolve()
    if (ROOT/"frontend").resolve() in target.parents and target.is_file(): return send_from_directory(ROOT/"frontend",path)
    return send_from_directory(ROOT/"frontend","index.html")
@app.get("/api/health")
def health():
    try: db.session.execute(db.text("SELECT 1")); return jsonify(status="ok",database="connected")
    except Exception: db.session.rollback(); return err("Database connection failed. Check MySQL and backend/.env.",503)

@app.post("/api/auth/register")
def register():
    d=request.get_json(silent=True) or {};name=str(d.get("name","")).strip();email=str(d.get("email","")).strip().lower();pw=str(d.get("password",""))
    if not 2<=len(name)<=100:return err("Name must be 2–100 characters.")
    if "@" not in email or len(email)>255:return err("Enter a valid email.")
    if len(pw)<8:return err("Password must be at least 8 characters.")
    if User.query.filter(func.lower(User.email)==email).first():return err("Email already registered.",409)
    u=User(name=name,email=email,password_hash=generate_password_hash(pw));db.session.add(u)
    try:db.session.commit()
    except IntegrityError:db.session.rollback();return err("Email already registered.",409)
    session.clear();session["user_id"]=u.id
    return jsonify(user=user_dict(u)),201
@app.post("/api/auth/login")
def login():
    d=request.get_json(silent=True) or {};u=User.query.filter(func.lower(User.email)==str(d.get("email","")).strip().lower()).first()
    if not u or not check_password_hash(u.password_hash,str(d.get("password",""))):return err("Incorrect email or password.",401)
    session.clear();session["user_id"]=u.id;return jsonify(user=user_dict(u))
@app.post("/api/auth/logout")
def logout():session.clear();return jsonify(message="Logged out.")
@app.get("/api/auth/me")
def me():return jsonify(user=user_dict(current()) if current() else None)

@app.get("/api/groups")
@auth
def groups():
    rows=db.session.query(Group,func.count(GroupMember.id)).join(GroupMember,GroupMember.group_id==Group.id).filter(GroupMember.user_id==session["user_id"]).group_by(Group.id).order_by(Group.created_at.desc()).all()
    return jsonify(groups=[group_dict(g,n) for g,n in rows])
@app.post("/api/groups")
@auth
def create_group():
    d=request.get_json(silent=True) or {};name=str(d.get("name","")).strip();desc=str(d.get("description","")).strip()
    if not name or len(name)>120:return err("Group name is required (maximum 120 characters).")
    code="".join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(8))
    while Group.query.filter_by(invite_code=code).first():code="".join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(8))
    g=Group(name=name,description=desc or None,invite_code=code,created_by=session["user_id"]);db.session.add(g);db.session.flush()
    db.session.add(GroupMember(group_id=g.id,user_id=session["user_id"],role="owner"));log_activity(g.id,session["user_id"],"group_created",f"Created the group {name}.");db.session.commit()
    return jsonify(group=group_dict(g,1)),201
@app.post("/api/groups/join")
@auth
def join_group():
    code=str((request.get_json(silent=True) or {}).get("invite_code","")).strip().upper();g=Group.query.filter_by(invite_code=code).first()
    if not g:return err("Invitation code not found.",404)
    if member(g.id,session["user_id"]):return err("Already a member of this group.",409)
    db.session.add(GroupMember(group_id=g.id,user_id=session["user_id"]));log_activity(g.id,session["user_id"],"member_joined","Joined the group using an invitation code.");db.session.commit()
    return jsonify(group=group_dict(g)),201
@app.get("/api/groups/<int:gid>")
@auth
def group_detail(gid):
    g=allowed(gid,session["user_id"])
    if not g:return err("Group not found or access denied.",404)
    rows=db.session.query(User,GroupMember.role).join(GroupMember,GroupMember.user_id==User.id).filter(GroupMember.group_id==gid).order_by(User.name).all()
    return jsonify(group=group_dict(g,len(rows)),members=[{**user_dict(u),"role":role} for u,role in rows])

@app.get("/api/groups/<int:gid>/expenses")
@auth
def expenses(gid):
    if not allowed(gid,session["user_id"]):return err("Group not found or access denied.",404)
    rows=db.session.query(Expense,User.name).join(User,User.id==Expense.paid_by).filter(Expense.group_id==gid).order_by(Expense.expense_date.desc(),Expense.id.desc()).all()
    return jsonify(expenses=[expense_dict(e,n) for e,n in rows])
@app.post("/api/groups/<int:gid>/expenses")
@auth
def add_expense(gid):
    if not allowed(gid,session["user_id"]):return err("Group not found or access denied.",404)
    d=request.get_json(silent=True) or {};title=str(d.get("title","")).strip();cat=str(d.get("category","Other"))
    try:amount=dec(d.get("amount",""));day=date.fromisoformat(str(d.get("expense_date",date.today().isoformat())));payer=int(d.get("paid_by",session["user_id"]))
    except (ValueError,TypeError,InvalidOperation):return err("Enter a valid amount, date and payer.")
    if not title or len(title)>160:return err("Expense title is required (maximum 160 characters).")
    if amount<=0:return err("Amount must be greater than zero.")
    if cat not in CATEGORIES:return err("Choose a valid category.")
    if not member(gid,payer):return err("Payer must be a group member.")
    parts=d.get("participants")
    if not isinstance(parts,list) or not parts:return err("Select at least one participant.")
    try:
        ids=list(dict.fromkeys(int(p["user_id"] if isinstance(p,dict) else p) for p in parts))
    except (ValueError,TypeError,KeyError):return err("Invalid participant list.")
    valid={x.user_id for x in GroupMember.query.filter_by(group_id=gid).all()}
    if not set(ids).issubset(valid):return err("All participants must be group members.")
    split=d.get("split_type","equal");shares={}
    if split=="equal":
        cents=int(amount*100);base,rem=divmod(cents,len(ids))
        shares={uid:Decimal(base+(i<rem))/100 for i,uid in enumerate(ids)}
    elif split=="custom":
        try:shares={int(p["user_id"]):dec(p["share"]) for p in parts}
        except (ValueError,TypeError,KeyError,InvalidOperation):return err("Enter a valid share for each participant.")
        if set(shares)!=set(ids) or any(v<0 for v in shares.values()):return err("Custom shares must be non-negative and match selected participants.")
        if sum(shares.values(),Decimal("0.00"))!=amount:return err("Custom shares must add up exactly to the expense amount.")
    else:return err("Split type must be equal or custom.")
    try:
        e=Expense(group_id=gid,paid_by=payer,title=title,amount=amount,category=cat,expense_date=day,notes=str(d.get("notes","")).strip()[:500] or None)
        db.session.add(e);db.session.flush()
        for uid,share in shares.items():db.session.add(ExpenseSplit(expense_id=e.id,user_id=uid,share_amount=share))
        log_activity(gid,session["user_id"],"expense_added",f"Added {title} ({cat}) for ₹{m(amount)}.")
        db.session.commit()
    except Exception:
        db.session.rollback();app.logger.exception("Expense save failed");return err("Could not save expense. Please try again.",500)
    return jsonify(expense=expense_dict(e)),201

@app.get("/api/groups/<int:gid>/balances")
@auth
def get_balances(gid):
    if not allowed(gid,session["user_id"]):return err("Group not found or access denied.",404)
    vals=balances_for(gid);users={u.id:u for u in User.query.filter(User.id.in_(list(vals))).all()} if vals else {}
    result=[]
    for uid,v in vals.items():
        if uid in users:result.append({"user_id":uid,"name":users[uid].name,"email":users[uid].email,"net_balance":m(v),"status":"gets back" if v>0 else "owes" if v<0 else "settled"})
    result.sort(key=lambda x:Decimal(x["net_balance"]),reverse=True)
    return jsonify(balances=result,suggestions=suggestions(gid))
@app.get("/api/groups/<int:gid>/settlements")
@auth
def settlements(gid):
    if not allowed(gid,session["user_id"]):return err("Group not found or access denied.",404)
    P=aliased(User);R=aliased(User)
    rows=db.session.query(Settlement,P.name,R.name).join(P,P.id==Settlement.paid_by).join(R,R.id==Settlement.paid_to).filter(Settlement.group_id==gid).order_by(Settlement.settlement_date.desc(),Settlement.id.desc()).all()
    return jsonify(settlements=[{"id":s.id,"paid_by":s.paid_by,"paid_to":s.paid_to,"payer_name":pn,"receiver_name":rn,"amount":m(s.amount),"settlement_date":s.settlement_date.isoformat(),"note":s.note or ""} for s,pn,rn in rows])
@app.post("/api/groups/<int:gid>/settlements")
@auth
def add_settlement(gid):
    if not allowed(gid,session["user_id"]):return err("Group not found or access denied.",404)
    d=request.get_json(silent=True) or {}
    try:by=int(d.get("paid_by"));to=int(d.get("paid_to"));amount=dec(d.get("amount",""));day=date.fromisoformat(str(d.get("settlement_date",date.today().isoformat())))
    except (ValueError,TypeError,InvalidOperation):return err("Enter valid payer, receiver, amount and date.")
    if by==to:return err("Payer and receiver must be different.")
    if amount<=0:return err("Amount must be greater than zero.")
    if not member(gid,by) or not member(gid,to):return err("Both people must belong to this group.")
    vals=balances_for(gid)
    if vals.get(by,Decimal("0.00"))>=0 or vals.get(to,Decimal("0.00"))<=0:return err("Select a member who owes money and a member who is owed money.")
    max_amt=min(-vals[by],vals[to])
    if amount>max_amt:return err(f"Amount exceeds current debt of ₹{m(max_amt)}.")
    s=Settlement(group_id=gid,paid_by=by,paid_to=to,amount=amount,settlement_date=day,note=str(d.get("note","")).strip()[:300] or None)
    db.session.add(s);log_activity(gid,session["user_id"],"settlement_recorded",f"Recorded a settlement of ₹{m(amount)}.");db.session.commit()
    return jsonify(message="Settlement recorded."),201

@app.put("/api/groups/<int:gid>/expenses/<int:eid>")
@auth
def update_expense(gid,eid):
    if not allowed(gid,session["user_id"]): return err("Group not found or access denied.",404)
    e=Expense.query.filter_by(id=eid,group_id=gid).first()
    if not e: return err("Expense not found.",404)
    d=request.get_json(silent=True) or {}
    title=str(d.get("title",e.title)).strip();cat=str(d.get("category",e.category))
    try: amount=dec(d.get("amount",e.amount));day=date.fromisoformat(str(d.get("expense_date",e.expense_date.isoformat())));payer=int(d.get("paid_by",e.paid_by))
    except (ValueError,TypeError,InvalidOperation): return err("Enter a valid amount, date and payer.")
    if not title or len(title)>160:return err("Description is required (maximum 160 characters).")
    if amount<=0:return err("Amount must be greater than zero.")
    if cat not in CATEGORIES:return err("Choose a valid category.")
    if not member(gid,payer):return err("Payer must be a group member.")
    parts=d.get("participants")
    if not isinstance(parts,list) or not parts:return err("Select at least one participant.")
    try: ids=list(dict.fromkeys(int(p["user_id"] if isinstance(p,dict) else p) for p in parts))
    except (ValueError,TypeError,KeyError):return err("Invalid participant list.")
    valid={x.user_id for x in GroupMember.query.filter_by(group_id=gid).all()}
    if not set(ids).issubset(valid):return err("All participants must be group members.")
    split=d.get("split_type","equal");shares={}
    if split=="equal":
        cents=int(amount*100);base,rem=divmod(cents,len(ids));shares={uid:Decimal(base+(i<rem))/100 for i,uid in enumerate(ids)}
    elif split=="custom":
        try:shares={int(p["user_id"]):dec(p["share"]) for p in parts}
        except (ValueError,TypeError,KeyError,InvalidOperation):return err("Enter a valid share for each participant.")
        if set(shares)!=set(ids) or any(v<0 for v in shares.values()) or sum(shares.values(),Decimal("0.00"))!=amount:return err("Custom shares must be non-negative and add up exactly to the expense amount.")
    else:return err("Split type must be equal or custom.")
    try:
        e.title=title;e.amount=amount;e.category=cat;e.expense_date=day;e.paid_by=payer;e.notes=str(d.get("notes",e.notes or "")).strip()[:500] or None
        ExpenseSplit.query.filter_by(expense_id=e.id).delete(synchronize_session=False)
        for uid,share in shares.items():db.session.add(ExpenseSplit(expense_id=e.id,user_id=uid,share_amount=share))
        log_activity(gid,session["user_id"],"expense_updated",f"Updated {title} ({cat}) to ₹{m(amount)}.")
        db.session.commit()
    except Exception:
        db.session.rollback();app.logger.exception("Expense update failed");return err("Could not update expense. Please try again.",500)
    return jsonify(expense=expense_dict(e))

@app.delete("/api/groups/<int:gid>/expenses/<int:eid>")
@auth
def delete_expense(gid,eid):
    if not allowed(gid,session["user_id"]):return err("Group not found or access denied.",404)
    e=Expense.query.filter_by(id=eid,group_id=gid).first()
    if not e:return err("Expense not found.",404)
    title=e.title;amount=m(e.amount)
    try:
        ExpenseSplit.query.filter_by(expense_id=e.id).delete(synchronize_session=False)
        db.session.delete(e);log_activity(gid,session["user_id"],"expense_deleted",f"Deleted {title} (₹{amount}).");db.session.commit()
    except Exception:
        db.session.rollback();return err("Could not delete expense.",500)
    return jsonify(message="Expense deleted.")

@app.get("/api/groups/<int:gid>/budget")
@auth
def get_budget(gid):
    if not allowed(gid,session["user_id"]):return err("Group not found or access denied.",404)
    b=GroupBudget.query.filter_by(group_id=gid).first()
    spent=db.session.query(func.coalesce(func.sum(Expense.amount),0)).filter(Expense.group_id==gid,extract("year",Expense.expense_date)==date.today().year,extract("month",Expense.expense_date)==date.today().month).scalar()
    return jsonify(budget={"monthly_limit":m(b.monthly_limit),"updated_at":b.updated_at.isoformat() if b else None} if b else None,month_spent=m(spent))

@app.put("/api/groups/<int:gid>/budget")
@auth
def set_budget(gid):
    if not allowed(gid,session["user_id"]):return err("Group not found or access denied.",404)
    try:limit=dec((request.get_json(silent=True) or {}).get("monthly_limit",""))
    except (ValueError,TypeError,InvalidOperation):return err("Enter a valid monthly budget.")
    if limit<=0:return err("Monthly budget must be greater than zero.")
    b=GroupBudget.query.filter_by(group_id=gid).first()
    if b:b.monthly_limit=limit;b.updated_by=session["user_id"]
    else:db.session.add(GroupBudget(group_id=gid,monthly_limit=limit,updated_by=session["user_id"]))
    log_activity(gid,session["user_id"],"budget_updated",f"Set the monthly group budget to ₹{m(limit)}.");db.session.commit()
    return jsonify(message="Monthly budget saved.",monthly_limit=m(limit))

@app.get("/api/groups/<int:gid>/activity")
@auth
def group_activity(gid):
    if not allowed(gid,session["user_id"]):return err("Group not found or access denied.",404)
    rows=db.session.query(ActivityLog,User.name).outerjoin(User,User.id==ActivityLog.user_id).filter(ActivityLog.group_id==gid).order_by(ActivityLog.created_at.desc(),ActivityLog.id.desc()).limit(40).all()
    return jsonify(activity=[{"id":a.id,"user_name":name or "Former member","action":a.action,"details":a.details,"created_at":a.created_at.isoformat(timespec="minutes")} for a,name in rows])

@app.get("/api/dashboard")
@auth
def dashboard():
    gids=[x.group_id for x in GroupMember.query.filter_by(user_id=session["user_id"]).all()]
    if not gids:return jsonify(group_count=0,total_expenses="0.00",recent_expenses=[],category_totals=[])
    total=db.session.query(func.coalesce(func.sum(Expense.amount),0)).filter(Expense.group_id.in_(gids)).scalar()
    recent=db.session.query(Expense,User.name).join(User,User.id==Expense.paid_by).filter(Expense.group_id.in_(gids)).order_by(Expense.expense_date.desc(),Expense.id.desc()).limit(8).all()
    cats=db.session.query(Expense.category,func.sum(Expense.amount)).filter(Expense.group_id.in_(gids)).group_by(Expense.category).all()
    return jsonify(group_count=len(gids),total_expenses=m(total),recent_expenses=[expense_dict(e,n) for e,n in recent],category_totals=[{"category":c,"total":m(v)} for c,v in cats])

@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api/"):return err("API endpoint not found.",404)
    return send_from_directory(ROOT/"frontend","index.html")
@app.errorhandler(500)
def server_error(_):
    db.session.rollback();return err("Unexpected server error.",500)

with app.app_context():
    db.create_all()

if __name__=="__main__":
    app.run(host=os.getenv("HOST","127.0.0.1"),port=int(os.getenv("PORT","5000")),debug=False)
