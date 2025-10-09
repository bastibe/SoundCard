import re

def match_device(id, devices):
    """Find id in a list of devices.

    id can be a platfom specific id, a substring of the device name, or a
    fuzzy-matched pattern for the microphone name.
    """
    devices_by_id = {device.id: device for device in devices}
    real_devices_by_name = {
        device.name: device for device in devices
        if not getattr(device, 'isloopback', True)}
    loopback_devices_by_name = {
        device.name: device for device in devices
        if getattr(device, 'isloopback', True)}
    if id in devices_by_id:
        return devices_by_id[id]
    for device_map in real_devices_by_name, loopback_devices_by_name:
        if id in device_map:
            return device_map[id]
    # MacOS/coreaudio uses integer IDs where string operations of course
    # make no sense.
    if isinstance(id, int):
        raise IndexError('no device with id {}'.format(id))
    # try substring match:
    for device_map in real_devices_by_name, loopback_devices_by_name:
        for name, device in device_map.items():
            if id in name:
                return device
    # try fuzzy match:
    id_parts = [re.escape(c) for c in id]
    pattern = '.*'.join(id_parts)
    for device_map in real_devices_by_name, loopback_devices_by_name:
        for name, device in device_map.items():
            if re.search(pattern, name):
                return device
    raise IndexError('no device with id {}'.format(id))
