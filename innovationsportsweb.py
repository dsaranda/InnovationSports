from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
from flask_mqtt import Mqtt
import random


app = Flask(__name__)

# Crea una instancia del cliente MQTT
client = mqtt.Client()


# Inicializa el cliente de InfluxDB
influx_client = InfluxDBClient(host='localhost', port=8086)

# Verifica si la base de datos existe
databases = influx_client.get_list_database()
database_names = [db['name'] for db in databases]
print(database_names)
if 'sensores' not in database_names:
    print("No se encontró la base de datos 'sensores'.")
else:
    # Selecciona la base de datos
    influx_client.switch_database('sensores')
    print("Conectado correctamente a la base de datos 'sensores'.")

app.config['MQTT_BROKER_URL'] = '192.168.1.56'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

mqtt = Mqtt(app)

# Define la función de devolución de llamada on_connect
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscríbete al tópico "detectado" y "elapsed_time"
    client.subscribe("detectado")
    client.subscribe("detectado2")
    client.subscribe("detectado3")

elapsed_time = 0
elapsed_time2 = 0
elapsed_time3 = 0

# Configura el cliente MQTT
client.on_connect = on_connect

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('elapsed_time')
    mqtt.subscribe('elapsed_time2')
    mqtt.subscribe('elapsed_time3')


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global elapsed_time
    global elapsed_time2
    global elapsed_time3

    topic = message.topic
    payload = message.payload.decode()
    if topic == "elapsed_time":
        elapsed_time = int(payload)  
    elif topic == "elapsed_time2":
        elapsed_time2 = int(payload) 
    elif topic == "elapsed_time3":
        elapsed_time3 = int(payload)
        

counter = 0
def rutina_velocidad(client, userdata, msg):
    global counter
    if counter == 0:
        client.publish("encender_luz", "off")
    if msg.topic == "detectado" and msg.payload == b"si":
        luces = ["encender_luz2", "encender_luz3"]
        luz_aleatoria = random.choice(luces)
        client.publish(luz_aleatoria, "on")
        
        counter += 1
    elif msg.topic == "detectado2" and msg.payload == b"si":
        luces = ["encender_luz3", "encender_luz"]
        luz_aleatoria = random.choice(luces)
        client.publish(luz_aleatoria, "on")

    elif msg.topic == "detectado3" and msg.payload == b"si":
        luces = ["encender_luz2", "encender_luz"]
        luz_aleatoria = random.choice(luces)
        client.publish(luz_aleatoria, "on")

        if counter <= 35:
            guarda_velocidad()
        else:
            client.loop_stop()
            guarda_velocidad()
            client.disconnect()
            counter = 0
            
counter = 0          
def rutina_coordinacion(client, userdata, msg):
    global counter
    if counter == 0:
        client.publish("encender_luz", "off")
    if msg.topic == "detectado" and msg.payload == b"si":
        luces = ["encender_luz3"]
        luz_aleatoria = random.choice(luces)
        client.publish(luz_aleatoria, "on")
        
        counter += 1
        
    elif msg.topic == "detectado2" and msg.payload == b"si":
        luces = ["encender_luz", "encender_luz2"]
        luz_aleatoria = random.choice(luces)
        client.publish(luz_aleatoria, "on")
        
    
    elif msg.topic == "detectado3" and msg.payload == b"si":
        luces = ["encender_luz", "encender_luz2"]
        luz_aleatoria = random.choice(luces)
        client.publish(luz_aleatoria, "on")
        

        if counter <= 35:
            guarda_coordinacion()
        else:
            client.loop_stop()
            guarda_coordinacion()
            client.disconnect()
            counter = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ejecutar_velocidad', methods=['GET', 'POST'])
def ejecutar_velocidad():
    client.connect("192.168.1.56", 1883)
    client.publish("encender_luz", "on")
    client.on_message = rutina_velocidad
    client.subscribe("detectado")
    client.subscribe("detectado2")
    client.subscribe("detectado3")
    client.loop_forever()
    return render_template('index.html')

@app.route('/ejecutar_coordinacion', methods=['GET', 'POST'])
def ejecutar_coordinacion():
    client.connect("192.168.1.56", 1883)
    client.publish("encender_luz", "on")
    client.on_message = rutina_coordinacion
    client.subscribe("detectado")
    client.subscribe("detectado2")
    client.subscribe("detectado3")
    client.loop_forever()
    return render_template('index.html')

def guarda_velocidad():
    global elapsed_time
    global elapsed_time2
    global elapsed_time3

    dato = [
        {
            "measurement": "velocidad",
            "fields": {
                "Dispositivo1": elapsed_time
            }
        },
        {
            "measurement": "velocidad",
            "fields": {
                "Dispositivo2": elapsed_time2
            }
        },
        {
            "measurement": "velocidad",
            "fields": {
                "Dispositivo3": elapsed_time3
            }
        }
    ]

    if influx_client.write_points(dato):
        print("Se cargaron correctamente los datos")

def guarda_coordinacion():
    global elapsed_time
    global elapsed_time2
    global elapsed_time3

    dato = [
        {
            "measurement": "coordinacion",
            "fields": {
                "Dispositivo1": elapsed_time
            }
        },
        {
            "measurement": "coordinacion",
            "fields": {
                "Dispositivo2": elapsed_time2
            }
        },
        {
            "measurement": "coordinacion",
            "fields": {
                "Dispositivo3": elapsed_time3
            }
        }
    ]

    if influx_client.write_points(dato):
        print("Se cargaron correctamente los datos")

@app.route('/reiniciar_velocidad')
def reiniciar_velocidad():
    global elapsed_time, elapsed_time2, elapsed_time3
    elapsed_time = 0
    elapsed_time2 = 0
    elapsed_time3 = 0
    print(elapsed_time)
    print(elapsed_time2)
    print(elapsed_time3)
    dato = [
        {
            "measurement": "velocidad",
            "fields": {
                "Dispositivo1": elapsed_time
            }
        },
        {
            "measurement": "velocidad",
            "fields": {
                "Dispositivo2": elapsed_time2
            }
        },
        {
            "measurement": "velocidad",
            "fields": {
                "Dispositivo3": elapsed_time3
            }
        }
    ]

    if influx_client.write_points(dato):
        print("Se cargaron correctamente los datos")
    return render_template('index.html')

@app.route('/reiniciar_coordinacion')
def reiniciar_coordinacion():
    global elapsed_time, elapsed_time2, elapsed_time3
    elapsed_time = 0
    elapsed_time2 = 0
    elapsed_time3 = 0
    print(elapsed_time)
    print(elapsed_time2)
    print(elapsed_time3)
    dato = [
        {
            "measurement": "coordinacion",
            "fields": {
                "Dispositivo1": elapsed_time
            }
        },
        {
            "measurement": "coordinacion",
            "fields": {
                "Dispositivo2": elapsed_time2
            }
        },
        {
            "measurement": "coordinacion",
            "fields": {
                "Dispositivo3": elapsed_time3
            }
        }
    ]

    if influx_client.write_points(dato):
        print("Se cargaron correctamente los datos")
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')