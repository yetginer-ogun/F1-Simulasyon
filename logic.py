import sqlite3
import os
import random

DB_NAME = 'f1_2025.db'

class F1db:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        new_db = not os.path.exists(db_name)
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.c = self.conn.cursor()
        if new_db:
            self.create_tables()
            self.default_insert()
        else:
            self._ensure_columns()

    def create_tables(self):
        self.c.execute('''
        CREATE TABLE drivers (
            driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            current_points INTEGER,
            dnf_prob REAL DEFAULT 0.05
        )
        ''')
        self.c.execute('''
        CREATE TABLE remaining_races (
            race_id INTEGER PRIMARY KEY AUTOINCREMENT,
            race_name TEXT UNIQUE,
            is_sprint INTEGER DEFAULT 0
        )
        ''')
        self.conn.commit()

    def _ensure_columns(self):
        self.c.execute("PRAGMA table_info(drivers)")
        cols = [row[1] for row in self.c.fetchall()]
        if 'dnf_prob' not in cols:
            self.c.execute('ALTER TABLE drivers ADD COLUMN dnf_prob REAL DEFAULT 0.05')
            self.conn.commit()

        self.c.execute("PRAGMA table_info(remaining_races)")
        cols2 = [row[1] for row in self.c.fetchall()]
        if 'is_sprint' not in cols2:
            self.c.execute('ALTER TABLE remaining_races ADD COLUMN is_sprint INTEGER DEFAULT 0')
            self.conn.commit()

    def default_insert(self):
        drivers_data = [
            ("Lando Norris", 390, 0.05),
            ("Oscar Piastri", 366, 0.05),
            ("Max Verstappen", 366, 0.08),
            ("George Russell", 294, 0.05),
            ("Charles Leclerc", 226, 0.06),
            ("Lewis Hamilton", 152, 0.04),
            ("Kimi Antonelli", 137, 0.07),
            ("Alexander Albon", 73, 0.07),
            ("Nico Hülkenberg", 46, 0.06),
            ("Isack Hadjar", 43, 0.07),
            ("Oliver Bearman", 40, 0.08),
            ("Fernando Alonso", 40, 0.06),
            ("Carlos Sainz", 48, 0.06),
            ("Liam Lawson", 36, 0.07),
            ("Lance Stroll", 32, 0.08),
            ("Esteban Ocon", 32, 0.06),
            ("Yuki Tsunoda", 28, 0.09),
            ("Pierre Gasly", 22, 0.07),
            ("Gabriel Bortoleto", 19, 0.10),
            ("Franco Colapinto", 0, 0.12)
        ]
        races_data = [
            ("Qatar Grand Prix", 0),
            ("Abu Dhabi Grand Prix", 0)
        ]
        self.c.executemany(
            'INSERT OR IGNORE INTO drivers(name, current_points, dnf_prob) VALUES (?, ?, ?)', drivers_data
        )
        self.c.executemany(
            'INSERT OR IGNORE INTO remaining_races(race_name, is_sprint) VALUES (?, ?)', races_data
        )
        self.conn.commit()

    def upsert_driver(self, driver_id, name, points, dnf_prob):
        if driver_id is not None:
            self.c.execute(
                'UPDATE drivers SET name=?, current_points=?, dnf_prob=? WHERE driver_id=?',
                (name, int(points), float(dnf_prob), int(driver_id))
            )
        else:
            self.c.execute(
                'INSERT OR REPLACE INTO drivers(name, current_points, dnf_prob) VALUES (?, ?, ?)',
                (name, int(points), float(dnf_prob))
            )
        self.conn.commit()

    def delete_driver(self, driver_id):
        self.c.execute('DELETE FROM drivers WHERE driver_id=?', (driver_id,))
        self.conn.commit()

    def upsert_race(self, race_id, name, is_sprint):
        if race_id is not None:
            self.c.execute('UPDATE remaining_races SET race_name=?, is_sprint=? WHERE race_id=?',
                           (name, int(bool(is_sprint)), int(race_id)))
        else:
            self.c.execute('INSERT OR REPLACE INTO remaining_races(race_name, is_sprint) VALUES (?, ?)',
                           (name, int(bool(is_sprint))))
        self.conn.commit()


    def get_all_drivers(self):
        self.c.execute("SELECT name, current_points, dnf_prob, driver_id FROM drivers")
        rows = self.c.fetchall()
        return rows
    
    def get_all_races(self):
        self.c.execute("SELECT * FROM remaining_races")
        rows = self.c.fetchall()
        return rows
    
    def get_all_races_names(self):
        self.c.execute("SELECT race_name FROM remaining_races")
        rows = self.c.fetchall()
        return rows
    
    def reset_data(self):
        self.c.execute("DROP TABLE IF EXISTS drivers")
        self.c.execute("DROP TABLE IF EXISTS remaining_races")
        self.create_tables()
        self.default_insert()

    def add_race(self,name,sprint):
        self.c.execute("INSERT INTO remaining_races(race_name, is_sprint) VALUES (?, ?)",(name, int(bool(sprint))))
        self.conn.commit()

    def close(self):
        self.conn.close()


def monte_carlo_championship(drivers, races, num_simulations=5000):
    points_standard = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
    points_sprint   = [8, 7, 6, 5, 4, 3, 2, 1]

    # İsimleri ve temel değerleri tuple'lardan çekiyoruz
    names      = [d[0] for d in drivers]          # name
    base_points = {d[0]: int(d[1]) for d in drivers}   # points
    dnf_probs   = {d[0]: float(d[2]) for d in drivers} # dnf_prob
    # driver_id (d[3]) şu an simülasyonda kullanılmıyor, istersen ek mantıkta kullanabilirsin

    champion_count = {name: 0 for name in names}

    for _ in range(num_simulations):
        pts = base_points.copy()

        # races: (race_id, race_name, is_sprint)
        for r in races:
            race_id, race_name, is_sprint_flag = r
            is_sprint = bool(is_sprint_flag)

            # DNF olmayan sürücüler
            eligible = [n for n in names if random.random() > dnf_probs[n]]
            if not eligible:
                continue

            random.shuffle(eligible)
            points_awarded = points_sprint if is_sprint else points_standard

            for pos, driver in enumerate(eligible):
                if pos < len(points_awarded):
                    pts[driver] += points_awarded[pos]

        max_points = max(pts.values())
        leaders = [n for n, p in pts.items() if p == max_points]

        champion = random.choice(leaders) if len(leaders) > 1 else leaders[0]
        champion_count[champion] += 1

    # Olasılıkları döndür
    return {name: champion_count[name] / num_simulations for name in names}
