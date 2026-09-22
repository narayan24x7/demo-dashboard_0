"""Reproducible synthetic demonstration data; no real customer or staff records."""
import random
from datetime import date, timedelta

def seed(db):
    if db.execute('SELECT COUNT(*) FROM outlets').fetchone()[0]:
        return
    rng = random.Random(42)
    today = date.today()
    db.execute('INSERT INTO franchises VALUES(1,?,?,?)', ('Urban Table', 'Gujarat', 'Demo Operations Team'))
    locations = [('Ahmedabad Central','North'),('Anand Campus','Central'),('Vadodara West','Central'),('Surat Riverside','South'),('Rajkot Market','West'),('Gandhinagar Hub','North')]
    for oid, (name, region) in enumerate(locations,1):
        db.execute('INSERT INTO outlets VALUES(?,?,?,?,?)',(oid,1,name,region,'active'))
        for days in range(90):
            d = today - timedelta(days=89-days)
            base = [42000,31000,37000,48000,26000,39000][oid-1]
            factor = (0.68 if oid == 5 and days >= 60 else 1) * (1.18 if d.weekday()>=5 else 1)
            revenue = round(base * factor * rng.uniform(.87,1.13),2)
            db.execute('INSERT INTO sales(outlet_id,date,revenue,transactions,cost) VALUES(?,?,?,?,?)',(oid,d.isoformat(),revenue,int(revenue/240),round(revenue*rng.uniform(.57,.73),2)))
        for j,product in enumerate(['Rice (kg)','Vegetables (kg)','Cooking oil (L)','Packaging (units)']):
            demand = [16,24,8,140][j]
            quantity = demand * (1.2 if oid in (2,5) and j<2 else 8)
            cur=db.execute('INSERT INTO inventory(outlet_id,product,quantity,reorder_level,lead_days,unit_cost,expiry_date) VALUES(?,?,?,?,?,?,?)',(oid,product,quantity,demand*3,3,[55,40,130,3][j],(today+timedelta(days=2 if j==1 else 90)).isoformat()))
            for k in range(35):
                used = round(demand*rng.uniform(.8,1.2),2)
                db.execute('INSERT INTO movements(inventory_id,date,used,wasted) VALUES(?,?,?,?)',(cur.lastrowid,(today-timedelta(days=34-k)).isoformat(),used,round(used*(.15 if oid==5 else .02),2)))
        for n in range(5):
            hours=40 if oid!=5 else 29
            db.execute('INSERT INTO staff(outlet_id,name,role,scheduled_hours,worked_hours,orders,shift) VALUES(?,?,?,?,?,?,?)',(oid,f'Team member {oid}-{n+1}',['Manager','Chef','Service','Service','Cashier'][n],40,hours,rng.randint(70,150),'09:00–17:00' if n%2 else '14:00–22:00'))
        for name in ['Lunch special','Local discovery']:
            spend=10000
            db.execute('INSERT INTO campaigns(outlet_id,name,spend,attributed_revenue,gross_margin,impressions,clicks,conversions,status) VALUES(?,?,?,?,?,?,?,?,?)',(oid,name,spend,18000 if oid in (2,5) else 55000,.4,22000,1200,160,'active'))
        for category in ['Food safety','Brand standards','Service quality']:
            critical=int(oid==5 and category=='Food safety')
            db.execute('INSERT INTO audits(outlet_id,date,category,score,finding,critical) VALUES(?,?,?,?,?,?)',(oid,today.isoformat(),category,48 if critical else rng.randint(78,99),'Temperature log incomplete' if critical else 'Routine inspection completed',critical))
    db.commit()
