from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__, template_folder='html')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
db = SQLAlchemy(app)

# Client model
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    reservations = db.relationship('Reservation', backref='client', lazy=True)

# Chambre model
class Chambre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True)
    type = db.Column(db.String(50))
    prix = db.Column(db.Float)
    reservations = db.relationship('Reservation', backref='chambre', lazy=True)

# Réservation model
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_client = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    id_chambre = db.Column(db.Integer, db.ForeignKey('chambre.id'), nullable=False)
    date_arrivee = db.Column(db.DateTime, nullable=False)
    date_depart = db.Column(db.DateTime, nullable=False)
    statut = db.Column(db.String(50), default='confirmée')

# Créer les tables dans la base de données
with app.app_context():
    db.create_all()

@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    clients_list = []
    for client in clients:
        client_data = {
            'id': client.id,
            'nom': client.nom,
            'email': client.email
        }
        clients_list.append(client_data)
    return jsonify(clients_list)

@app.route('/api/clients/<int:id>', methods=['GET'])
def get_client(id):
    client = Client.query.get_or_404(id)
    client_data = {
        'id': client.id,
        'nom': client.nom,
        'email': client.email
    }
    return jsonify(client_data)

@app.route('/api/clients', methods=['POST'])
def create_client():
    data = request.json
    new_client = Client(nom=data['nom'], email=data['email'])
    db.session.add(new_client)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Client created successfully.'}), 201

@app.route('/api/chambres', methods=['GET'])
def get_chambres():
    chambres = Chambre.query.all()
    chambres_list = []
    for chambre in chambres:
        chambres_list.append({
            'id': chambre.id,
            'numero': chambre.numero,
            'type': chambre.type,
            'prix': chambre.prix
        })
    return jsonify(chambres_list)

@app.route('/api/chambres/<int:id>', methods=['GET'])
def get_chambre_by_id(id):
    chambre = Chambre.query.get_or_404(id)
    chambre_data = {
        'id': chambre.id,
        'numero': chambre.numero,
        'type': chambre.type,
        'prix': chambre.prix
    }
    return jsonify(chambre_data)

@app.route('/api/chambres/disponibles', methods=['GET'])
def chambres_disponibles():
    date_arrivee = request.args.get('date_arrivee')
    date_depart = request.args.get('date_depart')
    
    # Convertir les dates en objets datetime
    date_arrivee = datetime.strptime(date_arrivee, '%Y-%m-%d')
    date_depart = datetime.strptime(date_depart, '%Y-%m-%d')
    
    chambres_disponibles = []

    # Parcourir toutes les chambres
    for chambre in Chambre.query.all():
        reservations = Reservation.query.filter_by(id_chambre=chambre.id).all()
        disponible = True
        
        # Vérifier si la chambre est disponible pour les dates spécifiées
        for reservation in reservations:
            if (date_arrivee <= reservation.date_depart) and (date_depart >= reservation.date_arrivee):
                disponible = False
                break
        
        # Si la chambre est disponible, l'ajouter à la liste des chambres disponibles
        if disponible:
            chambres_disponibles.append({
                'id': chambre.id,
                'numero': chambre.numero,
                'type': chambre.type,
                'prix': chambre.prix
            })

    return jsonify(chambres_disponibles)

@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    reservations = Reservation.query.all()
    reservations_list = []
    for reservation in reservations:
        reservation_data = {
            'id': reservation.id,
            'id_client': reservation.id_client,
            'id_chambre': reservation.id_chambre,
            'date_arrivee': reservation.date_arrivee.isoformat(),
            'date_depart': reservation.date_depart.isoformat(),
            'statut': reservation.statut
        }
        reservations_list.append(reservation_data)
    return jsonify(reservations_list)

@app.route('/api/reservations/<int:id>', methods=['GET'])
def get_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    reservation_data = {
        'id': reservation.id,
        'id_client': reservation.id_client,
        'id_chambre': reservation.id_chambre,
        'date_arrivee': reservation.date_arrivee.isoformat(),
        'date_depart': reservation.date_depart.isoformat(),
        'statut': reservation.statut
    }
    return jsonify(reservation_data)

@app.route('/api/reservations', methods=['POST'])
def creer_reservation():
    data = request.json
    id_client = data.get('id_client')
    id_chambre = data.get('id_chambre')
    date_arrivee = datetime.strptime(data.get('date_arrivee'), '%Y-%m-%d')
    date_depart = datetime.strptime(data.get('date_depart'), '%Y-%m-%d')

    # Vérification de la disponibilité de la chambre
    chambre = Chambre.query.get(id_chambre)
    if chambre is None:
        return jsonify({'success': False, 'message': 'La chambre spécifiée n\'existe pas'}), 400

    # Vérification de la disponibilité de la chambre pour les dates demandées
    reservations = Reservation.query.filter_by(id_chambre=id_chambre).all()
    for reservation in reservations:
        if (date_arrivee < reservation.date_depart) and (date_depart > reservation.date_arrivee):
            return jsonify({'success': False, 'message': 'La chambre n\'est pas disponible pour ces dates'}), 400

    # Création de la réservation
    reservation = Reservation(id_client=id_client, id_chambre=id_chambre, date_arrivee=date_arrivee, date_depart=date_depart)
    db.session.add(reservation)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Réservation créée avec succès.'}), 201

@app.route('/api/reservations/<int:id>', methods=['DELETE'])
def annuler_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    db.session.delete(reservation)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Réservation annulée avec succès.'}), 200

@app.route('/api/chambres', methods=['POST'])
def ajouter_chambre():
    data = request.json
    numero = data.get('numero')
    type = data.get('type')
    prix = data.get('prix')
    chambre = Chambre(numero=numero, type=type, prix=prix)
    db.session.add(chambre)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Chambre ajoutée avec succès.'}), 201

@app.route('/api/chambres/<int:id>', methods=['PUT'])
def modifier_chambre(id):
    chambre = Chambre.query.get_or_404(id)
    data = request.json
    chambre.numero = data.get('numero', chambre.numero)
    chambre.type = data.get('type', chambre.type)
    chambre.prix = data.get('prix', chambre.prix)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Chambre mise à jour avec succès.'}), 200

@app.route('/api/chambres/<int:id>', methods=['DELETE'])
def supprimer_chambre(id):
    chambre = Chambre.query.get_or_404(id)
    db.session.delete(chambre)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Chambre supprimée avec succès.'}), 200

@app.route('/clientlist.html')
def client_list():
    return render_template('clientlist.html')

@app.route('/chambrelist.html')
def chambre_list():
    return render_template('chambrelist.html')

@app.route('/reservationlist.html')
def reservation_list():
    return render_template('reservationlist.html')

@app.route('/clientform.html')
def client_form():
    return render_template('clientform.html')

@app.route('/chambreform.html')
def chambre_form():
    return render_template('chambreform.html')

@app.route('/reservationform.html')
def reservation_form():
    return render_template('reservationform.html')

@app.route('/modify-chambre/<int:id>')
def modify_chambre(id):
    chambre_details = {
        'id': id,
    }
    return render_template('modifychambre.html', chambre=chambre_details)

# Lancer Application Flash
if __name__ == '__main__':
    app.run(debug=True)
