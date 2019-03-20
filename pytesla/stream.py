import websocket
import base64
import json

#websocket.enableTrace(True)

class StreamEvents:
    SPEED            = 'speed'         # int, or str if shift_state is ''
    ODOMETER         = 'odometer'      # float
    STATE_OF_CHARGE  = 'soc'           # int
    ELEVATION        = 'elevation'     # int
    HEADING          = 'est_heading'   # int
    LATITUDE         = 'est_lat'       # float
    LONGITUDE        = 'est_lng'       # float
    POWER            = 'power'         # int
    SHIFT_STATE      = 'shift_state'   # str
    ALL              = ['speed', 'odometer', 'soc', 'elevation',
                        'est_heading', 'est_lat', 'est_lng', 'power',
                        'shift_state']

class Stream:
    def __init__(self, vehicle):
        self._vehicle = vehicle
        self._ws = None
        self._log = vehicle._log

    def __repr__(self):
        return "<Stream {}>".format(str(self._vehicle))

    def connect(self, events):
        self._log.debug("Stream connect")

        # Refresh our vehicles list to ensure we have an
        # up-to-date token.
        self._vehicle.refresh()

        self._ws = websocket \
            .create_connection("wss://streaming.vn.teslamotors.com/streaming/",
                               timeout = 10)

        auth_str = "{}:{}".format(self._vehicle.email,
                                  self._vehicle.stream_auth_token)

        self._ws.send(json.dumps({
            'msg_type': 'data:subscribe',
            'token': base64.b64encode(bytes(auth_str, 'utf-8')).decode('utf-8'),
            'value': ','.join(events),
            'tag': str(self._vehicle.vehicle_id)
        }))

    def close(self):
        if self._ws is not None:
            self._ws.close()
            self._ws = None

    def read_stream(self, events, count):
        self._log.debug("In read_stream(count = {})".format(count))
        total = 0
        iter_count = 0

        self.connect(events)

        msg = json.loads(self._ws.recv())

        if msg['msg_type'] != 'control:hello':
            self._log.debug("Expected control:hello message, got: {}" \
                            .format(str(msg)))

            return

        while True:
            n = 0

            iter_count += 1

            self._log.debug("In read_stream(), iteration {}".format(iter_count))

            try:
                msg = json.loads(self._ws.recv())

                self._log.debug("Received '{}'".format(str(msg)))

                if msg['msg_type'] == 'data:update':
                    data = msg['value'].split(',')

                    event = {'timestamp': data[0]}
                    for i in range(0, len(events)):
                        event[events[i]] = data[i + 1]

                    yield (event, self)

                    n += 1
                    total += 1

                    self._log.debug("In read_stream(), n = {}, total = {}" \
                                    .format(n, total))

                    if count != 0 and total >= count or not self._ws:
                        self._log.debug("In read_stream(), inner break")
                        break

                    continue

                if msg['msg_type'] == 'data:error':
                    self._log.write("Stream error {} received, closing socket" \
                                    .format(str(msg)))

                    self._ws.close()
                    self._ws = None

                    break
            except Exception as e:
                self._log.write("Stream read error: {}".format(str(e)))

                break

            # If we were closed, stop
            if not self._ws:
                self._log.debug("In read_stream(), closed")
                break

            # If we got as many or more events than we asked for, stop.
            if count != 0 and total >= count:
                self._log.debug("In read_stream(), done")
                break
