from . import stream

class CommandError(Exception):
    """Tesla Model S vehicle command returned failure"""
    pass

class Vehicle:
    def __init__(self, vin, conn, payload, log):
        assert payload['vin'] == vin

        self._conn = conn
        self._data = payload
        self._log = log

    def __repr__(self):
        return "<Vehicle {}>".format(self.vin)

    # Helpers
    @property
    def vin(self):
        return self._data['vin']

    @property
    def id(self):
        return self._data['id']

    @property
    def vehicle_id(self):
        return self._data['vehicle_id']

    @property
    def state(self):
        return self._data['state']

    @property
    def email(self):
        return self._conn._email

    @property
    def stream_auth_token(self):
        return self._data['tokens'][0]

    # Stream entry generator for events defined in StreamEvents
    # (events should be an array of StreamEvents). This generator
    # generates tuples of an array of the requested events (preceded
    # by a timestamp) and a reference to the stream itself (which can
    # be closed to stop receiving events). This generator will
    # generate count number of events, or as many as it gets if count
    # is 0.
    def stream(self, events, count = 0):
        return stream.Stream(self).read_stream(events, count)

    def refresh(self):
        self._conn.vehicles(True)

    def request(self, verb):
        return self._conn.read_json('/api/1/vehicles/{}/data_request/{}' \
                                    .format(self.id, verb))['response']

    def command(self, verb, **kwargs):
        p = self._conn.read_json('/api/1/vehicles/{}/command/{}' \
                                 .format(self.id, verb), kwargs)

        args = []
        for a in kwargs:
            args.append("{} = {}".format(a, kwargs[a]))

        self._log.write("{}({}) called. Result was {}" \
                        .format(verb, ", ".join(args), p))

        if 'response' not in p or not p['response']:
            # Command returned failure, raise exception
            raise CommandError(p['error'])

        return p['response']

    # API getter properties
    @property
    def mobile_enabled(self):
        return self._conn.read_json('/api/1/vehicles/{}/mobile_enabled' \
                                    .format(self.id))['response']

    @property
    def data(self):
        return self._conn.read_json('/api/1/vehicles/{}/data' \
                                    .format(self.id)) #['response']

    @property
    def charge_state(self):
        return self.request('charge_state')

    @property
    def climate_state(self):
        return self.request('climate_state')

    @property
    def drive_state(self):
        return self.request('drive_state')

    @property
    def gui_settings(self):
        return self.request('gui_settings')

    @property
    def vehicle_state(self):
        return self.request('vehicle_state')

    # API commands
    def charge_port_door_open(self):
        return self.command('charge_port_door_open')

    def charge_port_door_close(self):
        return self.command('charge_port_door_close')

    def charge_standard(self):
        return self.command('charge_standard')

    def charge_max_range(self):
        return self.command('charge_max_range')

    def charge_start(self):
        return self.command('charge_start')

    def charge_stop(self):
        return self.command('charge_stop')

    @property
    def charge_limit(self):
        return self.charge_state['charge_limit_soc']

    @charge_limit.setter
    def charge_limit(self, limit):
        self.command('set_charge_limit', percent = limit)

    def flash_lights(self):
        return self.command('flash_lights')

    def honk_horn(self):
        return self.command('honk_horn')

    def remote_start_drive(self, password):
        return self.command('remote_start_drive', password = password)

    @property
    def speed_limit(self):
        return self.vehicle_state['speed_limit_mode']

    @speed_limit.setter
    def speed_limit(self, limit):
        return self.command('speed_limit_set_limit', limit_mph = limit)

    def activate_speed_limit(self, pin):
        return self.command('speed_limit_activate', pin = pin)

    def deactivate_speed_limit(self, pin):
        return self.command('speed_limit_deactivate', pin = pin)

    def clear_speed_limit_pin(self, pin):
        return self.command('speed_limit_clear_pin', pin = pin)

    def valet_mode(self, on, pin):
        return self.command('set_valet_mode', on = on, pin = pin)

    def reset_valet_pin(self):
        return self.command('reset_valet_pin')

    def sentry_mode(self, on):
        return self.command('set_sentry_mode', on = on)

    @property
    def locked(self):
        return self.vehicle_state['locked']

    @locked.setter
    def locked(self, lock):
        if lock:
            return self.command('door_lock')
        else:
            return self.command('door_unlock')

    def actuate_trunk(self):
        return self.command('actuate_trunk', which_trunk = 'rear')

    def actuate_frunk(self):
        return self.command('actuate_trunk', which_trunk = 'front')

    def sun_roof_control(self, state, percent = None):
        args = {'state': state}

        if state == 'move' and percent != None:
            args['percent'] = percent

        if state not in ('open', 'close', 'move', 'comfort', 'vent'):
            raise ValueError("Invalid sunroof state")

        return self.command('sun_roof_control', **args)

    def set_temps(self, driver, passenger):
        return self.command('set_temps', driver_temp = driver,
                            passenger_temp = passenger)

    def remote_seat_heater(self, heater, level):
        if heater not in range(0, 6):
            raise ValueError("Invalid seat heater: {}".format(heater))

        if level not in range(0, 4):
            raise ValueError("Invalid seat heater level: {}".format(level))

        return self.command('remote_seat_heater_request', heater = heater,
                            level = level)

    def remote_steering_wheel_heater(self, on):
        return self.command('remote_steering_wheel_heater_request', on = on)

    def auto_conditioning_start(self):
        return self.command('auto_conditioning_start')

    def auto_conditioning_stop(self):
        return self.command('auto_conditioning_stop')

    def media_toggle_playback(self):
        return self.command('media_toggle_playback')

    def media_next_track(self):
        return self.command('media_next_track')

    def media_prev_track(self):
        return self.command('media_prev_track')

    def media_next_fav(self):
        return self.command('media_next_fav')

    def media_prev_fav(self):
        return self.command('media_prev_fav')

    def media_volume_up(self):
        return self.command('media_volume_up')

    def media_volume_down(self):
        return self.command('media_volume_down')

    def navigation_request(self, where):
        return self.command('navigation_request',
                            type = 'share_ext_content_raw',
                            locale = 'en-US',
                            value = {
                                'android.intent.extra.TEXT': where
                            },
                            timestamp_ms = str(int(time.time())))

    def schedule_software_update(self, offset_sec):
        return self.command('schedule_software_update',
                            offset_sec = offset_sec)

    def cancel_software_update(self_sec):
        return self.command('cancel_software_update')

    def wake_up(self):
        d = self._conn.read_json('/api/1/vehicles/{}/wake_up' \
                                 .format(self.id), {})['response']

        # Update vehicle tokens if they're different from our cached
        # ones.
        tokens = d['tokens']

        if tokens != self._data['tokens']:
            self._data['tokens'] = tokens
            self._conn.save_state()

        return d
