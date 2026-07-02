# STRATOS Strategic Map & Database System

![STRATOS App Screenshot](screenshot.png)

## Overview
STRATOS is a comprehensive military strategic map application and database management system demonstration. It features a Flask-based web application with an interactive map, dashboards for tracking military assets, and robust database operations running on MySQL. This project doubles as a demonstration of complex database transaction scenarios (concurrency, deadlocks, isolation levels) and advanced SQL queries.

## Key Features
- **Interactive Map Dashboard:** Visualizes bases, enemy threats, and military assets across geographical locations.
- **Asset Management:** Tracks missiles, vehicles, personnel, and resource inventories (fuel, ammunition) assigned to various bases.
- **Mission Planning:** Facilitates attack simulations, readiness reporting, and logistics transfers.
- **Transaction Demonstrations:** Dedicated multi-threaded python scripts to showcase transaction behaviours, including commit, rollback, dirty reads, deadlocks, the lost update problem, and resolutions using `SERIALIZABLE` isolation.
- **Advanced SQL Queries:** Contains 15 complex SQL queries mapping to relational algebra operations for comprehensive data retrieval and analysis.

## Project Structure
- **`app.py`**: The main Flask application entry point, registering various blueprints for modular routing.
- **`routes/`**: Contains modular Flask blueprints handling backend logic for distinct components (`dashboard.py`, `bases.py`, `missiles.py`, `vehicles.py`, `enemy.py`, `map.py`, `missions.py`).
- **`db.py` & `utils.py`**: Database connection utility to interface with `STRATOS_DB`, and a utility module containing functions like the Haversine formula for geographic distance calculations.
- **`initialize.sql` & `seed.sql`**: SQL scripts establishing the `STRATOS_DB` schema and populating it with realistic seed data.
- **`app_queries_15.sql` & `queries_explanation.md`**: A suite of 15 advanced SQL queries designed for reporting and data retrieval, along with markdown documentation explaining their logic.
- **`run_demo.py` & `run_queries.py`**: Python scripts to execute and display the output of the predefined advanced SQL queries.
- **`transaction_demo.py`**: A robust, multi-threaded script that simulates concurrency to demonstrate database transaction conflicts (Lost Updates, Dirty Reads, Deadlocks) and their resolutions.
- **`templates/` & `static/`**: HTML views, CSS styles (`nav.css`, `style.css`), and frontend JavaScript logic (`common.js`, `map.js`) for rendering the interactive user interface. Includes GeoJSON data (`india.geojson`) for map rendering.

## Database Schema (`STRATOS_DB`)
The relational database models the military domain with tables including:
- **Bases & Enemy_Base**: Geographic locations and threat levels of friendly and hostile installations.
- **Personnel**: Tracking of military staff and availability status.
- **Vehicle_Type, Vehicle_Status & Vehicle_Inventory**: Comprehensive tracking of land, air, and sea vehicles.
- **Missile_Type & Missile_Inventory**: Arsenal inventory management per base.
- **Resource & Resource_Inventory**: Logistical tracking for consumables like fuel and ammunition.
- **Attack_Simulation, Readiness_Report & Logistics_Transfer**: Operational and strategic planning tables.

## Setup & Execution

### Prerequisites
- Python 3.8+
- MySQL Server
- Install dependencies (Flask, MySQL Connector):
  ```bash
  pip install -r requirements.txt
  ```

### Database Initialization
1. Ensure your MySQL server is active.
2. Create the schema and seed the database using the provided scripts:
   ```bash
   mysql -u <your_user> -p < initialize.sql
   mysql -u <your_user> -p STRATOS_DB < seed.sql
   ```
3. Set your database connection environment variables (if different from the defaults in `db.py`):
   ```bash
   export DB_HOST='localhost'
   export DB_USER='root'
   export DB_PASSWORD='your_password'
   export DB_NAME='STRATOS_DB'
   ```

### Running the Web Application
Start the Flask web server:
```bash
python app.py
```
Access the application by navigating to `http://localhost:5000` in your web browser.

### Running the Demonstrations
- **SQL Queries Demo:** 
  Execute the 15 advanced queries and view their formatted terminal output.
  ```bash
  python run_demo.py
  ```
- **Database Transactions Demo:** 
  Run the interactive transaction script to observe multi-threaded database scenarios and concurrency controls.
  ```bash
  python transaction_demo.py
  ```
