# Copyright (c) 2021 Ridecell India Pvt. Ltd. Please do not redistribute publicly.
import sqlalchemy
from flask import Flask, request
import json
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import math

Base = declarative_base()
DB_URL = 'postgres://parking_spots:jTZCD7JJkv35LXXM3jDjXz6RXcXcwqbH@c5bhzpimcc1s.us-west-2.rds.amazonaws.com:5432/parking_spots')
engine = create_engine(DB_URL)


class ParkingSpot(Base):
    __tablename__ = 'parking_spots'

    id = Column(Integer, primary_key=True)
    latitude = Column(String(30))
    longitude = Column(String(30))
    reserved = Column(Boolean)
    user_phone = Column(String(15))
    street_address = Column(Text)
    price = Column(Float)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)


app = Flask('api')


def is_dist_within_radius(slot, lt, ln, r):
  if math.sqrt((lt-slot.latitude)**2, (ln-slot.longitude)**2) <= r:
    return True
  else:
    return False


@app.route('/get_parking_available_near', methods=['POST'])
def get_available_slots_near():
  session = Session()
  d = request.get_json()
  lt = d['latitude']
  ln = d['longitude']
  r = d['radius']
  slots = session.query(ParkingSpot).filter(ParkingSpot.reserved==False).all()
  return json.dumps([s.as_dict() for s in slots if is_dist_within_radius(s, lt, ln, r)])


@app.route('/get_reserved_parking', methods=['POST'])
def get_reservations():
  session = Session()
  slots = session.query(ParkingSpot).filter(ParkingSpot.reserved==True).all()
  return json.dumps([s.as_dict() for s in slots])


@app.route('/parking_reserve', methods=['POST'])
def reserve_slot():
  d = request.get_json()
  if 'phone' not in d:
    return json.dumps({'error': 'User must provide a phone number'}), 400
  clean_phone_string = d['phone'].replace('-', '')
  try:
    int(clean_phone_string)
  except ValueError:
    return json.dumps({'error': 'User phone number has invalid'}), 400
  session = Session()
  if 'id' in d:
    slot = session.query(ParkingSpot).filter_by(id=d['id']).one_or_none()
  elif 'latitude' in d and 'longitude' in d:
    slot = session.query(ParkingSpot).filter_by(latitude=d['latitude']).filter_by(longitude=d['longitude']).one_or_none()
  else:
    return json.dumps({'error': 'Specified parking slot does not exist'}), 404
  if slot.reserved:
    return json.dumps({'error': 'Specified parking slot already reserved'}), 400
  slot.reserved = True
  slot.user_phone = d['phone']
  session.add(slot)
  session.commit()
  ret = "Slot reserved: " + str(slot.id)
  session.close()
  return ret


if __name__ == '__main__':
    app.run()
