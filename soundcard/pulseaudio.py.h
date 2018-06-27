
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

typedef enum pa_channel_map_def {
    PA_CHANNEL_MAP_AIFF,
    PA_CHANNEL_MAP_ALSA,
    PA_CHANNEL_MAP_AUX,
    PA_CHANNEL_MAP_WAVEEX,
    PA_CHANNEL_MAP_OSS,
    PA_CHANNEL_MAP_DEF_MAX,
    PA_CHANNEL_MAP_DEFAULT = PA_CHANNEL_MAP_AIFF
} pa_channel_map_def_t;

pa_channel_map* pa_channel_map_init_auto(pa_channel_map *m, unsigned channels, pa_channel_map_def_t def);
int pa_channel_map_valid(const pa_channel_map *map);

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

typedef struct pa_mainloop pa_mainloop;
pa_mainloop *pa_mainloop_new(void);
void pa_mainloop_free(pa_mainloop* m);
int pa_mainloop_run(pa_mainloop *m, int *retval);
void pa_mainloop_quit(pa_mainloop *m, int retval);

typedef struct pa_threaded_mainloop pa_threaded_mainloop;
pa_threaded_mainloop *pa_threaded_mainloop_new(void);
int pa_threaded_mainloop_start(pa_threaded_mainloop *m);
void pa_threaded_mainloop_stop(pa_threaded_mainloop *m);
void pa_threaded_mainloop_free(pa_threaded_mainloop *m);
void pa_threaded_mainloop_lock(pa_threaded_mainloop *m);
void pa_threaded_mainloop_unlock(pa_threaded_mainloop *m);

typedef struct pa_mainloop_api pa_mainloop_api;
pa_mainloop_api* pa_mainloop_get_api(pa_mainloop*m);
pa_mainloop_api *pa_threaded_mainloop_get_api(pa_threaded_mainloop *m);

typedef struct pa_context pa_context;
pa_context *pa_context_new(pa_mainloop_api *mainloop, const char *name);
void pa_context_unref(pa_context *c);
typedef enum pa_context_flags {PA_CONTEXT_NOFLAGS = 0} pa_context_flags_t;
typedef struct pa_spawn_api pa_spawn_api;
int pa_context_connect(pa_context *c, const char *server, pa_context_flags_t flags, const pa_spawn_api *api);
void pa_context_disconnect(pa_context *c);
typedef enum pa_context_state {
    PA_CONTEXT_UNCONNECTED,
    PA_CONTEXT_CONNECTING,
    PA_CONTEXT_AUTHORIZING,
    PA_CONTEXT_SETTING_NAME,
    PA_CONTEXT_READY,
    PA_CONTEXT_FAILED,
    PA_CONTEXT_TERMINATED
} pa_context_state_t;
pa_context_state_t pa_context_get_state(pa_context *c);

typedef struct pa_operation pa_operation;
pa_operation *pa_operation_ref(pa_operation *o);
void pa_operation_unref(pa_operation *o);
typedef enum pa_operation_state {
    PA_OPERATION_RUNNING,
    PA_OPERATION_DONE,
    PA_OPERATION_CANCELLED
} pa_operation_state_t;
pa_operation_state_t pa_operation_get_state(pa_operation *o);

typedef enum pa_sink_state { /* enum serialized in u8 */
    PA_SINK_INVALID_STATE = -1,
    PA_SINK_RUNNING = 0,
    PA_SINK_IDLE = 1,
    PA_SINK_SUSPENDED = 2
} pa_sink_state_t;

typedef struct pa_proplist pa_proplist;
const char *pa_proplist_gets(pa_proplist *p, const char *key);

typedef enum pa_encoding {
    PA_ENCODING_ANY,
    PA_ENCODING_PCM,
    PA_ENCODING_AC3_IEC61937,
    PA_ENCODING_EAC3_IEC61937,
    PA_ENCODING_MPEG_IEC61937,
    PA_ENCODING_DTS_IEC61937,
    PA_ENCODING_MPEG2_AAC_IEC61937,
    PA_ENCODING_MAX,
    PA_ENCODING_INVALID = -1,
} pa_encoding_t;

typedef struct pa_format_info {
    pa_encoding_t encoding;
    pa_proplist *plist;
} pa_format_info;

typedef struct pa_sink_port_info {
    const char *name;
    const char *description;
    uint32_t priority;
    int available;
} pa_sink_port_info;

typedef uint32_t pa_volume_t;
typedef struct pa_cvolume {
    uint8_t channels;
    pa_volume_t values[PA_CHANNELS_MAX];
} pa_cvolume;

