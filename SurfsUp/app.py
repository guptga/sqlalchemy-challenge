import os
import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
db_dir = "\sqlalchemy-challenge\Resources\hawaii.sqlite"
#print(f'os.path.abspath(db_dir): {str(os.path.abspath(db_dir))}')
print(os.getcwd()+db_dir)
SQLALCHEMY_DATABASE_URL = "sqlite:///" + os.getcwd()+db_dir
#os.path.abspath(db_dir)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

#engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

Base = automap_base()
Base.prepare(engine, reflect=True)

Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes for Hawaii Weather Data:<br/><br>"
        f"-- Daily Precipitation Totals for Last Year: <a href=\"/api/v1.0/precipitation\">/api/v1.0/precipitation<a><br/>"
        f"-- Active Weather Stations: <a href=\"/api/v1.0/stations\">/api/v1.0/stations<a><br/>"
        f"-- Daily Temperature Observations for most active station USC00519281 for Last Year: <a href=\"/api/v1.0/tobs\">/api/v1.0/tobs<a><br/>"
        f"-- Min, Average & Max Temperatures for Date Range: /api/v1.0/trip/yyyy-mm-dd&yyyy-mm-dd<br>"
        f"NOTE: If no end-date is provided, the trip api calculates stats through 08/23/17<br>" 
    )

@app.route('/api/v1.0/precipitation')
def precipitation():
  

    session = Session(engine)
    lateststr = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    latestdate = dt.datetime.strptime(lateststr, '%Y-%m-%d')
    querydate = dt.date(latestdate.year -1, latestdate.month, latestdate.day)
    sel = [Measurement.date,Measurement.tobs]
    queryresult = session.query(*sel).filter(Measurement.date >= querydate).all()
    session.close()

    precipitation = []
    for date, prcp in queryresult:
        prcp_dict = {}
        prcp_dict["Date"] = date
        prcp_dict["Precipitation"] = prcp
        precipitation.append(prcp_dict)

    return jsonify(precipitation)


@app.route('/api/v1.0/stations')
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
  # Return a list of active weather stations in Hawaii
    sel = [Measurement.station]
    active_stations = session.query(*sel).\
        group_by(Measurement.station).all()
    session.close()

    # Return a dictionary with the date as key and the daily precipitation total as value
    # Convert list of tuples into normal list and return the JSonified list
    list_of_stations = list(np.ravel(active_stations)) 
    return jsonify(list_of_stations)

@app.route('/api/v1.0/tobs')
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query the last 12 months of temperature observation data for the most active station
    start_date = '2016-08-23'
    sel = [Measurement.date, 
        Measurement.tobs]
    station_temps = session.query(*sel).\
            filter(Measurement.date >= start_date, Measurement.station == 'USC00519281').\
            group_by(Measurement.date).\
            order_by(Measurement.date).all()

    session.close()
  # Return a dictionary with the date as key and the daily temperature observation as value
    observation_dates = []
    temperature_observations = []

    for date, observation in station_temps:
        observation_dates.append(date)
        temperature_observations.append(observation)
    
    most_active_tobs_dict = dict(zip(observation_dates, temperature_observations))

    return jsonify(most_active_tobs_dict)

@app.route("/api/v1.0/trip/<start_date>")
def trip1(start_date, end_date='2017-08-23'):
    # Calculate minimum, average and maximum temperatures for the range of dates starting with start date.
    # If no end date is provided, the function defaults to 2017-08-23.

    session = Session(engine)
    query_result = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    session.close()

    trip_stats = []
    for min, avg, max in query_result:
        trip_dict = {}
        trip_dict["Min"] = min
        trip_dict["Average"] = avg
        trip_dict["Max"] = max
        trip_stats.append(trip_dict)

    # If the query returned non-null values return the results,
    # otherwise return an error message
    if trip_dict['Min']: 
        return jsonify(trip_stats)
    else:
        return jsonify({"error": f"Date {start_date} not found or not formatted as YYYY-MM-DD."}), 404
  
@app.route("/api/v1.0/trip/<start_date>&<end_date>")
def trip2(start_date, end_date):
    # Calculate minimum, average and maximum temperatures for the range of dates starting with start date.
    # If no valid end date is provided, the function defaults to 2017-08-23.

    session = Session(engine)
    query_result = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    session.close()

    trip_stats = []
    for min, avg, max in query_result:
        trip_dict = {}
        trip_dict["Min"] = min
        trip_dict["Average"] = avg
        trip_dict["Max"] = max
        trip_stats.append(trip_dict)

    # If the query returned non-null values return the results,
    # otherwise return an error message
    if trip_dict['Min']: 
        return jsonify(trip_stats)
    else:
        return jsonify({"error": f"Date(s) not found, invalid date range or dates not formatted correctly."}), 404
if __name__ == '__main__':
    app.run(debug=True)