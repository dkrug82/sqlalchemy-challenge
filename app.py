import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy import engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

Base = automap_base()

Base.prepare(engine, reflect=True)

Measurement = Base.classes.measurement
Station = Base.classes.station


app = Flask(__name__)

@app.route("/")
def welcome():

    return(
        f"Welcome to my Hawaii weather API!<br/>"
        f"The available routes are:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end" 
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
    year_ago = dt.datetime.strptime(recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    
    results = session.query(Measurement.date, Measurement.prcp).\
                        filter(Measurement.date >= year_ago).\
                        order_by(Measurement.date).all()
    session.close()
    
    precipitation_list = []
    for date, prcp in results:
        prcp_dict = {}
        prcp_dict[date] = prcp
        precipitation_list.append(prcp_dict)

    return jsonify(precipitation_list)
    #get rid of null                               DEBUG


@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = session.query(Station.station).all()
    session.close()

    station_list = list(np.ravel(results))

    return jsonify(station_list)


@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
    year_ago = dt.datetime.strptime(recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    active_station = session.query(Measurement.station, func.count(Measurement.id)).\
                                group_by(Measurement.station).\
                                order_by(func.count(Measurement.id).desc()).all()

    most_active_station = active_station[0][0]
    
    results = session.query(Measurement.date, Measurement.tobs).\
                        filter(Measurement.date >= year_ago).\
                        filter(Measurement.station == most_active_station).\
                        order_by(Measurement.date).all()
    
    session.close()
    result_list = list(np.ravel(results))
    return jsonify(result_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>") 
def stats(start=None, end=None):
    session = Session(engine)
    TMIN = session.query(func.min(Measurement.tobs))
    TMAX = session.query(func.max(Measurement.tobs))
    TAVG = session.query(func.avg(Measurement.tobs))
    if end is not None:
        TMIN = TMIN.filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()
        TMAX = TMAX.filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()
        TAVG = TAVG.filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()
    else:
        TMIN = TMIN.filter(Measurement.date >= start).all()
        TMAX = TMAX.filter(Measurement.date >= start).all()
        TAVG = TAVG.filter(Measurement.date >= start).all()
        
    session.close()
    
    temp = {"TMIN":list(np.ravel(TMIN))[0],
            "TMAX":list(np.ravel(TMAX))[0],
            "TAVG":list(np.ravel(TAVG))[0]}
   
    return jsonify(temp)


#TMIN, TAVG, TMAX
if __name__ == '__main__':
    app.run(debug=True)