typedef uint64_t pa_usec_t;

typedef enum pa_sink_flags {
    PA_SINK_NOFLAGS = 0x0000,
    PA_SINK_HW_VOLUME_CTRL = 0x0001,
    PA_SINK_LATENCY = 0x0002,
    PA_SINK_HARDWARE = 0x0004,
    PA_SINK_NETWORK = 0x0008,
    PA_SINK_HW_MUTE_CTRL = 0x0010,
    PA_SINK_DECIBEL_VOLUME = 0x0020,
    PA_SINK_FLAT_VOLUME = 0x0040,
    PA_SINK_DYNAMIC_LATENCY = 0x0080,
    PA_SINK_SET_FORMATS = 0x0100
} pa_sink_flags_t;

typedef struct pa_sink_info {
    const char *name;
    uint32_t index;
    const char *description;
    pa_sample_spec sample_spec;
    pa_channel_map channel_map;
    uint32_t owner_module;
    pa_cvolume volume;
    int mute;
    uint32_t monitor_source;
    const char *monitor_source_name;
    pa_usec_t latency;
    const char *driver;
    pa_sink_flags_t flags;
    pa_proplist *proplist;
    pa_usec_t configured_latency;
    pa_volume_t base_volume;
    pa_sink_state_t state;
    uint32_t n_volume_steps;
    uint32_t card;
    uint32_t n_ports;
    pa_sink_port_info** ports;
    pa_sink_port_info* active_port;
    uint8_t n_formats;
    pa_format_info **formats;
} pa_sink_info;

typedef struct pa_source_port_info {
    const char *name;
    const char *description;
    uint32_t priority;
    int available;
} pa_source_port_info;

typedef enum pa_source_flags {
    PA_SOURCE_NOFLAGS = 0x0000,
    PA_SOURCE_HW_VOLUME_CTRL = 0x0001,
    PA_SOURCE_LATENCY = 0x0002,
    PA_SOURCE_HARDWARE = 0x0004,
    PA_SOURCE_NETWORK = 0x0008,
    PA_SOURCE_HW_MUTE_CTRL = 0x0010,
    PA_SOURCE_DECIBEL_VOLUME = 0x0020,
    PA_SOURCE_DYNAMIC_LATENCY = 0x0040,
    PA_SOURCE_FLAT_VOLUME = 0x0080
} pa_source_flags_t;

typedef enum pa_source_state {
    PA_SOURCE_INVALID_STATE = -1,
    PA_SOURCE_RUNNING = 0,
    PA_SOURCE_IDLE = 1,
    PA_SOURCE_SUSPENDED = 2
} pa_source_state_t;

typedef struct pa_source_info {
    const char *name;
    uint32_t index;
    const char *description;
    pa_sample_spec sample_spec;
    pa_channel_map channel_map;
    uint32_t owner_module;
    pa_cvolume volume;
    int mute;
    uint32_t monitor_of_sink;
    const char *monitor_of_sink_name;
    pa_usec_t latency;
    const char *driver;
    pa_source_flags_t flags; //
    pa_proplist *proplist;
    pa_usec_t configured_latency;
    pa_volume_t base_volume;
    pa_source_state_t state; //
    uint32_t n_volume_steps;
    uint32_t card;
    uint32_t n_ports;
    pa_source_port_info** ports;
    pa_source_port_info* active_port;
    uint8_t n_formats;
    pa_format_info **formats;
} pa_source_info;

typedef void (*pa_sink_info_cb_t)(pa_context *c, const pa_sink_info *i, int eol, void *userdata);
pa_operation* pa_context_get_sink_info_list(pa_context *c, pa_sink_info_cb_t cb, void *userdata);
pa_operation* pa_context_get_sink_info_by_name(pa_context *c, const char *name, pa_sink_info_cb_t cb, void *userdata);
typedef void (*pa_source_info_cb_t)(pa_context *c, const pa_source_info *i, int eol, void *userdata);
pa_operation* pa_context_get_source_info_list(pa_context *c, pa_source_info_cb_t cb, void *userdata);
pa_operation* pa_context_get_source_info_by_name(pa_context *c, const char *name, pa_source_info_cb_t cb, void *userdata);
typedef void (*pa_context_notify_cb)(pa_context *c, void *userdata);
pa_operation *pa_context_drain(pa_context *c, pa_context_notify_cb cb, void *userdata);

