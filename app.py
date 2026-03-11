from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///regiment_system.db'
db = SQLAlchemy(app)

class Soldier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.String(50), nullable=False)
    strikes = db.relationship('Strike', backref='soldier', lazy=True)

    @property
    def active_count(self):
        # Counts strikes that are not appealed OR are already locked
        return sum(1 for s in self.strikes if s.status != 'Appealed' or s.is_locked)

    @property
    def appealed_count(self):
        # Only counts strikes in 'Appealed' status that aren't 3 days old yet
        return sum(1 for s in self.strikes if s.status == 'Appealed' and not s.is_locked)

class Strike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    soldier_id = db.Column(db.Integer, db.ForeignKey('soldier.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Active')

    @property
    def is_locked(self):
        # Logic: Strike becomes locked after 3 days
        return datetime.utcnow() > self.date_issued + timedelta(days=3)

@app.route('/')
def index():
    search = request.args.get('search', '')
    soldiers = Soldier.query.filter(Soldier.name.contains(search)).all() if search else Soldier.query.all()
    return render_template('index.html', soldiers=soldiers, search=search)

@app.route('/add_soldier', methods=['POST'])
def add_soldier():
    db.session.add(Soldier(name=request.form['name'], rank=request.form['rank']))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/issue_strike/<int:s_id>', methods=['POST'])
def issue_strike(s_id):
    db.session.add(Strike(soldier_id=s_id, reason=request.form['reason']))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/appeal/<int:strike_id>')
def appeal(strike_id):
    strike = Strike.query.get_or_404(strike_id)
    if not strike.is_locked:
        strike.status = 'Appealed'
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)