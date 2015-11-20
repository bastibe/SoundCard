import numpy
from cffi import FFI

ffi = FFI()
ffi.cdef("""
typedef enum pa_stream_direction {
    PA_STREAM_NODIRECTION,
    PA_STREAM_PLAYBACK,
    PA_STREAM_RECORD,
    PA_STREAM_UPLOAD
} pa_stream_direction_t;

typedef enum pa_sample_format {
    PA_SAMPLE_U8,
    PA_SAMPLE_ALAW,
    PA_SAMPLE_ULAW,
    PA_SAMPLE_S16LE,
    PA_SAMPLE_S16BE,
    PA_SAMPLE_FLOAT32LE,
    PA_SAMPLE_FLOAT32BE,
    PA_SAMPLE_S32LE,
    PA_SAMPLE_S32BE,
    PA_SAMPLE_S24LE,
    PA_SAMPLE_S24BE,
    PA_SAMPLE_S24_32LE,
    PA_SAMPLE_S24_32BE,
    PA_SAMPLE_MAX,
    PA_SAMPLE_INVALID = -1
} pa_sample_format_t;

typedef struct pa_sample_spec {
    pa_sample_format_t format;
    uint32_t rate;
    uint8_t channels;
} pa_sample_spec;

typedef enum pa_channel_position {
    PA_CHANNEL_POSITION_INVALID = -1,
    PA_CHANNEL_POSITION_MONO = 0,

    PA_CHANNEL_POSITION_FRONT_LEFT,
    PA_CHANNEL_POSITION_FRONT_RIGHT,
    PA_CHANNEL_POSITION_FRONT_CENTER,
    PA_CHANNEL_POSITION_LEFT = PA_CHANNEL_POSITION_FRONT_LEFT,
    PA_CHANNEL_POSITION_RIGHT = PA_CHANNEL_POSITION_FRONT_RIGHT,
    PA_CHANNEL_POSITION_CENTER = PA_CHANNEL_POSITION_FRONT_CENTER,
    PA_CHANNEL_POSITION_REAR_CENTER,
    PA_CHANNEL_POSITION_REAR_LEFT,
    PA_CHANNEL_POSITION_REAR_RIGHT,
    PA_CHANNEL_POSITION_LFE,
    PA_CHANNEL_POSITION_SUBWOOFER = PA_CHANNEL_POSITION_LFE,
    PA_CHANNEL_POSITION_FRONT_LEFT_OF_CENTER,
    PA_CHANNEL_POSITION_FRONT_RIGHT_OF_CENTER,
    PA_CHANNEL_POSITION_SIDE_LEFT,
    PA_CHANNEL_POSITION_SIDE_RIGHT,
    PA_CHANNEL_POSITION_AUX0,
    PA_CHANNEL_POSITION_AUX1,
    PA_CHANNEL_POSITION_AUX2,
    PA_CHANNEL_POSITION_AUX3,
    PA_CHANNEL_POSITION_AUX4,
    PA_CHANNEL_POSITION_AUX5,
    PA_CHANNEL_POSITION_AUX6,
    PA_CHANNEL_POSITION_AUX7,
    PA_CHANNEL_POSITION_AUX8,
    PA_CHANNEL_POSITION_AUX9,
    PA_CHANNEL_POSITION_AUX10,
    PA_CHANNEL_POSITION_AUX11,
    PA_CHANNEL_POSITION_AUX12,
    PA_CHANNEL_POSITION_AUX13,
    PA_CHANNEL_POSITION_AUX14,
    PA_CHANNEL_POSITION_AUX15,
    PA_CHANNEL_POSITION_AUX16,
    PA_CHANNEL_POSITION_AUX17,
    PA_CHANNEL_POSITION_AUX18,
    PA_CHANNEL_POSITION_AUX19,
    PA_CHANNEL_POSITION_AUX20,
    PA_CHANNEL_POSITION_AUX21,
    PA_CHANNEL_POSITION_AUX22,
    PA_CHANNEL_POSITION_AUX23,
    PA_CHANNEL_POSITION_AUX24,
    PA_CHANNEL_POSITION_AUX25,
    PA_CHANNEL_POSITION_AUX26,
    PA_CHANNEL_POSITION_AUX27,
    PA_CHANNEL_POSITION_AUX28,
    PA_CHANNEL_POSITION_AUX29,
    PA_CHANNEL_POSITION_AUX30,
    PA_CHANNEL_POSITION_AUX31,

    PA_CHANNEL_POSITION_TOP_CENTER,
    PA_CHANNEL_POSITION_TOP_FRONT_LEFT,
    PA_CHANNEL_POSITION_TOP_FRONT_RIGHT,
    PA_CHANNEL_POSITION_TOP_FRONT_CENTER,
    PA_CHANNEL_POSITION_TOP_REAR_LEFT,
    PA_CHANNEL_POSITION_TOP_REAR_RIGHT,
    PA_CHANNEL_POSITION_TOP_REAR_CENTER,
    PA_CHANNEL_POSITION_MAX
} pa_channel_position_t;

#define PA_CHANNELS_MAX   32U

typedef struct pa_channel_map {
    uint8_t channels;
    pa_channel_position_t map[PA_CHANNELS_MAX];
} pa_channel_map;

typedef struct pa_buffer_attr {
    uint32_t maxlength;
    uint32_t tlength;
    uint32_t prebuf;
    uint32_t minreq;
    uint32_t fragsize;
} pa_buffer_attr;

typedef struct pa_simple pa_simple;

pa_simple* pa_simple_new(
    const char *server,
    const char *name,
    pa_stream_direction_t dir,
    const char *dev,
    const char *stream_name,
    const pa_sample_spec *ss,
    const pa_channel_map *map,
    const pa_buffer_attr *attr,
    int *error
    );

void pa_simple_free(pa_simple *s);

int pa_simple_write(pa_simple *s, const void *data, size_t bytes, int *error);

int pa_simple_drain(pa_simple *s, int *error);

int pa_simple_read(
    pa_simple *s,
    void *data,
    size_t bytes,
    int *error
    );

typedef uint64_t pa_usec_t;

pa_usec_t pa_simple_get_latency(pa_simple *s, int *error);

int pa_simple_flush(pa_simple *s, int *error);

const char* pa_strerror(int error);
""")


