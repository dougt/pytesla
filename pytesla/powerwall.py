import urllib
import json
import ssl

try:
    from http.client import HTTPSConnection, HTTPException
except:
    from httplib import HTTPSConnection, HTTPException

class NoOpLogger:
    def write(self, str):
        pass
    def debug(self, str):
        pass

# Session class for connecting to the local powerwall gateway.
class LocalSession:
    def __init__(self, host, log):
        self._host = host

        if log == None:
            log = NoOpLogger()

        self._log = log
        self._is_open = False

        self._context = ssl._create_unverified_context()

    def open(self):
        self._httpconn = HTTPSConnection(self._host,
                                         context = self._context)
        #self._httpconn.set_debuglevel(5)

        self._is_open = True

    def close(self):
        if self._is_open:
            self._httpconn.close()
            self._httpconn = None

            self._is_open = False

    def request(self, path, post_data = None):
        """
        Send a request for the path 'path'. Does a POST of post_data if given,
        else a GET of the given path.
        """

        if not self._is_open:
            self.open()

        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        if type(post_data) == dict:
            post = json.dumps(post_data)
        else:
            post = post_data

        self._httpconn.request("GET" if post is None else "POST",
                               path, post, headers)
        response = self._httpconn.getresponse()

        if response.status != 200:
            # Make sure we read the response body, or we won't be able to
            # re-use the connection for following request.
            response.read()

            self._log.write("{} request failed: {}: {}" \
                            .format(path, response.status, response.reason))

            raise HTTPException(response.status, response.reason)

        return response

    def read_json(self, path, post_data = None):
        request = self.request(path, post_data)

        data = request.read().decode('utf-8')

        request.close()

        return json.loads(data)

class Powerwall:
    def __init__(self, host, log = None):
        self._host = host

        if log == None:
            log = NoOpLogger()

        self._log = log

        self.session = LocalSession(host, log)

    def aggregates(self):
        return self.session.read_json('/api/meters/aggregates')

    def site(self):
        return self.session.read_json('/api/meters/site')

    def solar(self):
        return self.session.read_json('/api/meters/solar')

    # State of Charge / State of Energy
    def soe(self):
        return self.session.read_json('/api/system_status/soe')

    def sitemaster(self):
        return self.session.read_json('/api/sitemaster')

    def powerwalls(self):
        return self.session.read_json('/api/powerwalls')

    def registration(self):
        return self.session.read_json('/api/customer/registration')

    def grid_status(self):
        return self.session.read_json('/api/system_status/grid_status')

    # Not working? 403 Forbidden
    #def update_status(self):
    #    return self.session.read_json('/api/system/update/status')

    def site_info(self):
        return self.session.read_json('/api/site_info')

    def site_name(self):
        return self.session.read_json('/api/site_info/site_name')

    def status(self):
        return self.session.read_json('/api/status')

    def grid_faults(self):
        return self.session.read_json('/api/system_status/grid_faults')

    def stop(self):
        return self.session.read_json('/api/sitemaster/stop')

    def run(self):
        return self.session.read_json('/api/sitemaster/run')

    def completed(self):
        return self.session.read_json('/api/config/completed')
