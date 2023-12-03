from flask import Flask, jsonify, request
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os #provides ways to access the Operating System and allows us to read the environment variables

load_dotenv()

app = Flask(__name__)

uri = "bolt://localhost:7687"
user = "neo4j"
password = "test1234"
driver = GraphDatabase.driver(uri, auth=(user, password),database="neo4j")

def get_employees(tx):
    query = "MATCH (e:Employee) RETURN e"
    results = tx.run(query).data()
    movies = [{'name': result['e']['name'], 'surname': result['e']['surname'], 'position': result['e']['position']} for result in results]
    return movies

@app.route('/employees', methods=['GET'])
def get_employees_route():
    with driver.session() as session:
        employees = session.execute_read(get_employees)

    response = {'employees': employees}
    return jsonify(response)

def get_employee(tx, name, surname):
    query = "MATCH (e:Employee) WHERE e.name=$name AND e.surname=$surname RETURN e"
    result = tx.run(query, name=name, surname=surname).data()

    if not result:
        return None
    else:
        return {'name': result[0]['e']['name'], 'surname': result[0]['e']['surname'], 'position': result[0]['e']['position']}

@app.route('/employees/<string:fullname>', methods=['GET'])
def get_employee_route(fullname):
    fullname = fullname.split("+")
    with driver.session() as session:
        employee = session.execute_read(get_employee, fullname[0], fullname[1])

    if not employee:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'employee': employee}
        return jsonify(response)

def add_employee(tx, name, surname, position, department):
    query = "CREATE (e:Employee {name: $name, surname: $surname, position: $position})-[:WORKS_IN]->(d:Department {name: $department})"
    tx.run(query, name=name, surname=surname, position=position, department=department)


@app.route('/employees', methods=['POST'])
def add_employee_route():
    name = request.json['name']
    surname = request.json['surname']
    position = request.json['position']
    department = request.json['department']

    with driver.session() as session:
        session.write_transaction(add_employee, name, surname, position, department)

    response = {'status': 'success'}
    return jsonify(response)


def update_employee(tx, id, new_name, new_surname, new_position):
    query = "MATCH (e:Employee) WHERE e.name=$name ADN e.surname=$surname RETURN e"
    result = tx.run(query, name=name, surname=surname).data()

    if not result:
        return None
    else:
        query = "MATCH (e:Employee) WHERE e.name=$name ADN e.surname=$surname SET e.name=$new_name, e.surname=$new_surname, e.position=$new_position"
        tx.run(query, id=id, new_name=new_name, new_surname=new_surname, new_position=new_position)
        return {'name': new_name, 'surname': new_surname, 'position': new_position}


@app.route('/employees/<string:id>', methods=['PUT'])
def update_employee_route(id):
    id = id
    new_name = request.json['name']
    new_surname = request.json['surname']
    new_position = request.json['position']

    with driver.session() as session:
        movie = session.write_transaction(update_employee, id, new_name, new_surname, new_position)

    if not movie:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)


def delete_employee(tx, id):
    query = "MATCH (e:Employee) WHERE e.id=$id RETURN e"
    result = tx.run(query, id=id).data()

    if not result:
        return None
    else:
        query = "MATCH (e:Employee) WHERE e.id=$id DETACH DELETE e"
        tx.run(query, id=id)
        return {'id': id}

@app.route('/employees/<string:id>', methods=['DELETE'])
def delete_employee_route(id):
    with driver.session() as session:
        movie = session.write_transaction(delete_employee, id)

    if not movie:
        response = {'message': 'Movie not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)

def get_employee_subordinates(tx, id):
    query = "MATCH (e:Employee)-[:MANAGES]->(e2:Employee) WHERE e.id=$id RETURN e2"
    result = tx.run(query, name=name, surname=surname).data()

    if not result:
        return None
    else:
        return {'name': result[0]['e']['name'], 'surname': result[0]['e']['surname'], 'position': result[0]['e']['position']}

@app.route('/employees/<string:id>/subordinates', methods=['GET'])
def get_subordinates_route(id):
    with driver.session() as session:
        employee = session.execute_read(get_employee_subordinates, id)

    if not employee:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'employee': employee}
        return jsonify(response)

def get_department_employees(tx, id):
    query = "MATCH (e:Employee)-[:WORKS_IN]->(d:Department) WHERE d.id=$id RETURN e"
    result = tx.run(query, name=name, surname=surname).data()

    if not result:
        return None
    else:
        return {'name': result[0]['e']['name'], 'surname': result[0]['e']['surname'], 'position': result[0]['e']['position']}

@app.route('/departments/<string:id>/employees', methods=['GET'])
def get_department_employees_route(id):
    with driver.session() as session:
        employees = session.execute_read(get_department_employees, id)

    if not employees:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'employees': employees}
        return jsonify(response)

if __name__ == '__main__':
    app.run()
