import flask
from flask import Response
import urllib.request
import json
import uuid
import re
import pandas as pd
from ksql import KSQLAPI
from confluent_kafka import Consumer


app = flask.Flask(__name__)
app.config["DEBUG"] = True

def api_json_to_dataframe(data):
    """ ksqldb api return data transfer to pandas dataframe """
    pattern = re.compile(r'`\w+`')
    cols = [x[1:-1] for x in pattern.findall(data[0]['header']['schema'])]
    vals = []
    for x in data[1:]:
        #print(x)
        vals.append(x['row']['columns'])
    df = pd.DataFrame(columns=cols,data=vals)
    return df


@app.route('/', methods=['GET'])
def home():
    data = {'api_version':'v1'}
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/ksql', methods=['POST'])
def ksql():
    # server config setting
    kafka_server = '172.16.43.68:9092'
    conf = {'bootstrap.servers': kafka_server,
            'group.id': uuid.uuid4().hex,
            'auto.offset.reset': 'earliest'}
            #'print.key': True}
    consumer = Consumer(conf)
    consumer.subscribe(['TBL_SUM_PAYMENTWD_TXN'])
    
    # start pull message 
    message = []
    keys = []
    while True:
        msg = consumer.poll(1)
    
        if msg is None:
            break
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue
        message.append(msg.value().decode('utf-8'))
        keys.append(msg.key().decode('utf-8'))
    consumer.close()
    
    query_keys = ','.join(["'%s'"%x for x in set(keys)])
    # query data from ksql api
    data = {
            "ksql": "select * FROM TBL_SUM_PAYMENTWD_TXN where PaymentTransactionNo in (%s);"%query_keys,
            "streamsProperties": {}
    }
    
    req = urllib.request.Request('http://172.16.43.68:8088/query',
                                 data=json.dumps(data).encode('utf8'),
                                 headers={'Accept':'application/vnd.ksql.v1+json'})
    response = urllib.request.urlopen(req)
    reqs = json.loads(response.read())
    df = api_json_to_dataframe(reqs)
    
    data = {'api_version':'v1'}
    response = Response(
        response=json.dumps(df.to_json()),
        status=200,
        mimetype='application/json'
    )
    return response


if __name__ == '__main__':
    app.run()
    #app.run(host="0.0.0.0", port=5000, debug=True)
