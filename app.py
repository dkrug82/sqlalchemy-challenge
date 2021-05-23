#Set up dependincies
import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy import engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#Set up data base
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

#Reflect into a new model
Base = automap_base()

#Reflect tables
Base.prepare(engine, reflect=True)

#save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#Set up flask
app = Flask(__name__)

#Create routes
#Home route
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

#precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    #start session
    session = Session(engine)

    #found most recent date and one year prior to that date in data base
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
    year_ago = dt.datetime.strptime(recent_date, '%Y-%m-%d') - dt.timedelta(days=365)
    
    #Query data base for precp data during the last year of record
    results = session.query(Measurement.date, Measurement.prcp).\
                        filter(Measurement.date >= year_ago).\
                        order_by(Measurement.date).all()
    session.close()
    
    #Stored results into a list of necessary data
    precipitation_list = []
    for date, prcp in results:
        prcp_dict = {}
        prcp_dict[date] = prcp
        precipitation_list.append(prcp_dict)

    return jsonify(precipitation_list)
    #get rid of null                               DEBUG

#station route
@app.route("/api/v1.0/stations")
def stations():
    #start session
    session = Session(engine)
    #Query database for all station names
    results = session.query(Station.station).all()
    session.close()

    #Unpacked tubles into a list
    station_list = list(np.ravel(results))

    return jsonify(station_list)

#temperature route
@app.route("/api/v1.0/tobs")
def tobs():
    #start session
    session = Session(engine)

    #found most recent date and one year prior to that date in data base
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
    year_ago = dt.datetime.strptime(recent_date, '%Y-%m-%d') - dt.timedelta(days=365)

    #Query database for active stations
    active_station = session.query(Measurement.station, func.count(Measurement.id)).\
                                group_by(Measurement.station).\
                                order_by(func.count(Measurement.id).desc()).all()

    #Retrived the most active station
    most_active_station = active_station[0][0]
    
    #Query database for the last year of temperature record at the most active station
    results = session.query(Measurement.date, Measurement.tobs).\
                        filter(Measurement.date >= year_ago).\
                        filter(Measurement.station == most_active_station).\
                        order_by(Measurement.date).all()
    #End session
    session.close()

    #Unpacked tubles into a list
    result_list = list(np.ravel(results))
    return jsonify(result_list)

#Routes for user chosen start and end dates for temperature records
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>") 
def stats(start=None, end=None):
    #Start session
    session = Session(engine)

    #Assign query to a variable for each min, max, and average temps
    TMIN = session.query(func.min(Measurement.tobs))
    TMAX = session.query(func.max(Measurement.tobs))
    TAVG = session.query(func.avg(Measurement.tobs))

    #Use if statement to iterate through the database to filter by start and end dates
    if end is not None:
        TMIN = TMIN.filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()
        TMAX = TMAX.filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()
        TAVG = TAVG.filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()
    #Added Else statement to be used if only a start date is provided
    else:
        TMIN = TMIN.filter(Measurement.date >= start).all()
        TMAX = TMAX.filter(Measurement.date >= start).all()
        TAVG = TAVG.filter(Measurement.date >= start).all()

    #End session    
    session.close()
    
    #Unpack tuples and convert to a list. Add the lists for each function to a dictionary
    temp = {"TMIN":list(np.ravel(TMIN))[0],
            "TMAX":list(np.ravel(TMAX))[0],
            "TAVG":list(np.ravel(TAVG))[0]}
   
    return jsonify(temp)



if __name__ == '__main__':
    app.run(debug=True)