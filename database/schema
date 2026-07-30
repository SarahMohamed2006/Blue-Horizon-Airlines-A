
-- Blue Horizon Airlines
-- Database Schema


CREATE TABLE Airports (
    airport_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    weather VARCHAR(50) NOT NULL,
    runway_status VARCHAR(30) NOT NULL
);

CREATE TABLE Aircraft (
    aircraft_id INT PRIMARY KEY,
    tail_number VARCHAR(20) UNIQUE NOT NULL,
    model VARCHAR(50) NOT NULL,
    capacity INT NOT NULL,
    status VARCHAR(30) NOT NULL,
    current_airport_id INT,
    FOREIGN KEY (current_airport_id) REFERENCES Airports(airport_id)
);

CREATE TABLE Flights (
    flight_id INT PRIMARY KEY,
    flight_number VARCHAR(20) UNIQUE NOT NULL,
    origin_airport_id INT NOT NULL,
    destination_airport_id INT NOT NULL,
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    status VARCHAR(30) NOT NULL,
    aircraft_id INT,
    FOREIGN KEY (origin_airport_id) REFERENCES Airports(airport_id),
    FOREIGN KEY (destination_airport_id) REFERENCES Airports(airport_id),
    FOREIGN KEY (aircraft_id) REFERENCES Aircraft(aircraft_id)
);

CREATE TABLE Crew (
    crew_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    license_type VARCHAR(50),
    availability BOOLEAN NOT NULL,
    hours_flown_today DECIMAL(4,1) DEFAULT 0
);

CREATE TABLE FlightCrew (
    flight_id INT,
    crew_id INT,
    PRIMARY KEY (flight_id, crew_id),
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id),
    FOREIGN KEY (crew_id) REFERENCES Crew(crew_id)
);

CREATE TABLE Maintenance (
    maintenance_id INT PRIMARY KEY,
    aircraft_id INT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL,
    engineer VARCHAR(100) NOT NULL,
    FOREIGN KEY (aircraft_id) REFERENCES Aircraft(aircraft_id)
);

CREATE TABLE Employees (
    employee_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL
);
