-- Airports

INSERT INTO Airports
    (airport_id, name, weather, runway_status)
VALUES
    (1, 'Cairo International Airport', 'Clear', 'Open'),
    (2, 'Dubai International Airport', 'Sunny', 'Open'),
    (3, 'Heathrow Airport', 'Rainy', 'Open'),
    (4, 'Charles de Gaulle Airport', 'Cloudy', 'Open');

-- Aircraft

INSERT INTO Aircraft
    (aircraft_id, tail_number, model, capacity, status, current_airport_id)
VALUES
    (1, 'BH-A320', 'Airbus A320', 180, 'Available', 1),
    (2, 'BH-B737', 'Boeing 737', 189, 'In Service', 2),
    (3, 'BH-A321', 'Airbus A321', 220, 'Maintenance', 3);

-- Flights

INSERT INTO Flights
    (flight_id, flight_number, origin_airport_id, destination_airport_id,
     departure_time, arrival_time, status, aircraft_id)
VALUES
    (1, 'BH101', 1, 2,
     '2026-08-01 09:00:00',
     '2026-08-01 13:00:00',
     'Scheduled', 1),

    (2, 'BH218', 3, 4,
     '2026-08-01 15:30:00',
     '2026-08-01 17:00:00',
     'Delayed', 2),

    (3, 'BH350', 2, 1,
     '2026-08-02 08:15:00',
     '2026-08-02 11:45:00',
     'Cancelled', 3);

-- Crew

INSERT INTO Crew
    (crew_id, name, role, license_type, availability, hours_flown_today)
VALUES
    (1, 'Ahmed Hassan', 'Captain', 'ATPL', 1, 3.5),
    (2, 'Sara Ali', 'First Officer', 'CPL', 1, 2.0),
    (3, 'Mohamed Nabil', 'Cabin Crew', NULL, 1, 4.0),
    (4, 'Nour El-Din', 'Cabin Crew', NULL, 0, 8.0);

-- FlightCrew

INSERT INTO FlightCrew
    (flight_id, crew_id)
VALUES
    (1, 1),
    (1, 2),
    (1, 3),
    (2, 1),
    (2, 4);

-- Maintenance

INSERT INTO Maintenance
    (maintenance_id, aircraft_id, severity, status, engineer)
VALUES
    (1, 3, 'High', 'In Progress', 'Omar Salem'),
    (2, 2, 'Low', 'Completed', 'Youssef Adel');

-- Employees

INSERT INTO Employees
    (employee_id, name, role)
VALUES
    (1, 'Omar Hassan', 'Dispatcher'),
    (2, 'Sarah Ali', 'Operations Manager'),
    (3, 'Ahmed Nasser', 'Maintenance Engineer'),
    (4, 'Mariam Adel', 'Supervisor');

-- Aircraft Assignments

INSERT INTO AircraftAssignments
    (flight_id, aircraft_id, assigned_at, assignment_reason)
VALUES
    (2, 1,
     '2026-08-01 14:30:00',
     'Replacement aircraft assigned after technical issue');

-- Crew Assignments

INSERT INTO CrewAssignments
    (flight_id, crew_id, assigned_at, assignment_status)
VALUES
    (2, 2,
     '2026-08-01 14:40:00',
     'Assigned'),

    (2, 3,
     '2026-08-01 14:40:00',
     'Assigned');

-- Flight Events

INSERT INTO FlightEvents
    (flight_id, event_type, severity, description, reported_at, status)
VALUES
    (2,
     'Aircraft Failure',
     'High',
     'Hydraulic system issue detected',
     '2026-08-01 13:50:00',
     'Open'),

    (3,
     'Weather',
     'Medium',
     'Heavy rain caused cancellation',
     '2026-08-02 07:00:00',
     'Resolved');

-- Operation Decisions

INSERT INTO OperationDecisions
    (flight_id, employee_id, decision, reason, risk_assessment, created_at)
VALUES
    (2,
     2,
     'Assign Backup Aircraft',
     'Original aircraft unavailable',
     'Low operational risk after replacement aircraft validation.',
     '2026-08-01 14:35:00');

-- Notifications

INSERT INTO Notifications
    (flight_id, recipient, message, sent_at, status)
VALUES
    (2,
     'Operations Team',
     'Replacement aircraft assigned successfully.',
     '2026-08-01 14:36:00',
     'Sent');