pa = ffi.dlopen('pulse-simple')


def _blocks(data, blocksize):
    start = 0
    while start < len(data):
        stop = min(start+blocksize, len(data))
        yield data[start:stop]
        start += blocksize


class _raise_pa_errors:
    def __enter__(self):
        self.error = ffi.new("int*")
        return self.error

    def __exit__(self, *args):
        if self.error[0] != 0:
            raise RuntimeError(pa.pa_strerror(self.error[0]))


def play(samples, samplerate):
    channels = samples.shape[1] if len(samples.shape) > 1 else 1
    spec = ffi.new("pa_sample_spec*", {'format': pa.PA_SAMPLE_FLOAT32LE,
                                       'channels': channels,
                                       'rate': samplerate})
    with _raise_pa_errors() as e:
        server = pa.pa_simple_new(ffi.NULL, # default server
                                  __name__.encode(), # program name
                                  pa.PA_STREAM_PLAYBACK,
                                  ffi.NULL, # use the default device
                                  b"play",  # description
                                  spec,
                                  ffi.NULL, # default channel map
                                  ffi.NULL, # default buffering
                                  e)
    try:
        for block in _blocks(samples, 1024):
            data = numpy.ascontiguousarray(block, numpy.float32)
            cdata = ffi.cast("float*", data.__array_interface__['data'][0])
            with _raise_pa_errors() as e:
                pa.pa_simple_write(server, cdata, data.nbytes, e)
        with _raise_pa_errors() as e:
            pa.pa_simple_drain(server, e)
    finally:
        pa.pa_simple_free(server)