typedef struct pa_server_info {
    const char *user_name;
    const char *host_name;
    const char *server_version;
    const char *server_name;
    pa_sample_spec sample_spec;
    const char *default_sink_name;
    const char *default_source_name;
    uint32_t cookie;
    pa_channel_map channel_map;
} pa_server_info;
typedef void (*pa_server_info_cb_t) (pa_context *c, const pa_server_info*i, void *userdata);
pa_operation* pa_context_get_server_info(pa_context *c, pa_server_info_cb_t cb, void *userdata);

int pa_sample_spec_valid(const pa_sample_spec *spec);

typedef struct pa_stream pa_stream;
pa_stream* pa_stream_new(pa_context *c, const char *name, const pa_sample_spec *ss, const pa_channel_map *map);
void pa_stream_unref(pa_stream *s);

typedef enum pa_stream_flags {
    PA_STREAM_NOFLAGS = 0x0000,
    PA_STREAM_START_CORKED = 0x0001,
    PA_STREAM_INTERPOLATE_TIMING = 0x0002,
    PA_STREAM_NOT_MONOTONIC = 0x0004,
    PA_STREAM_AUTO_TIMING_UPDATE = 0x0008,
    PA_STREAM_NO_REMAP_CHANNELS = 0x0010,
    PA_STREAM_NO_REMIX_CHANNELS = 0x0020,
    PA_STREAM_FIX_FORMAT = 0x0040,
    PA_STREAM_FIX_RATE = 0x0080,
    PA_STREAM_FIX_CHANNELS = 0x0100,
    PA_STREAM_DONT_MOVE = 0x0200,
    PA_STREAM_VARIABLE_RATE = 0x0400,
    PA_STREAM_PEAK_DETECT = 0x0800,
    PA_STREAM_START_MUTED = 0x1000,
    PA_STREAM_ADJUST_LATENCY = 0x2000,
    PA_STREAM_EARLY_REQUESTS = 0x4000,
    PA_STREAM_DONT_INHIBIT_AUTO_SUSPEND = 0x8000,
    PA_STREAM_START_UNMUTED = 0x10000,
    PA_STREAM_FAIL_ON_SUSPEND = 0x20000,
    PA_STREAM_RELATIVE_VOLUME = 0x40000,
    PA_STREAM_PASSTHROUGH = 0x80000
} pa_stream_flags_t;
int pa_stream_connect_playback(pa_stream *s, const char *dev, const pa_buffer_attr *attr, pa_stream_flags_t flags, const pa_cvolume *volume, pa_stream *sync_stream);
int pa_stream_connect_record(pa_stream *s, const char *dev, const pa_buffer_attr *attr, pa_stream_flags_t flags);
int pa_stream_disconnect(pa_stream *s);
typedef void (*pa_stream_success_cb_t) (pa_stream*s, int success, void *userdata);
pa_operation* pa_stream_cork(pa_stream *s, int b, pa_stream_success_cb_t cb, void *userdata);
pa_operation* pa_stream_drain(pa_stream *s, pa_stream_success_cb_t cb, void *userdata);
size_t pa_stream_writable_size(pa_stream *p);
size_t pa_stream_readable_size(pa_stream *p);
typedef void (*pa_free_cb_t)(void *p);
typedef enum pa_seek_mode {
    PA_SEEK_RELATIVE = 0,
    PA_SEEK_ABSOLUTE = 1,
    PA_SEEK_RELATIVE_ON_READ = 2,
    PA_SEEK_RELATIVE_END = 3
} pa_seek_mode_t;
int pa_stream_write(pa_stream *p, const void *data, size_t nbytes, pa_free_cb_t free_cb, int64_t offset, pa_seek_mode_t seek);
int pa_stream_peek(pa_stream *p, const void **data, size_t *nbytes);
int pa_stream_drop(pa_stream *p);
int pa_stream_get_latency(pa_stream *s, pa_usec_t *r_usec, int *negative);
const pa_channel_map* pa_stream_get_channel_map(pa_stream *s);
const pa_buffer_attr* pa_stream_get_buffer_attr(pa_stream *s);

typedef enum pa_stream_state {
    PA_STREAM_UNCONNECTED,
    PA_STREAM_CREATING,
    PA_STREAM_READY,
    PA_STREAM_FAILED,
    PA_STREAM_TERMINATED
} pa_stream_state_t;
pa_stream_state_t pa_stream_get_state(pa_stream *p);

typedef void(*pa_stream_request_cb_t)(pa_stream *p, size_t nbytes, void *userdata);
void pa_stream_set_read_callback(pa_stream *p, pa_stream_request_cb_t cb, void *userdata);

pa_operation* pa_stream_update_timing_info(pa_stream *s, pa_stream_success_cb_t cb, void *userdata);
