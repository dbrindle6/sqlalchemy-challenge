# Import the dependencies.
from flask import Flask, jsonify
import numpy as np
import datetime as dt
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()
Base.prepare(autoload_with=engine)  # Use autoload_with instead of reflect=True

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# Home Route
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation - Last 12 months of precipitation data<br/>"
        f"/api/v1.0/stations - List of weather stations<br/>"
        f"/api/v1.0/tobs - Temperature Observations for the most active station<br/>"
        f"/api/v1.0/&lt;start&gt; - TMIN, TAVG, TMAX from start date<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt; - TMIN, TAVG, TMAX for date range"
    )

# Precipitation Route
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the last 12 months of precipitation data."""
    session = Session(engine)  # Create session inside route
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).\
        order_by(Measurement.date).all()

    session.close()  # Close session

    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    
    return jsonify(precipitation_dict)

# Stations Route
@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations."""
    session = Session(engine)
    stations_data = session.query(Station.station).all()
    session.close()

    stations_list = list(np.ravel(stations_data))
    return jsonify(stations_list)

# Temperature Observation Route (tobs)
@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations for the most active station in the last 12 months."""
    session = Session(engine)
    most_active_station = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]

    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    temperature_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= one_year_ago).all()

    session.close()

    temperature_list = list(np.ravel(temperature_data))
    return jsonify(temperature_list)

# Start Route
@app.route("/api/v1.0/<start>")
def temp_range_start(start=None):
    """Return TMIN, TAVG, TMAX for dates greater than or equal to the start date."""
    start = start.strip()  # Remove any extra spaces
    try:
        dt.datetime.strptime(start, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid start date format. Use YYYY-MM-DD."}), 400

    session = Session(engine)
    temp_stats = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start).all()
    
    session.close()

    temp_stats_list = list(np.ravel(temp_stats))
    return jsonify(temp_stats_list)

# Start/End Route
@app.route("/api/v1.0/<start>/<end>")
def temp_range(start=None, end=None):
    """Return TMIN, TAVG, TMAX for the dates greater than or equal to the start date (or between start and end)."""
    start = start.strip()
    end = end.strip()
    
    # Date validation using try-except
    try:
        dt.datetime.strptime(start, "%Y-%m-%d")
        dt.datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    
    session = Session(engine)
    temp_stats = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()

    session.close()

    temp_stats_list = list(np.ravel(temp_stats))
    return jsonify(temp_stats_list)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
