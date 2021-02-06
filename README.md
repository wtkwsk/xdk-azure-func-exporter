# XDK Sensor Visualization with InfluxDB & Grafana
The main goal of this proof-of-concept is to showcase the possibilties of the [Bosch XDK](https://developer.bosch.com/web/xdk) with it's variety of sensors and connecticity options for usage in IoT applications.
Also a possible rapid prototyping system architecture is shown below.
This repository contains the [Eclipse Mita](https://www.eclipse.org/mita/) code that is compiled into embedded c code for the XDK as well as the Azure Function source code and further related ressources.
## Architecture
![architecture](https://i.ibb.co/CBsGKpd/xdk.png) 

The code on the XDK consists of two event-loops that run after the initialization (connectivity & sensor setup) and are [compiled in single RTOS](https://www.eclipse.org/mita/concepts/) tasks. The main even-loop sends sensor data each 10 seconds over HTTP to an Azure Functions Endpoint. For productive use-cases this could be improved to use HTTPS.
For some sensors it makes little sense to simply send the current reading every 10 sec - think about acceleration data - rather you would like the data to be sampled over the whole 10-second period and transmit a single aggregated value (max/min/mean/avg/...). This is what the second event-loop is for: It reads the acceleration data (Z,Y,Z-axis) each 100ms and keeps only the max value. That way, shocks and short movements of the XDK can easily be detected.

The Azure Function processes each request by parsing the JSON body of the HTTP request, and constructing a corresponding [InfluxDB Line Protocol](https://docs.influxdata.com/influxdb/v1.8/write_protocols/line_protocol_tutorial/) string, that will then be used to insert the new data points into the InfluxDB.

For this PoC setup, InfluxDB and Grafana are hosted on a single Azure VM to save cost and reduce complexity. For both tools, SaaS offerings or custom high-available setups would be available. The VM is located in a virtual network that is split in three subnets. One for Azure Bastion, which is used for management access (over ssh) to the VM. One contains the VM itself, and the third one hosts the ApplicationGateway that functions as a web traffic load balancer for controlled user access to the [Grafana](https://grafana.com/) instance.
![Grafana Dashboard](https://i.ibb.co/kQyyyp3/grafana.png)
