from flask_sqlalchemy import SQLAlchemy
from datetime import date
from sqlalchemy.dialects.postgresql import UUID
import uuid

db = SQLAlchemy()

# ── Hinweis: fw_common.members wird NICHT als SQLAlchemy-Model definiert,
#    sondern per SQL direkt abgefragt (anderes Schema, PostgREST verwaltet).
#    Wir nutzen nur die member_id (UUID FK) für Verknüpfungen.

class Menu(db.Model):
    __tablename__ = 'menus'
    __table_args__ = {'schema': 'fw_food'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    datum = db.Column(db.Date, default=date.today, unique=True, index=True)
    beschreibung = db.Column(db.Text, nullable=False)
    zwei_menues_aktiv = db.Column(db.Boolean, default=False)
    menu1_name = db.Column(db.Text, nullable=True)
    menu2_name = db.Column(db.Text, nullable=True)
    anmeldefrist = db.Column(db.String(5), default='19:45')
    frist_aktiv = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    # Kompatibilität mit altem Code
    @property
    def description(self):
        return self.beschreibung

    @property
    def date(self):
        return self.datum

    @property
    def menu1(self):
        return self.menu1_name or self.beschreibung

    @property
    def menu2(self):
        return self.menu2_name if self.zwei_menues_aktiv else None

    @property
    def registration_deadline(self):
        return self.anmeldefrist

    @property
    def deadline_enabled(self):
        return self.frist_aktiv

    def is_registration_open(self):
        if not self.frist_aktiv:
            return True
        from datetime import datetime
        now = datetime.now()
        if now.date() != self.datum:
            return True
        deadline_time = datetime.strptime(self.anmeldefrist, '%H:%M').time()
        return now.time() < deadline_time

class Registration(db.Model):
    __tablename__ = 'registrations'
    __table_args__ = (
        db.UniqueConstraint('member_id', 'datum', name='_member_date_uc'),
        {'schema': 'fw_food'}
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    datum = db.Column(db.Date, default=date.today, index=True)
    menu_wahl = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    # Kompatibilität
    @property
    def date(self):
        return self.datum

    @property
    def menu_choice(self):
        return self.menu_wahl

    @property
    def user_id(self):
        return self.member_id

class Guest(db.Model):
    __tablename__ = 'guests'
    __table_args__ = (
        db.UniqueConstraint('datum', 'menu_wahl', name='_guest_date_menu_uc'),
        {'schema': 'fw_food'}
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    datum = db.Column(db.Date, default=date.today, index=True)
    menu_wahl = db.Column(db.Integer, default=1)
    anzahl = db.Column(db.Integer, default=0)

    # Kompatibilität
    @property
    def date(self):
        return self.datum

    @property
    def menu_choice(self):
        return self.menu_wahl

    @property
    def count(self):
        return self.anzahl

class RfidCard(db.Model):
    __tablename__ = 'rfid_cards'
    __table_args__ = {'schema': 'fw_food'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id = db.Column(db.Text, unique=True, nullable=False, index=True)
    member_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class MobileToken(db.Model):
    __tablename__ = 'mobile_tokens'
    __table_args__ = {'schema': 'fw_food'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = db.Column(UUID(as_uuid=True), unique=True, nullable=False)
    token = db.Column(db.Text, unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    @staticmethod
    def generate_token():
        import secrets
        return secrets.token_urlsafe(32)

class AdminLog(db.Model):
    __tablename__ = 'admin_log'
    __table_args__ = {'schema': 'fw_food'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zeitpunkt = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), index=True)
    admin_user = db.Column(db.Text, nullable=False, index=True)
    aktion = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text, nullable=True)

    # Kompatibilität
    @property
    def timestamp(self):
        return self.zeitpunkt

    @property
    def action(self):
        return self.aktion

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception:
            db.session.rollback()

class PresetMenu(db.Model):
    __tablename__ = 'preset_menus'
    __table_args__ = {'schema': 'fw_food'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.Text, nullable=False, unique=True)
    sort_order = db.Column(db.Integer, default=0)

    @staticmethod
    def get_all_ordered():
        return PresetMenu.query.order_by(PresetMenu.sort_order, PresetMenu.name).all()


# ── Helper: Mitglieder-Name aus fw_common.members laden ────────────────────
def get_member_name(member_id):
    """Lädt Vorname + Name für eine member_id aus fw_common.members."""
    if not member_id:
        return 'Unbekannt'
    result = db.session.execute(
        db.text('SELECT "Vorname", "Name" FROM fw_common.members WHERE id = :mid'),
        {'mid': str(member_id)}
    ).fetchone()
    if result:
        return f"{result[0] or ''} {result[1] or ''}".strip()
    return 'Unbekannt'


def get_member_by_personal_number(personal_number):
    """Sucht ein Mitglied anhand der Personalnummer (card_id Mapping)."""
    card = RfidCard.query.filter_by(card_id=personal_number).first()
    if card:
        return card.member_id
    return None


def get_member(member_id):
    """Einzelnes Mitglied als Dict laden."""
    if not member_id:
        return None
    result = db.session.execute(
        db.text('SELECT id, "Vorname", "Name" FROM fw_common.members WHERE id = :mid'),
        {'mid': str(member_id)}
    ).fetchone()
    if result:
        return {
            'id': str(result[0]),
            'name': f"{result[1] or ''} {result[2] or ''}".strip(),
            'vorname': result[1] or '',
            'nachname': result[2] or '',
        }
    return None


def get_all_members(active_only=True):
    """Alle Mitglieder aus fw_common.members laden (Read-only)."""
    sql = 'SELECT id, "Vorname", "Name" FROM fw_common.members'
    if active_only:
        sql += ' WHERE "Aktiv" = true'
    sql += ' ORDER BY "Name", "Vorname"'
    rows = db.session.execute(db.text(sql)).fetchall()
    members = []
    for r in rows:
        mid = str(r[0])
        members.append({
            'id': mid,
            'name': f"{r[1] or ''} {r[2] or ''}".strip(),
            'vorname': r[1] or '',
            'nachname': r[2] or '',
        })
    return members


def get_member_cards(member_id):
    """Alle RFID-Karten eines Mitglieds."""
    return RfidCard.query.filter_by(member_id=member_id).all()


def get_member_token(member_id):
    """MobileToken eines Mitglieds (oder None)."""
    return MobileToken.query.filter_by(member_id=member_id).first()
