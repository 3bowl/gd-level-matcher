import miniaudio
import time


def play(sound):
    # Stream and play an OGG file
    stream = miniaudio.stream_file(sound)
    info = miniaudio.get_file_info(sound)
    with miniaudio.PlaybackDevice() as playback:
        playback.start(stream)
        time.sleep(info.duration)