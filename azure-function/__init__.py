import os
import time
import logging
import numbers
from influxdb import InfluxDBClient

import azure.functions as func

# transforms any type of number into a float
# doesn't change all other types
def save_num(n):
    if isinstance(n, numbers.Number):
        return float(n)
    return n

# Metric object, that can gradually be build up with fields and tags
# Can be exported as valid influxdb(1.8) line protocol string
# See: https://docs.influxdata.com/influxdb/v1.8/write_protocols/line_protocol_tutorial/
class Metric(object):
    def __init__(self, measurement):
        self.measurement = measurement
        self.field_set = dict()
        self.tag_set = dict()
        self.timestamp = None

    def add_timestamp(self, timestamp):
        self.timestamp = timestamp

    def add_tag(self, tag, value):
        self.tag_set[str(tag)] = str(value)

    def add_field(self, field, value):
        self.field_set[str(field)] = str(value)

    def __str__(self):
        line_protocol = self.measurement

        tags = list()
        for key, value in self.tag_set.items():
            tags.append("{}={}".format(key, value))
        if len(tags) > 0 :
            line_protocol += ",{}".format(",".join(tags))

        fields = list()
        for key, value in self.field_set.items():
            fields.append("{}={}".format(key, value))
        if len(fields) > 0 :
            line_protocol += " {}".format(",".join(fields))

        if self.timestamp is not None:
            line_protocol += " {}".format(self.timestamp)

        return line_protocol

def main(req: func.HttpRequest) -> func.HttpResponse:
    
    influx_password = os.environ.get('INFLUX_PW')
    if not influx_password:
        raise Exception("InfluxDB password not set in environmental variables!")
        return func.HttpResponse(status_code=500)

    influx_user = os.environ.get('INFLUX_USER')
    if not influx_user:
        raise Exception("InfluxDB username not set in environmental variables!")
        return func.HttpResponse(status_code=500)

    influx_host = os.environ.get('INFLUX_HOST')
    if not influx_host:
        raise Exception("InfluxDB host not set in environmental variables!")
        return func.HttpResponse(status_code=500)

    try:
        body = req.get_json()
        logging.debug("Parsed request body: {}".format(body))

        # InfluxDB connection
        client = InfluxDBClient(host=influx_host, port=8086, username=influx_user, password=influx_password, ssl=False)
        current_milli_time = round(time.time() * 1000)

        # Build valid line protocol string
        metric = Metric("sensordata")
        metric.add_timestamp(current_milli_time)

        for key, value in body.items():
            if key == "device-id":
                metric.add_tag('deviceid', value)
            else:
                metric.add_field(key, save_num(value))

        data_points = [str(metric)]
        logging.info(data_points)

        # Write to Database
        client.write_points(data_points, database='xdk', time_precision='ms', batch_size=1, protocol='line')

        # Return sucess
        return func.HttpResponse(status_code=200)

    except ValueError:
        logging.error("Could not parse request body into valid JSON:")
        logging.error(req.get_body())
        return func.HttpResponse(status_code=400)

    except KeyError:
        logging.error("Key-Error:")
        logging.error(body)
        return func.HttpResponse(status_code=400)
    
    except Exception as e:
        logging.error("An unexpected error occured: \n{}".format(e))
        raise
        return func.HttpResponse(status_code=500)
