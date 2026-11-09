# Plan course de Hannibal (5 km sous 20 min, 2 sorties par semaine) : écrit course.js pour l'app
# et un fichier .fit par séance pour la Forerunner 255, avec les allures tirées du dernier test 5 km.
# Usage : python -I plan_course.py 24:00      (chrono du dernier test 5 km)
# Allures : équations de Daniels et Gilbert (VDOT), sans dépendance externe.
import json, math, os, struct, sys, time, datetime

ICI = os.path.dirname(os.path.abspath(__file__))
DEBUT = datetime.date(2026, 11, 9)  # lundi de la semaine 1
OBJECTIF = 4 * 60                    # 4:00/km = 20:00 au 5 km

# ---------- plan ----------
def E(min_, nom='Footing'): return {'k': 'run', 't': min_ * 60, 'a': 'E', 'n': nom}
def ech(min_=15): return {'k': 'ech', 't': min_ * 60, 'a': 'E', 'n': 'Échauffement'}
def cal(min_=10): return {'k': 'cal', 't': min_ * 60, 'a': 'E', 'n': 'Retour au calme'}
def trot(sec): return {'k': 'rec', 't': sec, 'a': None, 'n': 'Trot'}
def reps(n, effort, recup): return {'rep': n, 'pas': [effort, recup]}
def dist(m, a): return {'k': 'run', 'd': m, 'a': a, 'n': f'{m} m' if m < 1000 else f'{m / 1000:g} km'.replace('.', ',')}
def bloc(min_, a='T'): return {'k': 'run', 't': min_ * 60, 'a': a, 'n': f'{min_} min seuil'}
LIGNES = reps(6, {'k': 'run', 't': 20, 'a': None, 'n': 'Ligne droite'}, {'k': 'rec', 't': 60, 'a': None, 'n': 'Marche ou trot'})

def fractionne(n, m, recup, a='I'):
    return {'titre': f'{n} × {m} m', 'pas': [ech(), reps(n, dist(m, a), trot(recup)), cal()]}
def seuil(blocs, recup, fin):
    titre = f'{len(blocs)} × {blocs[0]} min seuil' if len(blocs) > 1 else f'{blocs[0]} min au seuil'
    p = [ech()]
    p += [reps(len(blocs), bloc(blocs[0]), trot(recup))] if len(blocs) > 1 else [bloc(blocs[0])]
    return {'titre': titre, 'pas': p + [E(fin, 'Footing fin')]}
def footing(min_, lignes=False):
    return {'titre': f'Footing {min_} min' + (' + lignes droites' if lignes else ''), 'pas': [E(min_)] + ([LIGNES] if lignes else [])}
TEST = {'titre': 'Test 5 km', 'test': 1, 'pas': [ech(), reps(4, {'k': 'run', 't': 20, 'a': None, 'n': 'Ligne droite'}, trot(60)),
        {'k': 'run', 'd': 5000, 'a': None, 'n': '5 km à fond'}, cal()]}

SEM = [  # (mardi, dimanche)
    (footing(30, True), TEST),
    (fractionne(6, 400, 90), seuil([6, 6, 6], 60, 15)),
    (fractionne(8, 400, 90), seuil([10, 10], 120, 20)),
    (fractionne(5, 800, 120), seuil([5, 5, 5, 5], 60, 25)),
    (footing(30, True), footing(40)),
    (fractionne(6, 800, 120), TEST),
    (fractionne(5, 1000, 150), seuil([12, 12], 120, 25)),
    (fractionne(10, 400, 75), seuil([8, 8, 8], 90, 25)),
    (fractionne(6, 1000, 150), seuil([20], 0, 25)),
    (footing(30, True), footing(45)),
    (fractionne(4, 1200, 180), TEST),
    (fractionne(6, 800, 120), seuil([15, 15], 180, 20)),
    (fractionne(3, 1600, 180), seuil([6, 6, 6, 6], 60, 30)),
    (fractionne(12, 400, 60), seuil([25], 0, 25)),
    (footing(30, True), footing(45)),
    (fractionne(5, 1000, 120), TEST),
    (fractionne(5, 1000, 120, 'A5'), seuil([15, 15], 120, 25)),
    (fractionne(4, 1200, 150, 'A5'), seuil([20], 0, 20)),
    (fractionne(2, 2000, 180, 'A5'), footing(40, True)),
    (fractionne(4, 400, 90, 'A5'), dict(TEST, titre='Objectif : 5 km sous 20 min', objectif=1)),
]
ALLEGEES = {5, 10, 15}
BUTS = {'I': 'Fractionné : fait monter ta VO2 max, la clé du 5 km.', 'T': 'Seuil : tenir vite plus longtemps.',
        'A5': 'Allure 5 km visée : apprendre le rythme de la course.', 'E': 'Footing facile : récupérer, construire le fond.'}

def plan():
    out = []
    for w, (mar, dim) in enumerate(SEM, 1):
        for j, s in ((1, mar), (6, dim)):
            d = DEBUT + datetime.timedelta(days=7 * (w - 1) + j)
            out.append(dict(s, id=f's{w:02d}{"m" if j == 1 else "d"}', sem=w, d=d.isoformat(), allegee=int(w in ALLEGEES)))
    return out

# ---------- allures (Daniels-Gilbert) ----------
vo2 = lambda v: -4.60 + 0.182258 * v + 0.000104 * v * v
frac = lambda t: 0.8 + 0.1894393 * math.exp(-0.012778 * t) + 0.2989558 * math.exp(-0.1932605 * t)
vdot = lambda d, s: vo2(d / (s / 60)) / frac(s / 60)
def vitesse(o):  # m/min pour une consommation d'oxygène donnée
    a, b, c = 0.000104, 0.182258, -4.60 - o
    return (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)
