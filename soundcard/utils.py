def match_device(id, devices):
    """Find id in a list of devices.

    id can be a platfom-specific id, a substring of the device name, or a
    fuzzy-matched pattern for the microphone name.

    """
    devices_by_id = {device.id: device for device in devices}
    devices_by_name = {device.name: device for device in devices}
    if id in devices_by_id:
        return devices_by_id[id]
    # try substring match:
    for name, device in devices_by_name.items():
        if id in name:
            return device
    # try fuzzy match:
    pattern = '.*'.join(id)
    for name, device in devices_by_name.items():
        if re.match(pattern, name):
            return device
    raise IndexError('no device with id {}'.format(id))