def chrono5k(V):
    lo, hi = 600, 3600
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if vdot(5000, m) > V else (lo, m)
    return m
def allures(test_s):  # secondes par km : (lent, rapide)
    V = vdot(5000, test_s)
    sk = lambda p: 60000 / vitesse(p * V)
    a5 = max(OBJECTIF, chrono5k(V + 2) / 5)  # un cran au-dessus du dernier test, jamais plus vite que 4:00
    return {'E': (sk(.62), sk(.70)), 'T': (sk(.88) + 5, sk(.88) - 5), 'I': (sk(.975) + 5, sk(.975) - 5), 'A5': (a5 + 4, a5 - 4)}

# ---------- FIT (protocole public Garmin : file_id, workout, workout_step) ----------
CRC_T = [0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401, 0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400]
def crc(data, c=0):
    for b in data:
        for n in (b & 0xF, b >> 4):
            t = CRC_T[c & 0xF]; c = (c >> 4) & 0x0FFF; c ^= t ^ CRC_T[n]
    return c
def chaine(s, n):
    b = s.encode('utf-8')[:n - 1]
    while True:
        try: b.decode('utf-8'); break
        except UnicodeDecodeError: b = b[:-1]
    return b + b'\0' * (n - len(b))
ENUM, U16, U32, U32Z, STR = 0x00, 0x84, 0x86, 0x8C, 0x07
FMT = {ENUM: 'B', U16: 'H', U32: 'I', U32Z: 'I'}
def message(local, glob, champs):  # champs : [(numéro, type, taille, valeur)]
    d = struct.pack('<BBBHB', 0x40 | local, 0, 0, glob, len(champs)) + b''.join(struct.pack('BBB', n, z, t) for n, t, z, _ in champs)
    v = bytes([local]) + b''.join(chaine(x, z) if t == STR else struct.pack('<' + FMT[t], x) for n, t, z, x in champs)
    return d + v
INTENS = {'run': 0, 'rec': 4, 'ech': 2, 'cal': 3}
def fit(nom, pas, al):
    plats = []  # étapes à plat, les répétitions renvoient à l'index de leur première étape
    for p in pas:
        if 'rep' in p:
            i0 = len(plats); plats += p['pas']; plats.append({'repeat': i0, 'n': p['rep']})
        else: plats.append(p)
    data = message(0, 0, [(0, ENUM, 1, 5), (1, U16, 2, 1), (2, U16, 2, 65534), (3, U32Z, 4, 1), (4, U32, 4, int(time.time()) - 631065600)])
    data += message(1, 26, [(4, ENUM, 1, 1), (6, U16, 2, len(plats)), (8, STR, 32, nom)])
    for i, p in enumerate(plats):
        if 'repeat' in p:
            ch = [(254, U16, 2, i), (0, STR, 16, ''), (1, ENUM, 1, 6), (2, U32, 4, p['repeat']), (3, ENUM, 1, 2), (4, U32, 4, p['n']), (5, U32, 4, 0), (6, U32, 4, 0), (7, ENUM, 1, 0)]
        else:
            dt, dv = (1, p['d'] * 100) if 'd' in p else (0, p['t'] * 1000)
            if p['a']:
                lent, vite = al[p['a']]; tt, lo, hi = 0, round(1e6 / lent), round(1e6 / vite)  # vitesse en mm/s
            else: tt, lo, hi = 2, 0, 0
            ch = [(254, U16, 2, i), (0, STR, 16, p['n']), (1, ENUM, 1, dt), (2, U32, 4, dv), (3, ENUM, 1, tt), (4, U32, 4, 0), (5, U32, 4, lo), (6, U32, 4, hi), (7, ENUM, 1, INTENS[p['k']])]
        data += message(2, 27, ch)
    h = struct.pack('<BBHI4s', 14, 0x10, 2132, len(data), b'.FIT')
    h += struct.pack('<H', crc(h))
    return h + data + struct.pack('<H', crc(h + data))

def mmss(s): s = round(s); return f'{s // 60}:{s % 60:02d}'

if __name__ == '__main__':
    m, s = map(int, (sys.argv[1] if len(sys.argv) > 1 else '24:00').split(':'))
    al, P = allures(m * 60 + s), plan()
    with open(os.path.join(os.path.dirname(ICI), 'course.js'), 'w', encoding='utf-8') as f:
        f.write('// généré par montre/plan_course.py, ne pas modifier à la main\nwindow.COURSE_PLAN = ' + json.dumps(P, ensure_ascii=False) + f';\nwindow.COURSE_FIT = {m * 60 + s};  // fichiers .fit calés sur ce chrono\n')
    dos = os.path.join(ICI, 'fit'); os.makedirs(dos, exist_ok=True)
    for x in os.listdir(dos):
        if x.endswith('.fit'): os.remove(os.path.join(dos, x))
    for x in P:
        jour = 'mar' if x['id'].endswith('m') else 'dim'
        nom = f"S{x['sem']:02d} {jour} {x['titre']}".replace('×', 'x').replace('Objectif : ', '')
        with open(os.path.join(dos, f"{x['id']}.fit"), 'wb') as f: f.write(fit(nom, x['pas'], al))
    print(f'{len(P)} séances, allures pour un 5 km en {m}:{s:02d} :', {k: f'{mmss(a)}-{mmss(b)}' for k, (a, b) in al.items()})
